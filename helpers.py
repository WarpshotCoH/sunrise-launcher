import os

from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader

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


