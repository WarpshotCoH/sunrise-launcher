import os
import xml.etree.ElementTree as ET
import sys

from PySide2.QtCore import QObject, Slot, Signal

from manifest import fromXML, fromXMLString, Manifest
from settings import Settings, PathSettings, ApplicationSettings, RecentServers
from theme import Loader

# Storage of metadata about the users current install
class Store(QObject):
    updated = Signal()
    loaded = Signal()

    def __init__(self, parent=None):
        super(Store, self).__init__(parent)

        self.applications = {}
        self.runtimes = {}
        self.servers = {}
        self.cache = {}
        self.settings = Settings()
        self.running = []
        self.theme = None

        self.settings.set("autoPatch", True)
        self.settings.set("manifestList", set())
        self.settings.set("appSettings", {})
        self.settings.set("paths", PathSettings("bin", "run"))
        self.settings.set("recentServers", RecentServers())
        self.settings.set("hiddenServers", set())
        self.settings.set("lockedServers", [])
        self.settings.set("parentalPin", None)
        self.settings.commit()

        try:
            stored = Manifest.fromXML(ET.parse("store/manifests.xml").getroot())
            self.applications = stored.applications
            self.runtimes = stored.runtimes
            self.servers = stored.servers
        except Exception:
            print(sys.exc_info())
            pass

        self.loaded.emit()

    @Slot(str, str)
    def loadManifest(self, url, data):
        manifest = fromXMLString(data)

        print("Updating manifest from", url, "in store")

        self.applications.update(manifest.applications)
        self.runtimes.update(manifest.runtimes)
        self.servers.update(manifest.servers)

        appSettings = self.settings.get("appSettings")

        for app in self.applications.values():
            if not appSettings.get(app.id):
                appSettings[app.id] = ApplicationSettings(app.id)

        self.settings.set("appSettings", appSettings)

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
        m = Manifest("store", self.servers, self.applications, self.runtimes)
        output = ET.tostring(m.toXML(), encoding="utf8", method="xml")

        path = os.path.normpath(os.path.join(".", "store"))

        if not os.path.isdir(path):
            os.makedirs(path)

        f = open("store/manifests.xml", "wb+")
        f.write(output)
        f.close()
