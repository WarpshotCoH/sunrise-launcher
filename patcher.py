from PySide2.QtCore import QObject, QThread, Slot, Signal

class Patcher(QObject):
    patched = Signal()
    patchFailed = Signal()

    def __init__(self, endpoint, pool, parent = None):
        super(Patcher, self).__init__(parent)

        self.endpoint = endpoint
        self.pool = pool
        self.thread = QThread()
        self.downloader = None

        self.thread.start()

    @Slot(str, str)
    def update(self, url, data):
        # Sanity check in case we get passed an in use pool
        if url == self.endpoint:
            self.shutdown() # Ensure we are not processing anything before starting
            update = True # TODO: Impl data parsing

            self.downloader = Downloader([channel], "./tmp")
            self.downloader.moveToThread(self.thread)
            self.downloader.stateChange(self.onStateChange)

            self.downloader.download()

    def onStateChange(self, state, filename = None):
        True

        # TODO: On complete copy tmp over top of the existing install

        # TODO: On complete or error delete tmp

        # TODO: Display success / error notices

    def shutdown(self):
        self.pool.shutdown()
        self.thread.quit()
        self.thread.wait()
