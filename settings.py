from copy import deepcopy
import os

from PySide2.QtCore import QObject, QThread, Slot, Signal

from helpers import Serde, logger, serialize, unserialize, SunriseSettings

log = logger("main.state.settings")

class PathSettings:
    def __init__(self, binPath, runPath):
        self.binPath = os.path.join(SunriseSettings.dataPath, binPath)
        self.runPath = os.path.join(SunriseSettings.dataPath, runPath)

    def serialize(self):
        return {
            "type": "PathSettings",
            "data": {
                "binPath": self.binPath,
                "runPath": self.runPath
            }
        }

    @staticmethod
    def unserialize(obj):
        if type(obj) is dict and "type" in obj and obj["type"] == "PathSettings" and "data" in obj and type(obj["data"]) is dict:
            return PathSettings(obj["data"].get("binPath", "bin"), obj["data"].get("runPath", "run"))

        return None

class ContainerSettings:
    def __init__(self, id, autoPatch = False, customParams = None):
        self.id = id
        self.autoPatch = autoPatch
        self.customParams = customParams

    def serialize(self):
        return {
            "type": "ContainerSettings",
            "data": {
                "autoPatch": self.autoPatch,
                "customParams": self.customParams
            }
        }

    @staticmethod
    def unserialize(obj):
        if type(obj) is dict and "type" in obj and obj["type"] == "ContainerSettings" and "data" in obj and type(obj["data"]) is dict:
            return ContainerSettings(obj["data"].get("autoPatch", False), obj["data"].get("customParams", None))

        return None

class RecentServers:
    def __init__(self, data = []):
        self.recent = data

    def push(self, id):
        if id in self.recent:
            self.recent.remove(id)

        self.recent.insert(0, id)

    def serialize(self):
        return {
            "type": "RecentServers",
            "data": self.recent
        }

    @staticmethod
    def unserialize(obj):
        if type(obj) is dict and "type" in obj and obj["type"] == "RecentServers" and "data" in obj and type(obj["data"]) is list:
            return RecentServers(obj["data"])

        return None

class Settings(QObject):
    changed = Signal(str)
    committed = Signal(dict)
    cancelled = Signal()

    def __init__(self, data = None, parent = None):
        super(Settings, self).__init__(parent)

        self.store = data if data else {}
        self.pending = {}

    def get(self, k, default = None):
        item = self.store.get(k)

        if item:
            return deepcopy(item)
        else:
            return default

    def getPending(self, k):
        return self.pending.get(k)

    def getData(self):
        return deepcopy(self.store)

    def serialize(self):
        c = self.getData()

        for k, v in c.items():
            c[k] = serialize(v)

        return c

    def serialize(self):
        c = self.getData()

        for k, v in c.items():
            c[k] = serialize(v)

        rep = {}
        rep["type"] = "Settings"
        rep["data"] = c

        return rep

    @staticmethod
    def unserialize(obj):
        if type(obj) is dict and "type" in obj and obj["type"] == "Settings" and "data" in obj and type(obj["data"]) is dict:
            n = {}

            for k, v in obj["data"].items():
                n[k] = unserialize(v)

            return Settings(n)

        return None

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
                log.debug("Emit update for %s", k)
                self.changed.emit(k)

        self.committed.emit(self.store)

        self.pending = {}

    def reset(self):
        self.cancelled.emit()
        self.pending = {}

    def clear(self):
        keys = self.store.keys()

        self.store = {}
        self.pending = {}

        for k in keys:
            self.changed.emit(k)

        self.committed.emit(self.store)

    def connectKey(self, k, fn):
        self.changed.connect(lambda updatedKey: fn(k) if k == updatedKey else None)

Serde.register("PathSettings", PathSettings)
Serde.register("ContainerSettings", ContainerSettings)
Serde.register("RecentServers", RecentServers)
Serde.register("Settings", Settings)
