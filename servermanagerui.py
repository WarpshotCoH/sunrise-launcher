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

    @Slot()
    def reload(self):
        print("Reload server manager")
        servers = self.store.servers.values()
        hiddenIds = self.store.settings.get("hiddenServers")

        active = [s for s in servers if s.id not in hiddenIds]
        hidden  = [s for s in servers if s.id in hiddenIds]

        # if len(self.orderedServers) > 0:
        #     selectedServer = self.orderedServers[max(0, self.listUI.currentRow())]
        # else:
        #     selectedServer = None

        # Side-effect! This reorders the UI internal server storage
        # self.reorderServers()

        self.window.listWidget.clear()
        self.window.listWidget_2.clear()

        for server in active:
            QListWidgetItem(server.name, self.window.listWidget)

        for server in hidden:
            QListWidgetItem(server.name, self.window.listWidget_2)
