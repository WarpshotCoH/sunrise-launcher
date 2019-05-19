import hashlib
import sys
import time
import urllib.request as request

from PySide2.QtCore import QObject, QThread, QTimer, Slot, Signal
import requests

class WatcherPool(QObject):
    updated = Signal(str, str)
    startTrigger = Signal()
    stopTrigger = Signal()

    def __init__(self, parent=None):
        super(WatcherPool, self).__init__(parent)
        self.watchers = {}
        self.thread = QThread()
        self.thread.start()

    def add(self, url):
        if self.watchers.get(url):
            self.watchers[url].shutdown()

        self.watchers[url] = Watcher(url, self.updated)
        self.watchers[url].moveToThread(self.thread)
        self.stopTrigger.connect(self.watchers[url].shutdown)

        if self.thread.isRunning():
            print("Watch thread already running. Starting", url)
            # TODO: There should be a better way to write this
            try:
                self.startTrigger.disconnect()
            except Exception:
                pass

            self.startTrigger.connect(self.watchers[url].start)
            self.startTrigger.emit()
        else:
            print("Watch thread not running. Scheduling", url)
            self.thread.started.connect(self.watchers[url].start)

    def remove(self, url):
        if self.watchers.get(url):
            self.watchers[url].shutdown()
            self.watchers.pop(url, None)

    def shutdown(self):
        self.stopTrigger.emit()

        self.thread.quit()
        self.thread.wait()

class Watcher(QObject):
    def __init__(self, url, updater, parent=None):
        super(Watcher, self).__init__(parent)

        self.check = None
        self.url = url
        self.updater = updater

        self.timer = None

    @Slot()
    def start(self):
        print("Start watcher", self.url)
        self.timer = QTimer()
        self.timer.setInterval(60000)
        self.timer.timeout.connect(self.run)
        self.timer.start()
        self.run()

    def shutdown(self):
        # TODO: Fix QObject::killTimer: Timers cannot be stopped from another thread on shutdown
        if self.timer:
            self.timer.stop()

    @Slot()
    def run(self):
        try:
            print("Try fetch", self.url)
            req = requests.get(self.url, timeout=5)

            with req:
                req.raise_for_status()
                check = hashlib.sha512(req.content).hexdigest()

                if not self.check == check:
                    self.check = check
                    print("Update available", self.url)
                    self.updater.emit(self.url, req.text)

        except Exception:
            print("Fetch error", self.url)
            print(sys.exc_info())
