import os

from PySide2.QtCore import QObject, QThread, Slot, Signal

from downloader import Downloader, FileDownload, DownloaderState

class DownloadUI(QObject):
    launch = Signal()
    trigger = Signal()

    def __init__(self, progressBar, fileBar, label, button, parent=None):
        super(DownloadUI, self).__init__(parent)

        self.progressBar = progressBar
        self.fileBar = fileBar
        self.label = label
        self.button = button
        self.thread = QThread()
        self.downloader = None

        self.button.clicked.connect(self.startDownload)

        # Boot the background thread
        self.thread.start()

    def hide(self):
        self.progressBar.hide()
        self.fileBar.hide()
        self.label.hide()
        self.button.hide()

    def show(self):
        self.progressBar.show()
        self.fileBar.show()
        self.label.show()
        self.button.show()

    def load(self, containers, installPath):
        self.containers = containers
        self.installPath = installPath

        if os.path.isdir(installPath):
            self.verifyDownload()

    def run(self):
        self.launch.emit()

    def verifyDownload(self):
        # Before verifying, make sure existing downloaders have been cleaned up
        if self.downloader:
            self.downloader.pause()

        self.downloader = Downloader(self.containers, self.installPath, True)
        self.runInBackground(self.downloader.verify)

    def startDownload(self):
        # Before downloading, make sure existing downloaders have been cleaned up
        if self.downloader:
            self.downloader.pause()

        self.downloader = Downloader(self.containers, self.installPath)
        self.runInBackground(self.downloader.download)

    def runInBackground(self, fn):
        print("Start background task", fn)

        # We do not want multiple downloads to start while waiting for the thread
        # to initialize
        self.disableButton()

        # Connect up to the files progress events
        self.downloader.start.connect(self.onStart)
        self.downloader.progress.connect(self.onProgress)
        self.downloader.stateChange.connect(self.onDownloaderStateChange)

        # Connect up to the file progress events
        self.downloader.fileStart.connect(self.onFileStart)
        self.downloader.fileProgress.connect(self.onFileProgress)
        self.downloader.fileVerify.connect(self.onFileVerify)

        # Move the download manager to the background thread
        self.downloader.moveToThread(self.thread)

        # Schedule the downloader to start once the thread is active
        # Once the thread is ready, we can re-enable the button. We attach the
        # enable listener first because it has to run prior to the download
        # starting. Once the download starts the thread will be busy until it
        # completes / errors / or is cancelled
        if self.thread.isRunning():
            print("Download thread already active. Starting", fn)

            # TODO: There should be a better way to write this
            try:
                self.trigger.disconnect()
            except Exception:
                pass

            self.trigger.connect(fn)
            self.trigger.emit()
            self.enableButton()
        else:
            print("Download thread not active. Scheduling", fn)
            self.thread.started.connect(fn)
            self.thread.started.connect(self.enableButton)

    def enableButton(self):
        self.button.setEnabled(True)

    def disableButton(self):
        self.button.setEnabled(False)

    def pauseDownload(self):
        self.downloader.pause()

    def shutdown(self):
        if self.downloader:
            self.downloader.pause()

        if self.thread:
            self.thread.quit()
            self.thread.wait()

    @Slot(str, int, int, int)
    def onStart(self, name, pMin, pStart, pMax):
        print("Downloader Start")
        print(name, pMin, pStart, pMax)
        self.progressBar.setFormat("[{}] %p% (%v / %m)".format(name))
        self.progressBar.setMinimum(pMin)
        self.progressBar.setValue(pStart)
        self.progressBar.setMaximum(pMax)

    @Slot(int)
    def onProgress(self, i):
        self.progressBar.setValue(i)

    @Slot(DownloaderState, str)
    def onDownloaderStateChange(self, state, filename = None):
        print("Change state", state)
        self.disableButton()

        buttonLabel = {
            DownloaderState.NEW: "Download",
            DownloaderState.RUNNING: "Pause",
            DownloaderState.PAUSED: "Resume",
            DownloaderState.COMPLETE: "Play",
            DownloaderState.DOWNLOAD_FAILED: "Download",
            DownloaderState.VERIFICATION_FAILED: "Download",
        }

        buttonAction = {
            DownloaderState.NEW: self.startDownload,
            DownloaderState.RUNNING: self.pauseDownload,
            DownloaderState.PAUSED: self.startDownload,
            DownloaderState.COMPLETE: self.run,
            DownloaderState.DOWNLOAD_FAILED: self.startDownload,
            DownloaderState.VERIFICATION_FAILED: self.startDownload,
        }

        self.button.setText(buttonLabel[state])
        self.button.clicked.disconnect()
        self.button.clicked.connect(buttonAction[state])

        if state == DownloaderState.DOWNLOAD_FAILED and filename:
            self.label.setText("Failed to download " + filename)

        if state == DownloaderState.VERIFICATION_FAILED and filename:
            self.label.setText("Failed to verify " + filename)

        # On a pause request or a complete we clear out any progress text
        if state == DownloaderState.PAUSED or state == DownloaderState.COMPLETE:
            self.label.setText("")

        self.enableButton()

    @Slot(int, int, int, str)
    def onFileStart(self, pMin, pStart, pMax, filename):
        self.fileBar.setMinimum(pMin)
        self.fileBar.setValue(pStart)
        self.fileBar.setMaximum(pMax)
        self.label.setText("Downloading: %s..." % filename)
        self.label.repaint()

    @Slot(int, int, int, str)
    def onFileVerify(self, pMin, pStart, pMax, filename):
        self.fileBar.setMinimum(pMin)
        self.fileBar.setValue(pStart)
        self.fileBar.setMaximum(pMax)
        self.label.setText("Verifying: %s..." % filename)
        self.label.repaint()

    @Slot(int)
    def onFileProgress(self, i):
        self.fileBar.setValue(i)
