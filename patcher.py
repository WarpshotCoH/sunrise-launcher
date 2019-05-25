import os

from PySide2.QtCore import QObject, QThread, Slot, Signal

from helpers import logger
from httpdownloader import HTTPDownloader
from manifest import Application
from settings import SunriseSettings

log = logger("main.patcher")

class Patcher(QObject):
    patched = Signal()
    patchFailed = Signal()

    def __init__(self, endpoint, pool, parent = None):
        super(Patcher, self).__init__(parent)

        self.endpoint = endpoint
        self.pool = pool
        self.thread = QThread()
        self.downloader = None

        pool.updated.connect(self.update)
        pool.add(endpoint)

    @Slot(str, str)
    def update(self, url, data):
        # Sanity check in case we get passed an in use pool
        if url == self.endpoint:
            log.info("Preparing to download patch")
            self.shutdown() # Ensure we are not processing anything before starting

            application = Application("sunrise.v1-beta", "tool", "v1-beta", None, False, "", "", "", [], None, None, [], [])

            self.downloader = HTTPDownloader([application], os.path.join(SunriseSettings.settingsPath, "patch", application.id))
            self.downloader.moveToThread(self.thread)
            self.thread.started.connect(self.downloader.download)
            self.downloader.stateChange.connect(self.onStateChange)

            self.thread.start()
            log.info("Started downloading %s path to %s", application.id, os.path.join(SunriseSettings.settingsPath, "patch", application.id))

    def onStateChange(self, state, filename = None):
        log.debug("Patch state transition %s %s", state, filename)
        True

        # TODO: On complete copy tmp over top of the existing install

        # TODO: On complete or error delete tmp

        # TODO: Display success / error notices

    def shutdown(self):
        self.pool.shutdown()
        self.thread.quit()
        self.thread.wait()
