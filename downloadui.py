import os

from PySide2.QtCore import QObject, QThread, Slot, Signal

from downloader import DownloaderState
from httpdownloader import HTTPDownloader
from manifest import Application, Runtime, Server
from helpers import createWidget, logger, uList, isInstalled, InstallState, disconnect

log = logger("main.ui.download")

class DownloadUI(QObject):
    launch = Signal(str)

    def __init__(self, store, parent):
        super(DownloadUI, self).__init__(parent)

        self.store = store
        self.ui = createWidget("ui/listview-download.ui")

        self.progressBar = self.ui.progress
        progressSizePolicy = self.progressBar.sizePolicy()
        progressSizePolicy.setRetainSizeWhenHidden(True)
        self.progressBar.setSizePolicy(progressSizePolicy)

        self.fileBar = self.ui.fileProgress
        fileBarSizePolicy = self.fileBar.sizePolicy()
        fileBarSizePolicy.setRetainSizeWhenHidden(True)
        self.fileBar.setSizePolicy(fileBarSizePolicy)

        self.button = self.ui.play
        self.downloadThread = None
        self.downloader = None
        self.containers =[]
        self.launchId = None

        self.button.clicked.connect(self.startDownload)

        parent.addWidget(self.ui)

    def hide(self):
        self.ui.hide()

    def show(self):
        self.ui.show()

    @Slot(Application, Runtime, Server)
    def load(self, application = None, runtime = None, server = None):
        log.info("Loading %s %s %s", application, runtime, server)

        if application == None and runtime == None and server == None:
            self.shutdown()
            self.hide()
        else:
            self.show()

        self.min = self.max = self.cur = 0
        self.containers = []

        if server:
            self.launchId = server.id
        elif application and application.type == "mod":
            # TODO: Filter out non-launchable applications
            self.launchId = application.id
        else:
            self.launchId = None

        if runtime:
            self.containers.append(runtime)

        if application:
            self.containers.append(application)

        if len(self.containers) > 0:
            log.debug("Found containers %s to handle", self.containers)

            if self.store.settings.get("containerSettings").get(self.containers[-1].id).autoPatch:
                self.startDownload()
            else:
                if not isInstalled(self.store, self.containers[-1].id) == InstallState.NOTINSTALLED:
                    self.verifyDownload()
                else:
                    disconnect(self.button.clicked)
                    self.button.setText(self.getButtonLabel(DownloaderState.NEW))
                    self.button.clicked.connect(self.getButtonAction(DownloaderState.NEW))

    def run(self):
        if self.launchId:
            self.launch.emit(self.launchId)

    def verifyDownload(self):
        log.debug("Triggered verification for %s", self.containers)

        self.shutdown()

        self.downloader = HTTPDownloader(
            self.containers,
            self.store.settings.get("paths").binPath,
            self.store.cache.get("fileMap", {})
        )

        self.runInBackground(self.downloader.verify)
        self.show()

    def fullVerifyDownload(self):
        log.debug("Triggered full verification for %s", self.containers)

        self.shutdown()

        self.downloader = HTTPDownloader(
            self.containers,
            self.store.settings.get("paths").binPath,
            self.store.cache.get("fileMap", {}),
            fullVerify = True
        )

        self.runInBackground(self.downloader.verify)
        self.show()

    def startDownload(self):
        log.debug("Triggered download for %s", self.containers)

        # Before verifying or downloading, make sure existing downloaders and
        # threads have been cleaned up
        self.shutdown()

        self.downloader = HTTPDownloader(
            self.containers,
            self.store.settings.get("paths").binPath,
            self.store.cache.get("fileMap", {})
        )

        self.runInBackground(self.downloader.download)
        self.show()

    # TODO: Startup on this feels slow (due to thread spawn maybe?). Can we
    #       reuse the thread / downloader and instead use a custom slot + signal
    #       for triggering instead of thread start?
    def runInBackground(self, fn):
        log.info("Start background download")

        # We do not want multiple downloads to start while waiting for the thread
        # to initialize
        self.disableButton()

        # Init the download background thread
        # TODO: Can not seem to figure out how to spawn a single QThread and then
        #       continually reused by placing new work on to it. Seems like
        #       something that we should be able to do.
        self.downloadThread = QThread()
        self.downloadThread.setObjectName("Download")

        # Connect up to the files progress events
        self.downloader.start.connect(self.onStart)
        self.downloader.progress.connect(self.onProgress)
        self.downloader.stateChanged.connect(self.onDownloaderStateChange)

        # Connect up to the file progress events
        self.downloader.fileStarted.connect(self.onFileStart)
        self.downloader.fileProgress.connect(self.onFileProgress)
        self.downloader.fileCompleted.connect(self.onFileComplete)
        self.downloader.invalidMapFileFound.connect(self.onInvalidMapFile)

        # Connect up to the container progress event
        self.downloader.containerCompleted.connect(self.onContainerComplete)

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
            log.debug("Shutting down downloader")
            self.downloader.shutdown()

        if self.downloadThread:
            log.debug("Shutting down download thread")
            self.downloadThread.quit()
            self.downloadThread.wait()

    def getButtonLabel(self, state):

        # TODO: Button/label for non-runnable targets
        buttonLabel = {
            DownloaderState.NEW: self.store.s("DOWNLOAD_INSTALL"),
            DownloaderState.DOWNLOADING: self.store.s("DOWNLOAD_PAUSE"),
            DownloaderState.VERIFYING: self.store.s("DOWNLOAD_PLAY"),
            DownloaderState.PAUSED: self.store.s("DOWNLOAD_RESUME"),
            DownloaderState.COMPLETE: self.store.s("DOWNLOAD_PLAY"),
            DownloaderState.DOWNLOAD_FAILED: self.store.s("DOWNLOAD_DOWNLOAD"),
            DownloaderState.VERIFICATION_FAILED: self.store.s("DOWNLOAD_REPAIR"),
            DownloaderState.MISSING: self.store.s("DOWNLOAD_INSTALL"),
        }

        return buttonLabel[state]

    def getButtonAction(self, state):

        # TODO: Button/label for non-runnable targets
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

        return buttonAction[state]

    @Slot(str, int, int, int)
    def onStart(self, name, pMin, pStart, pMax):
        log.info("Continer download started for %s", name)
        log.info("Min: %s Start: %s Max: %s", pMin, pStart, pMax)
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

    @Slot(DownloaderState, tuple)
    def onDownloaderStateChange(self, state, file):
        log.debug("Change state %s : %s", state, file)
        self.disableButton()

        # Ignore the shutdown state. Currently it means the application is
        # shutting down or we are transitioning to another list item
        if not state == DownloaderState.SHUTDOWN:
            log.debug("Setting button label to %s", self.getButtonLabel(state))
            self.button.setText(self.getButtonLabel(state))
            self.button.clicked.disconnect()
            self.button.clicked.connect(self.getButtonAction(state))

            if state == DownloaderState.DOWNLOADING or state == DownloaderState.VERIFYING:
                self.progressBar.show()
                self.fileBar.show()

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

            if state == DownloaderState.DOWNLOAD_FAILED and file[1]:
                log.info("Failed to download %s", file[1])
                self.progressBar.setFormat("Failed to download {}".format(file[1]))
                self.fileBar.hide()

            if state == DownloaderState.VERIFICATION_FAILED and file[1]:
                log.info("Failed to verify %s", file[1])

            # On a pause, complete, or missing we clear out any progress text
            if state == DownloaderState.PAUSED or state == DownloaderState.COMPLETE or state == DownloaderState.MISSING or state == DownloaderState.VERIFICATION_FAILED:
                self.progressBar.hide()
                self.fileBar.hide()

    @Slot(int, int, int, str)
    def onFileStart(self, pMin, pStart, pMax, filename):
        self.fileBar.setMinimum(pMin)
        self.fileBar.setValue(pStart)
        self.fileBar.setMaximum(pMax)
        self.fileBar.setFormat("{}/{} - {}".format(self.cur, self.max, filename))
        self.fileBar.show()

    @Slot(str, str)
    def onInvalidMapFile(check, file):
        fMap = self.store.cache.get("fileMap", {})

        if check in fMap:
            files = fMap.get(check)

            if file in files:
                files.remove(file)

                self.store.cache.set("fileMap", fMap)
                self.store.cache.commit()

    @Slot(int)
    def onFileProgress(self, i):
        self.fileBar.setValue(i)

    @Slot(list)
    def onFileComplete(self, file):
        fMap = self.store.cache.get("fileMap", {})

        if not fMap.get(file[0]):
            fMap[file[0]] = uList()

        if not [file[1], file[2]] in fMap[file[0]]:
            fMap[file[0]].push([file[1], file[2]])

            self.store.cache.set("fileMap", fMap)
            self.store.cache.commit()

        log.debug("File completed %s", file)

    @Slot(tuple)
    def onContainerComplete(self, info):
        checks = self.store.cache.get("containerChecks", {})

        if not info[0] in checks.keys():
            checks[info[0]] = {}

        if not ("local" in checks[info[0]] and checks[info[0]]["local"] == info[1]):
            checks[info[0]]["local"] = info[1]

            self.store.cache.set("containerChecks", checks)
            self.store.cache.commit()

            log.debug("Local check for %s set to %s", info[0], info[1])
