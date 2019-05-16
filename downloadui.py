import os

from PySide2.QtCore import QObject, QThread, Slot, Signal

from downloader import Downloader, FileDownload, DownloaderState
from manifest import Application, Runtime, Server

class DownloadUI(QObject):
    launch = Signal(str)

    def __init__(self, store, progressBar, fileBar, button, parent=None):
        super(DownloadUI, self).__init__(parent)

        self.store = store
        self.progressBar = progressBar
        self.fileBar = fileBar
        self.button = button
        self.downloadThread = None
        self.downloader = None
        self.containers =[]
        self.areContainersRunnable = False

        self.button.clicked.connect(self.startDownload)

    def hide(self):
        self.progressBar.hide()
        self.fileBar.hide()
        self.button.hide()

    def show(self):
        self.progressBar.show()
        self.fileBar.show()
        self.button.show()

    @Slot(Application, Runtime, Server)
    def load(self, application = None, runtime = None, server = None):
        self.min = self.max = self.cur = 0
        self.server = server
        self.containers = []

        if runtime:
            self.containers.append(runtime)

        if application:
            self.containers.append(application)

        self.areContainersRunnable = application == None

        if not self.store.settings.get("appSettings").get(application.id).autoPatch:
            if os.path.isdir(self.store.settings.get("paths").binPath):
                self.verifyDownload()

            self.button.setText("Install")
        else:
            self.startDownload()

    def run(self):
        if self.server:
            self.launch.emit(self.server.id)

    def verifyDownload(self):
        self.shutdown()
        self.downloader = Downloader([self.containers[-1]], self.store.settings.get("paths").binPath)
        self.runInBackground(self.downloader.verify)

    def startDownload(self):
        # Before verifying or downloading, make sure existing downloaders and
        # threads have been cleaned up
        self.shutdown()
        self.downloader = Downloader(self.containers, self.store.settings.get("paths").binPath)
        self.runInBackground(self.downloader.download)

    # TODO: Startup on this feels slow (due to thread spawn maybe?). Can we
    #       reuse the thread / downloader and instead use a custom slot + signal
    #       for triggering instead of thread start?
    def runInBackground(self, fn):
        print("Start background download")

        # We do not want multiple downloads to start while waiting for the thread
        # to initialize
        self.disableButton()

        # Init the download background thread
        # TODO: Can not seem to figure out how to spawn a single QThread and then
        #       continually reused by placing new work on to it. Seems like
        #       something that we should be able to do.
        self.downloadThread = QThread()

        # Connect up to the files progress events
        self.downloader.start.connect(self.onStart)
        self.downloader.progress.connect(self.onProgress)
        self.downloader.stateChange.connect(self.onDownloaderStateChange)

        # Connect up to the file progress events
        self.downloader.fileStart.connect(self.onFileStart)
        self.downloader.fileProgress.connect(self.onFileProgress)
        self.downloader.fileVerify.connect(self.onFileStart)

        # Move the download manager to the background thread
        self.downloader.moveToThread(self.downloadThread)

        # Once the thread is ready, we can re-enable the button. We attach the
        # enable listener first because it has to run prior to the download
        # starting. Once the download starts the thread will be busy until it
        # completes / errors / or is cancelled
        self.downloadThread.started.connect(self.enableButton)

        # Schedule the downloader to start once the thread is active
        self.downloadThread.started.connect(fn)

        # Boot the background thread
        self.downloadThread.start()

    def enableButton(self):
        self.button.setEnabled(True)

    def disableButton(self):
        self.button.setEnabled(False)

    def pauseDownload(self):
        self.downloader.pause()

    def shutdown(self):
        if self.downloader:
            self.downloader.shutdown()

        if self.downloadThread:
            self.downloadThread.quit()
            self.downloadThread.wait()

    @Slot(str, int, int, int)
    def onStart(self, name, pMin, pStart, pMax):
        print("Downloader Start")
        print(name, pMin, pStart, pMax)
        self.min = pMin
        self.max = pMax
        self.progressBar.setFormat("({}) %p%".format(name))
        self.progressBar.setMinimum(pMin)
        self.progressBar.setValue(pStart)
        self.progressBar.setMaximum(pMax)
        self.progressBar.show()

    @Slot(int)
    def onProgress(self, i):
        self.cur = i
        self.progressBar.setValue(i)

    @Slot(DownloaderState, str)
    def onDownloaderStateChange(self, state, filename = None):
        print("Change state", state)
        self.disableButton()

        buttonLabel = {
            DownloaderState.NEW: "Install",
            DownloaderState.DOWNLOADING: "Pause",
            DownloaderState.VERIFYING: "Play",
            DownloaderState.PAUSED: "Resume",
            DownloaderState.COMPLETE: "Play",
            DownloaderState.DOWNLOAD_FAILED: "Download",
            DownloaderState.VERIFICATION_FAILED: "Repair",
            DownloaderState.MISSING: "Install",
        }

        buttonAction = {
            DownloaderState.NEW: self.startDownload,
            DownloaderState.DOWNLOADING: self.pauseDownload,
            DownloaderState.VERIFYING: self.pauseDownload,
            DownloaderState.PAUSED: self.startDownload,
            DownloaderState.COMPLETE: self.run,
            DownloaderState.DOWNLOAD_FAILED: self.startDownload,
            DownloaderState.VERIFICATION_FAILED: self.startDownload,
            DownloaderState.MISSING: self.startDownload,
        }

        # Ignore the shutdown state. Currently it means the application is
        # shutting down or we are transitioning to another list item
        if not state == DownloaderState.SHUTDOWN:
            print("Setting label to", buttonLabel[state])
            self.button.setText(buttonLabel[state])
            self.button.clicked.disconnect()
            self.button.clicked.connect(buttonAction[state])

            if state == DownloaderState.DOWNLOADING or state == DownloaderState.VERIFYING:
                self.progressBar.setProperty("Done", False)
                self.progressBar.setStyle(self.progressBar.style())
                self.fileBar.setProperty("Done", False)
                self.fileBar.setStyle(self.fileBar.style())

            # TODO: If QThread can be re-used over and over then this is not necessary.
            #       In the meantime we tear down the thread whenever progress stops and
            #       create a new one progress begins again
            if state == DownloaderState.PAUSED or state == DownloaderState.COMPLETE or state == DownloaderState.DOWNLOAD_FAILED or state == DownloaderState.VERIFICATION_FAILED:

                # If we had a running thread that needs to be stopped, ensure that it
                # is stopped before we allow a new download to be started with a new
                # download thread
                self.downloadThread.finished.connect(self.enableButton)
                self.downloadThread.quit()
            else:
                if not state == DownloaderState.VERIFYING:
                    self.enableButton()

            if state == DownloaderState.DOWNLOAD_FAILED and filename:
                self.progressBar.setFormat("Failed to download {}".format(filename))
                self.fileBar.hide()

            if state == DownloaderState.VERIFICATION_FAILED and filename:
                self.progressBar.setFormat("Failed to verify {}".format(filename))
                self.fileBar.hide()

            # On a pause, complete, or missing we clear out any progress text
            if state == DownloaderState.PAUSED or state == DownloaderState.COMPLETE or state == DownloaderState.MISSING:
                self.progressBar.setProperty("Done", True)
                self.progressBar.setStyle(self.progressBar.style())
                self.fileBar.setProperty("Done", True)
                self.fileBar.setStyle(self.fileBar.style())

    @Slot(int, int, int, str)
    def onFileStart(self, pMin, pStart, pMax, filename):
        self.fileBar.setMinimum(pMin)
        self.fileBar.setValue(pStart)
        self.fileBar.setMaximum(pMax)
        self.fileBar.setFormat("{}/{} - {}".format(self.cur, self.max, filename))
        self.fileBar.show()

    @Slot(int)
    def onFileProgress(self, i):
        self.fileBar.setValue(i)
