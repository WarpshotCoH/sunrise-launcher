from PySide2.QtCore import QThread, Slot

from downloader import Downloader, FileDownload, DownloaderState

class DownloadUI:
  def __init__(self, progressBar, fileBar, label, button):
    self.progressBar = progressBar
    self.fileBar = fileBar
    self.label = label
    self.button = button
    self.downloadThread = None
    self.downloader = None

    self.button.clicked.connect(self.startDownload)

  def load(self, files, installPath):
    self.files = files
    self.installPath = installPath

  def startDownload(self):
    print("Start background download")

    # We do not want multiple downloads to start while waiting for the thread
    # to initialize
    self.disableButton()

    # Init the download background thread
    # TODO: Can not seem to figure out how to spawn a single QThread and then
    #       continually reused by placing new work on to it. Seems like
    #       something that we should be able to do.
    self.downloadThread = QThread()

    # Re-initializing the download manager for simplicity. It means we need to
    # re-verify work that was previously done, but this seems to be the correct
    # thing to do. Content could have changed between the pause / resume
    self.downloader = Downloader(self.files, self.installPath)

    # Connect up to the files progress events
    self.downloader.start.connect(self.onStart)
    self.downloader.progress.connect(self.onProgress)
    self.downloader.stateChange.connect(self.onDownloaderStateChange)
    
    # Connect up to the file progress events
    self.downloader.fileStart.connect(self.onFileStart)
    self.downloader.fileProgress.connect(self.onFileProgress)
    self.downloader.fileVerify.connect(self.onFileVerify)

    # Move the download manager to the background thread
    self.downloader.moveToThread(self.downloadThread)

    # Once the thread is ready, we can re-enable the button. We attach the
    # enable listener first because it has to run prior to the download
    # starting. Once the download starts the thread will be busy until it
    # completes / errors / or is cancelled
    self.downloadThread.started.connect(self.enableButton)

    # Schedule the downloader to start once the thread is active
    self.downloadThread.started.connect(self.downloader.download)

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
      self.downloader.pause()

    if self.downloadThread:
      self.downloadThread.quit()
      self.downloadThread.wait()

  @Slot(int, int, int)
  def onStart(self, pMin, pStart, pMax):
    print("Downloader Start")
    print(pMin, pStart, pMax)
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
      DownloaderState.COMPLETE: self.startDownload,
      DownloaderState.DOWNLOAD_FAILED: self.startDownload,
      DownloaderState.VERIFICATION_FAILED: self.startDownload,
    }

    self.button.setText(buttonLabel[state])
    self.button.clicked.disconnect()
    self.button.clicked.connect(buttonAction[state])

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
      self.enableButton()

    if state == DownloaderState.DOWNLOAD_FAILED and filename:
      self.label.setText("Failed to download " + filename)

    if state == DownloaderState.VERIFICATION_FAILED and filename:
      self.label.setText("Failed to verify " + filename)

    # On a pause request we clear out any progress text
    if state == DownloaderState.PAUSED:
      self.label.setText("")

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