import os
import posixpath
import sys

from PySide2.QtCore import QThread, QObject, Signal

from download import FileDownload

class DownloaderState():
    NEW = 1
    RUNNING = 2
    PAUSED = 3
    COMPLETE = 4
    DOWNLOAD_FAILED = 5
    VERIFICATION_FAILED = 6

class Downloader(QObject):
    fileStart = Signal(int, int, int, str)
    fileProgress = Signal(int)
    fileVerify = Signal(int, int, int, str)
    start = Signal(int, int, int)
    progress = Signal(int)
    stateChange = Signal(DownloaderState, str)

    def __init__(self, containers, installPath, fastCheck = False, parent=None):
        super(Downloader, self).__init__(parent)

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

    def verify(self):
        self.changeState(DownloaderState.RUNNING)

        try:
            for container in self.containers:
                print("Verifying container", container.name)

                self.start.emit(0, 0, len(container.files))
                print("Emit runtime size")

                for index, file in enumerate(container.files):
                    if self.state == DownloaderState.PAUSED:
                        print("Exit early from pause")
                        return

                    print("Verify", index)
                    fileName = posixpath.basename(file.name)
                    filePath = file.name

                    path = os.path.normpath(os.path.join(self.installPath, container.id, filePath))

                    print("Verify from", path)

                    self.currentFile = FileDownload(file, path)
                    self.currentFile.toggleHashCheck(self.fastCheck)

                    print("Constructed file", fileName)

                    if os.path.isfile(path):
                        print("File exists. Verifying", path)
                        status = self.currentFile.verify(self.fileVerify, self.fileProgress)

                        if not status:
                            # Do not fail the file if the user has requested a pause
                            if not self.state == DownloaderState.PAUSED:
                                self.changeState(DownloaderState.VERIFICATION_FAILED, fileName)

                            return
                        else:
                            print("Verfification complete", fileName)
                            self.progress.emit(index + 1)
                    else:
                        print("File missing. Verifying", path)
                        self.changeState(DownloaderState.VERIFICATION_FAILED, fileName)
                        return

                self.changeState(DownloaderState.COMPLETE)
        except Exception:
            print("Error!")
            print(sys.exc_info())

    def download(self):
        self.changeState(DownloaderState.RUNNING)

        try:
            for container in self.containers:
                print("Downloading container", container.name)

                self.start.emit(0, 0, len(container.files))
                print("Emit runtime size")

                for index, file in enumerate(container.files):
                    if self.state == DownloaderState.PAUSED:
                        print("Exit early from pause")
                        return

                    print("Download", index)
                    fileName = os.path.basename(file.name)
                    filePath = os.path.dirname(file.name)

                    path = os.path.normpath(os.path.join(self.installPath, container.id, file.name))
                    dirPath = os.path.normpath(os.path.join(self.installPath, container.id, filePath))

                    if not os.path.isdir(dirPath):
                        print("Create download path", dirPath)
                        os.makedirs(dirPath)

                    print("Write to", path)

                    self.currentFile = FileDownload(file, path)

                    print("Constructed file", fileName)

                    if os.path.isfile(path):
                        print("File already exists. Verifying", path)
                        status = self.currentFile.verify(self.fileVerify, self.fileProgress)
                    else:
                        status = False

                    if not status:
                        status = self.currentFile.start(self.fileStart, self.fileProgress)

                    if not status:
                        # Do not fail the file if the user has requested a pause
                        if not self.state == DownloaderState.PAUSED:
                            self.changeState(DownloaderState.DOWNLOAD_FAILED, fileName)

                        return
                    else:
                        print("Download complete", fileName)
                        status = self.currentFile.verify(self.fileVerify, self.fileProgress)

                        if not status:
                            # Do not fail the file if the user has requested a pause
                            if not self.state == DownloaderState.PAUSED:
                                self.changeState(DownloaderState.VERIFICATION_FAILED, fileName)

                            return
                        else:
                            print("Verfification complete", fileName)
                            self.progress.emit(index + 1)

                self.changeState(DownloaderState.COMPLETE)
        except Exception:
            print("Error!")
            print(sys.exc_info())
