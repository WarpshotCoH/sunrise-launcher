from PySide2.QtCore import Slot

from helpers import uList
from watcher import WatcherPool

class ManifestPool(WatcherPool):
    def __init__(self, store, parent=None):
        super(ManifestPool, self).__init__(parent)
        self.store = store
        self.store.settings.connectKey("manifestList", self.update)

    @Slot(str)
    def update(self, key):
        urlList = self.watchers.keys()
        newList = self.store.settings.get("manifestList")

        for url in list(set(urlList) - set(newList)):
            self.remove(url)

        for url in list(set(newList) - set(urlList)):
            self.add(url)
