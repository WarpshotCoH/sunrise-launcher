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

  def __init__(self, files, installPath, parent=None):
    super(Downloader, self).__init__(parent)

    self.state = DownloaderState.NEW
    self.files = files
    self.installPath = installPath
    self.currentFile = None

  def changeState(self, state, msg = None):
    self.state = state
    self.stateChange.emit(state, msg)

  def pause(self):
    self.changeState(DownloaderState.PAUSED)
    self.currentFile.stop()

  def download(self):
    self.changeState(DownloaderState.RUNNING)

    try:
      self.start.emit(0, 0, len(self.files))
      print("Emit runtime size")
      
      for index, file in enumerate(self.files):
        if self.state == DownloaderState.PAUSED:
          print("Exit early from pause")
          return

        print("Download", index)
        fileName = posixpath.basename(file.name)
        fileSize = int(file.size)
        filePath = file.name

        path = os.path.normpath(os.path.join(self.installPath, filePath))

        if not os.path.isdir(self.installPath):
          print("Create install path", self.installPath)
          os.makedirs(self.installPath)

        print("Write to", path)

        self.currentFile = FileDownload(
          path,
          file.urls,
          fileName,
          fileSize,
          file.check,
          file.algo
        )

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