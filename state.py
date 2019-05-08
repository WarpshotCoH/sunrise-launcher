import os
import xml.etree.ElementTree as ET
import sys

from PySide2.QtCore import QObject, Slot, Signal

from manifest import fromXML, Manifest

class PathConfig:
    def __init__(self, binPath, runPath):
        self.binPath = binPath
        self.runPath = runPath


# Storage of metadata about the users current install
class Store(QObject):
    update = Signal()

    def __init__(self, parent=None):
        super(Store, self).__init__(parent)

        self.applications = {}
        self.runtimes = {}
        self.servers = {}
        self.cache = {}
        self.settings = {}
        self.running = []

        self.settings["autoDownload"] = []
        self.settings["paths"] = PathConfig("bin", "run")

        try:
            stored = Manifest.fromXML(ET.parse("store/manifests.xml").getroot())
            self.applications = stored.applications
            self.runtimes = stored.runtimes
            self.servers = stored.servers
        except Exception:
            print(sys.exc_info())
            pass

    @Slot(str, Manifest)
    def load(self, url, manifest):
        print("Updating manifest from", url, "in store")

        self.applications.update(manifest.applications)
        self.runtimes.update(manifest.runtimes)
        self.servers.update(manifest.servers)
        self.update.emit()

    @Slot(str)
    def addRunning(self, id):
        print("Adding", id, "to running list")
        self.running.append(id)

    @Slot(str)
    def removeRunning(self, id):
        print("Removing", id, "to running list")
        self.running.remove(id)

    def resolveDownload(self, id):
        # TODO: Do we need to handle collisions between app and runtime ids
        requested = self.applications.get(id, self.runtimes.get(id))

        if requested:
            print("Resolved", requested.id)
            if hasattr(requested, "runtime") and requested.runtime:
                return self.resolveDownload(requested.runtime) + [requested]
            else:
                return [requested]
        else:
            print("Failed to resolve", id)
            return []

    def save(self):
        m = Manifest("store", self.servers, self.applications, self.runtimes)
        output = ET.tostring(m.toXML(), encoding="utf8", method="xml")

        path = os.path.normpath(os.path.join(".", "store"))

        if not os.path.isdir(path):
            os.makedirs(path)

        f = open("store/manifests.xml", "wb+")
        f.write(output)
        f.close()
