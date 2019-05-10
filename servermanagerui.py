from PySide2.QtCore import QObject, QThread, Slot, Signal
from PySide2.QtWidgets import QFileDialog, QListWidgetItem
# from PySide2.QtWidgets import QApplication, QMainWindow, QPushButton, QListWidget,


class ServerManagerUI(QObject):

    def __init__(self, store, serverManagerWindow, parent=None):
        super(ServerManagerUI, self).__init__(parent)

        self.store = store

        # TODO: Should this boot its own UI? Instead of accept an arg
        self.window = serverManagerWindow

        self.store.updated.connect(self.reload)
        self.store.settings.connectKey("hiddenServers", self.reload)
        self.window.addServer.clicked.connect(self.showServer)
        self.window.delServer.clicked.connect(self.hideServer)

    def getServers(self):
        servers = self.store.servers.values()
        hiddenIds = self.store.settings.get("hiddenServers")

        active = [s for s in servers if s.id not in hiddenIds]
        hidden  = [s for s in servers if s.id in hiddenIds]

        return [active, hidden]

    @Slot()
    def showServer(self):
        hidden = self.store.settings.get("hiddenServers")
        hidden.remove(self.getSelectedServerId())
        self.store.settings.set("hiddenServers", hidden)
        self.store.settings.commit()

    @Slot()
    def hideServer(self):
        hidden = self.store.settings.get("hiddenServers")
        hidden.add(self.getSelectedServerId())
        self.store.settings.set("hiddenServers", hidden)
        self.store.settings.commit()

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
