from copy import deepcopy

from PySide2.QtCore import QObject, QThread, Slot, Signal

from helpers import logger

log = logger("main.state.settings")

class PathSettings:
    def __init__(self, binPath, runPath):
        self.binPath = binPath
        self.runPath = runPath

class ContainerSettings:
    def __init__(self, id, autoPatch = False, customParams = None):
        self.id = id
        self.autoPatch = autoPatch
        self.customParams = customParams

class RecentServers:
    def __init__(self):
        self.recent = []

    def push(self, id):
        if id in self.recent:
            self.recent.remove(id)

        self.recent.insert(0, id)

class Settings(QObject):
    changed = Signal(str)
    committed = Signal(dict)
    cancelled = Signal()

    def __init__(self, parent = None):
        super(Settings, self).__init__(parent)

        self.store = {}
        self.pending = {}

    def get(self, k):
        return deepcopy(self.store.get(k))

    def getPending(self, k):
        return self.pending.get(k)

    def getData(self):
        return deepcopy(self.store)

    def load(self, store):
        self.pending = store

    def set(self, k, v):
        self.pending[k] = v

    def commit(self):
        pending = deepcopy(self.pending)

        for k, v in pending.items():
            log.debug("Checking %s for updates", k)

            if not (k in self.store and self.store[k] == v):
                self.store[k] = v
                log.debug("Emit update for %s: %s", k, v)
                self.changed.emit(k)


        self.committed.emit(self.store)

        self.pending = {}

    def reset(self):
        self.cancelled.emit()
        self.pending = {}

    def destroy(self):
        self.store = {}
        self.pending = {}

    def connectKey(self, k, fn):
        self.changed.connect(lambda updatedKey: fn(k) if k == updatedKey else None)

