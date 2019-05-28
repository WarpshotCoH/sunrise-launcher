import os
import posixpath
import random
from shutil import copyfile
import sys
import time

from PySide2.QtCore import QThread, QObject, Signal

from downloader import DownloaderState
from download import FileDownload
from helpers import logger

log = logger("main.downloader.http")

class FDBDownloader(QObject):
    fileStart = Signal(int, int, int, str)
    fileProgress = Signal(int)
    fileVerify = Signal(int, int, int, str)
    start = Signal(str, int, int, int)
    progress = Signal(int)
    stateChange = Signal(DownloaderState, str)

    def __init__(self, containers, installPath, fastCheck = False, parent=None):
        super(FDBDownloader, self).__init__(parent)

        self.state = DownloaderState.NEW
        self.containers = containers
        self.installPath = installPath
        self.currentFile = None
        self.fastCheck = fastCheck

    def changeState(self, state, msg = None):
        self.state = state
        self.stateChange.emit(state, msg)

    def pause(self):
        self.changeState(DownloaderState.PAUSED)

        if self.currentFile:
            self.currentFile.stop()
            self.currentFile = None

    def shutdown(self):
        self.changeState(DownloaderState.SHUTDOWN)

        if self.currentFile:
            self.currentFile.stop()
            self.currentFile = None

    def isStopped(self):
        return self.state == DownloaderState.PAUSED or self.state == DownloaderState.SHUTDOWN

    def checkForContainerInstalls(self):
        for container in self.containers:
            log.info("Checking for container install existance %s", container.name)

            containerPath = os.path.normpath(os.path.join(self.installPath, container.id))

            if not os.path.isdir(containerPath):
                log.info("Missing container install path %s", containerPath)
                self.changeState(DownloaderState.MISSING)
                return False

        return True

    def verify(self):
        try:
            assert not QThread.currentThread().objectName() == "Main", "Verifiction running on main thread"

            self.changeState(DownloaderState.VERIFYING)

            if not self.checkForContainerInstalls():
                return

            for container in self.containers:
                log.info("Verifying container %s", container.name)

                self.start.emit(container.name, 0, 0, len(container.files))
                log.debug("Emit runtime size")

                for index, file in enumerate(container.files):
                    if self.isStopped():
                        log.info("Exit verification early from pause")
                        return

                    log.debug("Verify %s", index)
                    fileName = posixpath.basename(file.name)

                    path = os.path.normpath(os.path.join(self.installPath))

                    # log.debug("Verify from %s", path)

                    self.currentFile = FileDownload(file, path)
                    self.currentFile.toggleHashCheck(self.fastCheck)

                    log.debug("Constructed file %s", fileName)

                    if os.path.isfile(path):
                        log.debug("File exists. Verifying %s", path)
                        status = self.currentFile.verify(self.fileVerify, self.fileProgress)

                        if not status:
                            # Do not fail the file if the user has requested a pause
                            if not self.isStopped():
                                log.info("Verification failed %s mismatch", path)
                                self.changeState(DownloaderState.VERIFICATION_FAILED, fileName)

                            return
                        else:
                            log.info("Verfification complete %s", fileName)
                            self.progress.emit(index + 1)
                    else:
                        log.info("Verification failed %s missing", path)
                        self.changeState(DownloaderState.VERIFICATION_FAILED, fileName)
                        return

            self.changeState(DownloaderState.COMPLETE)
        except Exception:
            log.error(sys.exc_info())

    def selectMirror(self, container):
        mirrors = list(filter(lambda s: s.tag == "http", container.sources))

        if len(mirrors) > 0:
            return mirrors[random.randint(0, len(mirrors) - 1)].src

        return None

    def download(self):
        try:
            assert not QThread.currentThread().objectName() == "Main", "Download running on main thread"

            self.changeState(DownloaderState.DOWNLOADING)

            for container in self.containers:
                log.info("Downloading container %s", container.name)

                self.start.emit(container.name, 0, 0, len(container.files))
                log.debug("Emit runtime size")

                mirror = self.selectMirror(container)

                for index, file in enumerate(container.files):
                    if self.isStopped():
                        log.info("Exit download early from pause")
                        return

                    log.debug("Download %s", index)
                    fileName = os.path.basename(file.name)

                    path = os.path.normpath(os.path.join(self.installPath, file.check))
                    dirPath = os.path.normpath(os.path.join(self.installPath))

                    if not os.path.isdir(dirPath):
                        log.info("Create download path %s", dirPath)
                        os.makedirs(dirPath)

                    log.info("Write to %s", path)

                    self.currentFile = FileDownload(file, path, mirror)

                    log.debug("Constructed file %s", fileName)

                    if os.path.isfile(path):
                        log.info("File already exists. Verifying %s", path)
                        status = self.currentFile.verify(self.fileVerify, self.fileProgress)
                    else:
                        status = False

                    if not status:
                        status = self.currentFile.start(self.fileStart, self.fileProgress)

                    if not status:
                        # Do not fail the file if the user has requested a pause
                        if not self.isStopped():
                            self.changeState(DownloaderState.DOWNLOAD_FAILED, fileName)

                        return
                    else:
                        log.info("Download complete %s", fileName)
                        status = self.currentFile.verify(self.fileVerify, self.fileProgress)

                        if not status:
                            # Do not fail the file if the user has requested a pause
                            if not self.isStopped():
                                self.changeState(DownloaderState.VERIFICATION_FAILED, fileName)

                            return

                    if status:
                        log.info("Verfification complete %s", fileName)
                        self.progress.emit(index + 1)

            self.changeState(DownloaderState.COMPLETE)
        except Exception:
            log.error(sys.exc_info())
