import logging
import os
import sys

from appdirs import user_log_dir
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader

def logger(name):
    l = logging.getLogger(name)
    l.setLevel(logging.DEBUG)
    handler = logging.FileHandler(os.path.join(user_log_dir("Sunrise", "Sunrise"), "sunrise.log"))
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    l.addHandler(handler)
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

    def __iter__(self):
        return iter(self.list)


