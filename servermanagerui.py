from PySide2.QtCore import QObject, QThread, Slot, Signal
from PySide2.QtWidgets import QFileDialog, QListWidgetItem
# from PySide2.QtWidgets import QApplication, QMainWindow, QPushButton, QListWidget,


class ServerManagerUI(QObject):

    def __init__(self, store, serverManagerWindow, parent=None):
        super(ServerManagerUI, self).__init__(parent)

        self.store = store
        self.newHidden = self.store.settings.get("hiddenServers")

        # TODO: Should this boot its own UI? Instead of accept an arg
        self.window = serverManagerWindow

        self.store.updated.connect(self.updateNewHiddenServers)
        self.store.settings.connectKey("hiddenServers", self.updateNewHiddenServers)
        self.window.addServer.clicked.connect(self.showServer)
        self.window.delServer.clicked.connect(self.hideServer)
        self.window.controls.accepted.connect(self.commitHiddenServers)
        self.window.controls.rejected.connect(self.resetNewHiddenServers)

    @Slot()
    def show(self):
        self.window.show()

    @Slot()
    def hide(self):
        self.window.hide()

    def getServers(self):
        servers = self.store.servers.values()

        active = [s for s in servers if s.id not in self.newHidden]
        hidden  = [s for s in servers if s.id in self.newHidden]

        return [active, hidden]

    @Slot()
    def showServer(self):
        self.newHidden.remove(self.getSelectedServerId())
        self.reload()

    @Slot()
    def hideServer(self):
        self.newHidden.add(self.getSelectedServerId())
        self.reload()

    def commitHiddenServers(self):
        self.store.settings.set("hiddenServers", self.newHidden)
        self.store.settings.commit()
        self.hide()

    @Slot()
    def resetNewHiddenServers(self):
        self.newHidden = self.store.settings.get("hiddenServers")
        self.reload()
        self.hide()

    @Slot(str)
    def updateNewHiddenServers(self, key = None):
        if self.store.settings.get("hiddenServers"):
            self.newHidden = self.newHidden.union(self.store.settings.get("hiddenServers"))
            self.reload()

    def getSelectedServerId(self):
        [active, hidden] = self.getServers()

        index = self.window.activeServers.currentRow()

        if not index == -1:
            return active[index].id
        else:
            index = self.window.hiddenServers.currentRow()

            if not index == -1:
                return hidden[index].id
            else:
                return None

    @Slot(str)
    def reload(self, key = None):
        print("Reload server manager")
        [active, hidden] = self.getServers()

        self.window.activeServers.clear()
        self.window.hiddenServers.clear()

        for server in active:
            QListWidgetItem(server.name, self.window.activeServers)

        for server in hidden:
            QListWidgetItem(server.name, self.window.hiddenServers)
