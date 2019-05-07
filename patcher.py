import hashlib
import sys
import time
import urllib.request as request

from PySide2.QtCore import QObject, QThread, QTimer, Slot, Signal
import requests

from manifest import fromXMLString, Manifest

class PatcherPool(QObject):
    update = Signal(str, Manifest)

    def __init__(self, parent=None):
        super(PatcherPool, self).__init__(parent)
        self.patchers = {}
        self.thread = QThread()
        self.thread.start()

    def add(self, manifestUrl):
        if self.patchers.get(manifestUrl):
            self.patchers[manifestUrl].shutdown()

        self.patchers[manifestUrl] = Patcher(manifestUrl, self.update)
        self.patchers[manifestUrl].moveToThread(self.thread)

        if self.thread.isRunning():
            self.patchers[manifestUrl].start()
        else:
            self.thread.started.connect(self.patchers[manifestUrl].start)

    def shutdown(self):
        for patcher in self.patchers.values():
            patcher.shutdown()

        self.thread.quit()
        self.thread.wait()

class Patcher(QObject):
    def __init__(self, manifestUrl, updater, parent=None):
        super(Patcher, self).__init__(parent)

        self.manifest = None
        self.check = None
        self.manifestUrl = manifestUrl
        self.updater = updater

        self.timer = None

    @Slot()
    def start(self):
        self.timer = QTimer()
        self.timer.setInterval(60000)
        self.timer.timeout.connect(self.run)
        self.timer.start()
        self.run()

    def shutdown(self):
        if self.timer:
            self.timer.stop()

    @Slot()
    def run(self):
        try:
            print("Try fetch", self.manifestUrl)
            with open (self.manifestUrl, "r") as file:
                contents = file.read()
            # r = requests.get(self.manifestUrl, timeout=5)

            # with r:
                # r.raise_for_status()
                check = hashlib.sha512(contents.encode("utf-8")).hexdigest()

                if not self.check == check:
                    self.check = check
                    self.manifest = fromXMLString(contents)
                    # self.manifest = Manifest.fromXML(r.text)
                    self.updater.emit(self.manifestUrl, self.manifest)

        except Exception:
            print("Fetch error", self.manifestUrl)
            print(sys.exc_info())
