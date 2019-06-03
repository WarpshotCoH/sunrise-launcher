import logging
import os
import shutil
import sys

from appdirs import user_data_dir, user_log_dir
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader

APP_NAME = "Sunrise"
APP_AUTHOR = "Sunrise"

class SunriseSettings:
    settingsPath = user_data_dir(APP_NAME, APP_AUTHOR)
    logsPath = user_log_dir(APP_NAME, APP_AUTHOR)

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

class uList:
    def __init__(self):
        self.list = []

    def push(self, item):
        if not item in self.list:
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
