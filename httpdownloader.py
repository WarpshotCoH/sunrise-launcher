from functools import reduce
from hashlib import sha512
import os
import posixpath
import random
from shutil import copyfile
import sys
import time

from PySide2.QtCore import QThread, QObject, Signal

from downloader import DownloaderState
from download import FileDownload
from helpers import logger, copyDir

log = logger("main.downloader.http")

class HTTPDownloader(QObject):
    fileStarted = Signal(int, int, int, str)
    fileProgress = Signal(int)
    fileCompleted = Signal(list)
    containerCompleted = Signal(tuple)
    start = Signal(str, int, int, int)
    progress = Signal(int)
    stateChanged = Signal(DownloaderState, tuple)
    invalidMapFileFound = Signal(str, str)

    def __init__(self, containers, installPath, fileMap = None, fullVerify = False, parent=None):
        super(HTTPDownloader, self).__init__(parent)

        self.state = DownloaderState.NEW
        self.containers = containers
        self.installPath = installPath
        self.fileMap = fileMap
        self.fullVerify = fullVerify
        self.currentFile = None

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

    def selectMirror(self, container):
        mirrors = list(filter(lambda s: s.tag == "http", container.sources))

        if len(mirrors) > 0:
            return mirrors[random.randint(0, len(mirrors) - 1)].src

        return None

    def verify(self):
        self.processContainers(download = False)

    def download(self):
        self.processContainers(download = True)

    def processContainers(self, download = False):
        try:
            assert not QThread.currentThread().objectName() == "Main", "Download running on main thread"

            self.changeState(DownloaderState.DOWNLOADING)

            exclusions = reduce(
                lambda ex, cur: ex + list(map(lambda e: e.name, cur.exclusions)),
                self.containers,
                []
            )

            log.debug("Computed exclusion list %s", exclusions)

            containerCheck = sha512()

            for container in self.containers:

                # Set up the default install path
                dstPath = os.path.join(self.installPath, container.id)

                if container.ctype == "application":
                    files = container.files

                    # If we downloading a non-standalone application, then it should be installed
                    # to the runtime directory
                    if not container.standalone:
                        dstPath = os.path.join(self.installPath, self.containers[0].id)
                else:
                    files = list(filter(lambda f: not f.name in exclusions, container.files))

                log.debug("Computed download list %s", files)

                self.start.emit(container.name, 0, 0, len(files))

                mirror = self.selectMirror(container)

                log.info("Downloading container %s to %s", container.name, dstPath)

                for index, file in enumerate(files):
                    if self.isStopped():
                        log.info("Exit download early from pause")
                        return

                    log.debug("Download %s", index)
                    fileName = os.path.basename(file.name)
                    filePath = os.path.dirname(file.name)

                    path = os.path.normpath(os.path.join(dstPath, file.name))
                    dirPath = os.path.normpath(os.path.join(dstPath, filePath))

                    if not os.path.isdir(dirPath):
                        log.info("Create download path %s", dirPath)
                        os.makedirs(dirPath)

                    log.info("Begin work on %s", path)

                    self.currentFile = FileDownload(file, path, mirror)

                    # File status always starts as false
                    status = False

                    log.debug("Constructed file %s", fileName)

                    if os.path.isfile(path):
                        log.info("File already exists. Verifying %s", path)

                        # Before verifying the hash, perform a quick check if the file is in
                        # the file map
                        if not self.fullVerify:
                            if self.currentFile.file.check in self.fileMap:
                                for file in self.fileMap[self.currentFile.file.check]:
                                    if not status:
                                        status = file[0] == path and self.currentFile.check(file[1])

                        if not status:
                            status = self.currentFile.verify(self.fileStarted, self.fileProgress)

                    if download:
                        if not status:
                            # If we don't already have the file locally, check the fileMap to
                            # see if it has been downloaded already by someone else
                            if self.currentFile.file.check in self.fileMap:
                                existingFiles = self.fileMap[self.currentFile.file.check]

                                log.info("Found %s existing file(s) for %s : %s", len(existingFiles), self.currentFile.file.check, path)

                                for file in existingFiles:
                                    if not status:
                                        status = self.currentFile.copyFrom(file[0], self.fileStarted, self.fileProgress)

                                        if not status:
                                            self.invalidMapFileFound.emit(self.currentFile.file.check, file[0])
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

                            # Emit the progress so far on the container
                            self.containerCompleted.emit((container.id, containerCheck.hexdigest()))

                            return
                    else:
                        log.info("Verfification complete %s", fileName)
                        self.progress.emit(index + 1)
                        self.fileCompleted.emit([self.currentFile.file.check, path, os.path.getmtime(path)])
                        containerCheck.update(bytes(self.currentFile.file.check, "utf-8"))

            # Container is complete, emit the install hash
            self.containerCompleted.emit((container.id, containerCheck.hexdigest()))

            self.currentFile = None
            self.changeState(DownloaderState.COMPLETE)
        except Exception:

            # TODO: We may hit an error were we attempted to access self.currentFile after
            # it has been destroyed by shutdown. It can safely be ignored as we wanted to
            # terminate processing anyway. This should be addressed when this code is
            # refactored into a better form
            log.warn(sys.exc_info(), exc_info = True)
