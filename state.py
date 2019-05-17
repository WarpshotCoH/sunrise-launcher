import os
import pickle
import sys
import xml.etree.ElementTree as ET

from PySide2.QtCore import QObject, Slot, Signal

from manifest import fromXML, fromXMLString, Manifest
from settings import Settings, PathSettings, ContainerSettings, RecentServers
from theme import Loader

# Storage of metadata about the users current install
class Store(QObject):
    updated = Signal()

    def __init__(self, parent=None):
        super(Store, self).__init__(parent)

        self.applications = {}
        self.runtimes = {}
        self.servers = {}
        self.cache = {}
        self.settings = Settings()
        self.running = []
        self.theme = None

    def load(self):
        try:
            storedManifests = Manifest.fromXML(ET.parse("store/manifests.xml").getroot())
            self.applications = storedManifests.applications
            self.runtimes = storedManifests.runtimes
            self.servers = storedManifests.servers
        except Exception:
            print(sys.exc_info())
            pass

        try:
            if os.path.isfile(os.path.normpath("store/settings.pickle")):
                f = open("store/settings.pickle", "rb")
                self.settings.load(pickle.load(f))
            else:
                self.settings.set("autoPatch", True)
                self.settings.set("manifestList", set())
                self.settings.set("containerSettings", {})
                self.settings.set("paths", PathSettings("bin", "run"))
                self.settings.set("recentServers", RecentServers())
                self.settings.set("hiddenServers", set())

            self.settings.commit()
        except Exception:
            print(sys.exc_info())
            pass

        self.updated.emit()

    def getTools(self):
        return list(filter(lambda a: a.type == "mod", self.applications.values()))

    def getClients(self):
        return list(filter(lambda a: a.type == "client", self.applications.values()))

    @Slot(str, str)
    def loadManifest(self, url, data):
        manifest = fromXMLString(data)

        print("Updating manifest from", url, "in store")

        self.applications.update(manifest.applications)
        self.runtimes.update(manifest.runtimes)
        self.servers.update(manifest.servers)

        containerSettings = self.settings.get("containerSettings")

        for app in self.applications.values():
            if not containerSettings.get(app.id):
                containerSettings[app.id] = ContainerSettings(app.id)

        for runtime in self.runtimes.values():
            if not containerSettings.get(runtime.id):
                containerSettings[runtime.id] = ContainerSettings(runtime.id)

        self.settings.set("containerSettings", containerSettings)

        manifests = self.settings.get("manifestList")
        manifests.add(url)

        self.settings.set("manifestList", manifests)

        self.settings.commit()

        print("Committed settings for", url)

        self.updated.emit()

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
        path = os.path.normpath(os.path.join(".", "store"))

        if not os.path.isdir(path):
            os.makedirs(path)

        manifest = Manifest("store", self.servers, self.applications, self.runtimes)
        manifestOutput = ET.tostring(manifest.toXML(), encoding="utf8", method="xml")

        f = open("store/manifests.xml", "wb+")
        f.write(manifestOutput)
        f.close()

        f = open("store/settings.pickle", "wb+")
        settingsOutput = pickle.dump(self.settings.getData(), f)

        f.close()
