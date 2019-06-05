import logging
import os
import shutil
import sys

from appdirs import user_cache_dir, user_data_dir, user_log_dir
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader

APP_NAME = "Sunrise"
APP_AUTHOR = "Sunrise"

class SunriseSettings:
    cachePath = user_cache_dir(APP_NAME, APP_AUTHOR)
    logsPath = user_log_dir(APP_NAME, APP_AUTHOR)
    settingsPath = user_data_dir(APP_NAME, APP_AUTHOR)

def logger(name):
    l = logging.getLogger(name)
    l.setLevel(logging.DEBUG)

    # TODO: Move handlers up to the top level and re-enable propagate
    l.propagate = False

    if len(l.handlers) == 0:
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        console.setLevel(logging.DEBUG)
        l.addHandler(console)

        if not os.path.isdir(os.path.join(SunriseSettings.logsPath)):
            os.makedirs(os.path.join(SunriseSettings.logsPath))

        file = logging.FileHandler(os.path.join(SunriseSettings.logsPath, "sunrise.log"))
        file.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        file.setLevel(logging.INFO)

        l.addHandler(file)

    return l

log = logger("main.helpers")

class Serde:
    reg = {}

    @staticmethod
    def register(tag, c):
        Serde.reg[tag] = c

def serialize(obj):
    if hasattr(obj, "serialize"):
        return obj.serialize()

    if type(obj) is dict:
        newObj = {}

        for k, v in obj.items():
            newObj[k] = serialize(v)

        return newObj

    if type(obj) is list:
        return list(map(serialize, obj))

    return obj

def unserialize(obj):
    if type(obj) is dict and "type" in obj:
        for t, c in Serde.reg.items():
            o = c.unserialize(obj)

            if not o == None:
                return o

    if type(obj) is dict:
        newObj = {}

        for k, v in obj.items():
            newObj[k] = unserialize(v)

        return newObj

    if type(obj) is list:
        return list(map(unserialize, obj))

    return obj

def isInstalled(store, id):
    installPath = store.settings.get("paths").binPath
    path = os.path.normpath(os.path.join(installPath, id))

    return os.path.isdir(path)

def createWidget(ui_file):
    ui_file = QFile(ui_file)
    ui_file.open(QFile.ReadOnly)

    loader = QUiLoader()
    widget = loader.load(ui_file)
    ui_file.close()

    return widget

def copyDir(src, dst):
    if not os.path.exists(dst):
        os.makedirs(dst)

    for item in os.listdir(src):
        srcItem = os.path.join(src, item)
        dstItem = os.path.join(dst, item)

        if os.path.isdir(s):
            copytree(srcItem, dstItem)
        else:
            shutil.copy2(srcItem, dstItem)

class uList:
    def __init__(self, data = None):
        self.list = data if data else []

    def push(self, item):
        if not item in self.list:
            log.debug("%s is not in list %s", item, self.list)
            self.list.insert(0, item)

    def swap(self, index1, index2):
        self.list[index1], self.list[index2] = self.list[index2], self.list[index1]

    def remove(self, item):
        if item in self.list:
            self.list.remove(item)

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        return iter(self.list)

    def serialize(self):
        rep = {}
        rep["type"] = "uList"
        rep["data"] = self.list

        return rep

    @staticmethod
    def unserialize(obj):
        if type(obj) is dict and "type" in obj and obj["type"] == "uList" and "data" in obj and type(obj["data"]) is list:
            return uList(list(map(unserialize, obj["data"])))

        return None

Serde.register("uList", uList)
