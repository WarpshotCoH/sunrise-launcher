import json
import os
import pickle
import sys
import xml.etree.ElementTree as ET

from PySide2.QtCore import QObject, Slot, Signal

from helpers import uList, SunriseSettings
from manifest import fromXML, fromXMLString, Manifest
from settings import Settings, PathSettings, ContainerSettings, RecentServers
from theme import Loader, Theme

from helpers import logger

log = logger("main.state")

LOCAL_MANIFEST_URL = "local://manifests.xml"

# Storage of metadata about the users current install
class Store(QObject):
    updated = Signal()

    def __init__(self, parent = None):
        super(Store, self).__init__(parent)

        self.config = {}
        self.manifestNames = {}
        self.applications = {}
        self.runtimes = {}
        self.servers = {}
        self.cache = Settings()
        self.settings = Settings()
        self.running = []
        self.themes = {}
        self.strings = {}

        try:
            config = open("config.json", "r").read()

            if config:
                self.config = json.loads(config)

        except Exception:
            log.error("App config initialization failure")
            log.error(sys.exc_info())
            pass

        try:
            dirs = list(os.walk(os.path.abspath("themes")))

            if len(dirs) > 0:
                for themeId in dirs[0][1]:
                    log.info("Adding theme from %s", themeId)
                    theme = Theme.fromPath(os.path.join("themes", themeId))

                    if theme.props and "name" in theme.props:
                        self.themes[theme.props["name"]] = theme

        except Exception:
            log.error("Default theme initialization failure")
            log.error(sys.exc_info())
            pass

        try:
            stringConfig = open("twine/app.en.json", "r").read()

            if stringConfig:
                self.strings = json.loads(stringConfig)

        except Exception:
            log.error("Strings initialization failure")
            log.error(sys.exc_info())
            pass

        try:
            dirs = list(os.walk(os.path.join(SunriseSettings.settingsPath, "themes")))

            if len(dirs) > 0:
                for themeId in dirs[0][1]:
                    log.info("Adding user theme from %s", themeId)
                    theme = Theme.fromPath(os.path.join(SunriseSettings.settingsPath, "themes", themeId))

                    if theme.props and "name" in theme.props:
                        self.themes[theme.props["name"]] = theme

        except Exception:
            log.error("User theme initialization failure")
            log.error(sys.exc_info())
            pass

        self.settings.committed.connect(self.saveSettings)
        self.updated.connect(self.saveManifests)

    def f(self, key):
        return self.config['flags'].get(key)

    def s(self, key):
        return self.strings.get(key)

    def load(self):
        try:
            cacheFile = os.path.join(SunriseSettings.cachePath, "cache.pickle")

            if os.path.isfile(cacheFile):
                f = open(cacheFile, "rb")
                self.cache.load(pickle.load(f))
                self.cache.commit()

            if not self.cache.get("fileMap"):
                self.cache.set("fileMap", {})

            self.cache.commit()
        except Exception:
            log.error(sys.exc_info())
            pass

        try:
            settingsFile = os.path.join(SunriseSettings.settingsPath, "settings.pickle")

            if os.path.isfile(settingsFile):
                f = open(settingsFile, "rb")
                self.settings.load(pickle.load(f))
                self.settings.commit()

            if not self.settings.get("autoPatch"):
                self.settings.set("autoPatch", True)

            if not self.settings.get("containerSettings"):
                self.settings.set("containerSettings", {})

            if not self.settings.get("paths"):
                self.settings.set("paths", PathSettings("bin", "run"))

            if not self.settings.get("recentServers"):
                self.settings.set("recentServers", RecentServers())

            if not self.settings.get("hiddenServers"):
                self.settings.set("hiddenServers", uList())

            if not self.settings.get("theme") and len(self.themes.keys()) > 0:
               self.settings.set("theme", list(self.themes.keys())[0])

            if not self.settings.get("manifestList"):
                self.settings.set("manifestList", uList())

            self.settings.commit()
        except Exception:
            log.error(sys.exc_info())
            pass

        try:
            storedManifests = open(os.path.join(SunriseSettings.settingsPath, "manifests.xml"), "r").read()
            self.loadManifest(LOCAL_MANIFEST_URL, storedManifests)
        except Exception:
            log.error(sys.exc_info())
            pass

        log.debug("Loaded state")
        log.debug("%s theme is selected", self.settings.get("theme"))

        self.updated.emit()

    def getTools(self):
        return list(filter(lambda a: a.type == "mod", self.applications.values()))

    def getClients(self):
        return list(filter(lambda a: a.type == "client", self.applications.values()))

    def installTheme(self, filePath):
        theme = Loader.load(filePath)

        if theme:
            self.themes[theme.props["name"]] = theme
            self.settings.set("theme", theme.props["name"])
            self.settings.commit()
            self.updated.emit()

    @Slot(str, str)
    def loadManifest(self, url, data):
        manifest = fromXMLString(data, url)

        log.info("Loading manifest from %s in to the store", url)

        self.applications.update(manifest.applications)
        self.runtimes.update(manifest.runtimes)
        self.servers.update(manifest.servers)

        containerSettings = self.settings.get("containerSettings")

        for app in self.applications.values():
            if not app.id in containerSettings:
                containerSettings[app.id] = ContainerSettings(app.id)

        for runtime in self.runtimes.values():
            if not runtime.id in containerSettings:
                containerSettings[runtime.id] = ContainerSettings(runtime.id)

        self.settings.set("containerSettings", containerSettings)

        if not manifest.source == LOCAL_MANIFEST_URL:
            self.manifestNames[url] = manifest.name
            manifests = self.settings.get("manifestList")
            manifests.push(url)

            self.settings.set("manifestList", manifests)

        self.settings.commit()
        log.info("Committed container settings for %s", url)

        self.updated.emit()

    @Slot(str)
    def addRunning(self, id):
        log.debug("Adding %s to running list", id)
        self.running.append(id)

    @Slot(str)
    def removeRunning(self, id):
        log.debug("Removing %s to running list", id)
        self.running.remove(id)

    def saveCache(self):
        if not os.path.isdir(SunriseSettings.cachePath):
            os.makedirs(SunriseSettings.cachePath)

        log.debug("Writing %s to cache file",  self.cache.getData())

        f = open(os.path.join(SunriseSettings.cachePath, "cache.pickle"), "wb+")
        cacheOutput = pickle.dump(self.cache.getData(), f)

        log.debug("Wrote cache file")

        f.close()

    def saveSettings(self):
        if not os.path.isdir(SunriseSettings.settingsPath):
            os.makedirs(SunriseSettings.settingsPath)

        log.debug("Writing %s to settings file",  self.settings.getData())

        f = open(os.path.join(SunriseSettings.settingsPath, "settings.pickle"), "wb+")
        settingsOutput = pickle.dump(self.settings.getData(), f)

        log.debug("Wrote settings file")

        f.close()

    def saveManifests(self):
        if not os.path.isdir(SunriseSettings.settingsPath):
            os.makedirs(SunriseSettings.settingsPath)

        manifest = Manifest("store", self.servers, self.applications, self.runtimes, LOCAL_MANIFEST_URL)
        manifestOutput = ET.tostring(manifest.toXML(), encoding="utf8", method="xml")

        f = open(os.path.join(SunriseSettings.settingsPath, "manifests.xml"), "wb+")
        f.write(manifestOutput)

        log.debug("Wrote local manifest file")

        f.close()
