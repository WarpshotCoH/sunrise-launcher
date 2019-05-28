import hashlib
import sys
import time
import urllib.request as request

from PySide2.QtCore import QObject, QThread, QTimer, Slot, Signal
import requests

from helpers import logger

pLog = logger("main.watcherpool")
wLog = logger("main.watcherpool.watcher")

class WatcherPool(QObject):
    updated = Signal(str, str)
    startTrigger = Signal()
    stopTrigger = Signal(str)
    shutdownTrigger = Signal()

    def __init__(self, parent=None):
        super(WatcherPool, self).__init__(parent)
        self.watchers = {}
        self.graveyard = []
        self.thread = QThread()
        self.thread.setObjectName("Watcher")
        self.thread.start()

    def add(self, url):
        if self.watchers.get(url):
            self.remove(url)

        self.watchers[url] = Watcher(url, self.updated)
        self.watchers[url].moveToThread(self.thread)
        self.stopTrigger.connect(self.watchers[url].stop)
        self.shutdownTrigger.connect(self.watchers[url].shutdown)

        if self.thread.isRunning():
            pLog.debug("Watch thread already running. Starting %s", url)
            # TODO: There should be a better way to write this
            try:
                self.startTrigger.disconnect()
            except Exception:
                pass

            self.startTrigger.connect(self.watchers[url].start)
            self.startTrigger.emit()

            pLog.debug("Emitted start trigger")
        else:
            pLog.debug("Watch thread not running. Scheduling %s", url)
            self.thread.started.connect(self.watchers[url].start)

    def remove(self, url):
        if self.watchers.get(url):
            self.stopTrigger.emit(url)

            # Append to graveyard so that the timer can gracefully stop
            # instead of the reference being dropped
            self.graveyard.append(self.watchers.pop(url))

    @Slot()
    def shutdown(self):
        self.shutdownTrigger.emit()

        # TODO: Hack to get the pool's thread to run the shutdown requests
        #       prior to shutting down the thread itself. Stopping the thread
        #       immediately results in timers in the pool thread being stopped
        #       by the main thread. This seems problematic? I do not know
        #       enough of the systems to make a proper call
        time.sleep(0.25)

        self.thread.quit()
        self.thread.wait()

class Watcher(QObject):
    def __init__(self, url, updater = None, parent=None):
        super(Watcher, self).__init__(parent)

        self.check = None
        self.url = url
        self.updater = updater

        self.timer = None

    @Slot()
    def start(self):
        try:
            wLog.debug("Start watcher for %s", self.url)
            wLog.debug("Current thread during watcher start %s", QThread.currentThread().objectName())

            assert not QThread.currentThread().objectName() == "Main", "Watcher startup on main thread"

            self.timer = QTimer()
            self.timer.setInterval(60000)
            self.timer.timeout.connect(self.run)
            self.timer.start()
            self.run()
        except Exception as error:
            wLog.error("Start error %s", self.url)
            wLog.error(sys.exc_info())

            raise error

    @Slot(str)
    def stop(self, url):
        try:
            assert not QThread.currentThread().objectName() == "Main", "Watcher is trying to stop from main thread"

            if self.timer:
                if url == self.url:
                    wLog.debug("Stop timer %s", self.url)
                    self.timer.stop()
        except Exception as error:
            wLog.error("Stop error %s", self.url)
            wLog.error(sys.exc_info())

            raise error

    @Slot()
    def shutdown(self):
        try:
            assert not QThread.currentThread().objectName() == "Main", "Watcher is trying to shutdown from main thread"

            if self.timer:
                wLog.debug("Stop timer %s", self.url)
                self.timer.stop()
        except Exception as error:
            wLog.error("Shutdown error %s", self.url)
            wLog.error(sys.exc_info())

            raise error

    @Slot()
    def run(self):
        try:
            assert not QThread.currentThread().objectName() == "Main", "Watcher is running on main thread"

            wLog.info("Try fetch for %s", self.url)
            req = requests.get(self.url, timeout=5)

            with req:
                req.raise_for_status()
                check = hashlib.sha512(req.content).hexdigest()

                if not self.check == check:
                    self.check = check
                    wLog.info("Update available for %s", self.url)
                    self.updater.emit(self.url, req.text)
                else:
                    wLog.debug("Manifest at %s has not changed", self.url)

        except Exception as error:
            wLog.error("Fetch error %s", self.url)
            wLog.error(sys.exc_info())

            raise error
