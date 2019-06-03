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

class HTTPDownloader(QObject):
    fileStarted = Signal(int, int, int, str)
    fileProgress = Signal(int)
    fileCompleted = Signal(tuple)
    start = Signal(str, int, int, int)
    progress = Signal(int)
    stateChanged = Signal(DownloaderState, tuple)

    def __init__(self, containers, installPath, fileMap = None, fastCheck = False, parent=None):
        super(HTTPDownloader, self).__init__(parent)

        self.state = DownloaderState.NEW
        self.containers = containers
        self.installPath = installPath
        self.fileMap = fileMap
        self.fastCheck = fastCheck
        self.currentFile = None
        self.fileMap = {}

    def changeState(self, state, fileName = None):
        self.state = state

        if self.currentFile:
            self.stateChanged.emit(
                state,
                (self.currentFile.file.check, fileName)
            )
        else:
            self.stateChanged.emit(state, None)

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
                    filePath = file.name

                    path = os.path.normpath(os.path.join(self.installPath, container.id, filePath))

                    log.debug("Verify from %s", path)

                    self.currentFile = FileDownload(file, path)
                    self.currentFile.toggleHashCheck(self.fastCheck)

                    log.debug("Constructed file %s", fileName)

                    if os.path.isfile(path):
                        log.debug("File exists. Verifying %s", path)
                        status = self.currentFile.verify(self.fileStarted, self.fileProgress)

                        if not status:
                            # Do not fail the file if the user has requested a pause
                            if not self.isStopped():
                                log.info("Verification failed %s mismatch", path)
                                self.changeState(DownloaderState.VERIFICATION_FAILED, path)

                            return
                        else:
                            log.info("Verfification complete %s", fileName)
                            self.progress.emit(index + 1)
                            self.fileCompleted.emit((self.currentFile.file.check, path))
                    else:
                        log.info("Verification failed %s missing", path)
                        self.changeState(DownloaderState.VERIFICATION_FAILED, path)
                        return

            self.currentFile = None
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

                mirror = self.selectMirror(container)

                for index, file in enumerate(container.files):
                    if self.isStopped():
                        log.info("Exit download early from pause")
                        return

                    log.debug("Download %s", index)
                    fileName = os.path.basename(file.name)
                    filePath = os.path.dirname(file.name)

                    path = os.path.normpath(os.path.join(self.installPath, container.id, file.name))
                    dirPath = os.path.normpath(os.path.join(self.installPath, container.id, filePath))

                    if not os.path.isdir(dirPath):
                        log.info("Create download path %s", dirPath)
                        os.makedirs(dirPath)

                    log.info("Write to %s", path)

                    self.currentFile = FileDownload(file, path, mirror)

                    log.debug("Constructed file %s", fileName)

                    if os.path.isfile(path):
                        log.info("File already exists. Verifying %s", path)
                        status = self.currentFile.verify(self.fileStarted, self.fileProgress)
                    else:
                        status = False

                    if not status:
                        # If we don't already have the file locally, check the fileMap to
                        # see if it has been downloaded already by someone else
                        if self.currentFile.file.check in self.fileMap:
                            existingFiles = self.fileMap[self.currentFile.file.check]

                            log.info("Found %s existing file(s) for %s : %s", len(existingFiles), self.currentFile.file.check, path)

                            for file in existingFiles:
                                if not status:
                                    status = self.currentFile.copyFrom(file, self.fileStarted, self.fileProgress)
                        else:
                            log.debug("Failed to find %s in existing file map", self.currentFile.file.check)

                        if not status:
                            # We do not have any local copies, download the file
                            status = self.currentFile.start(self.fileStarted, self.fileProgress)

                    if not status:
                        # Do not fail the file if the user has requested a pause
                        if not self.isStopped():
                            self.changeState(DownloaderState.DOWNLOAD_FAILED, path)

                        return
                    else:
                        log.info("Download complete %s", fileName)
                        status = self.currentFile.verify(self.fileStarted, self.fileProgress)

                        if not status:
                            # Do not fail the file if the user has requested a pause
                            if not self.isStopped():
                                self.changeState(DownloaderState.VERIFICATION_FAILED, path)

                            return

                    if status:
                        log.info("Verfification complete %s", fileName)

                        if hasattr(container, "runtime"):
                            dstDir = os.path.abspath(os.path.normpath(os.path.join(self.installPath, container.runtime, filePath)))
                            dstFile = os.path.join(dstDir, fileName)

                            if not os.path.isdir(dstDir):
                                os.makedirs(dstDir)

                            copyfile(os.path.abspath(path), os.path.abspath(os.path.join(dstDir, fileName)))

                        self.progress.emit(index + 1)
                        self.fileCompleted.emit((self.currentFile.file.check, path))

            self.currentFile = None
            self.changeState(DownloaderState.COMPLETE)
        except Exception:
            log.error(sys.exc_info())
