import logging
import os
import sys

from appdirs import user_log_dir
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader

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

        file = logging.FileHandler(os.path.join(user_log_dir("Sunrise", "Sunrise"), "sunrise.log"))
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

    def __iter__(self):
        return iter(self.list)


