import hashlib
import sys
import time
import urllib.request as request

from PySide2.QtCore import QObject, QTimer, Slot, Signal
import requests

from manifest import fromXMLString, Manifest

class PatcherPool(QObject):
    update = Signal(str, Manifest)

    def __init__(self, parent=None):
        super(PatcherPool, self).__init__(parent)
        self.patchers = {}

    def add(self, manifestUrl):
        if self.patchers.get(manifestUrl):
            self.patchers[manifestUrl].shutdown()

        self.patchers[manifestUrl] = Patcher(manifestUrl, self.update)
        self.patchers[manifestUrl].run()

    def shutdown(self):
        for patcher in self.patchers.values():
            patcher.shutdown()

class Patcher(QObject):
    def __init__(self, manifestUrl, updater, parent=None):
        super(Patcher, self).__init__(parent)

        self.manifest = None
        self.check = None
        self.manifestUrl = manifestUrl
        self.updater = updater

        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.run)
        self.timer.start()

    def shutdown(self):
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
