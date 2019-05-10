from PySide2.QtCore import QObject, Signal, Slot
from PySide2.QtWidgets import QListWidgetItem

from manifest import Server, Application, Runtime

class ServerListUI(QObject):
    selected = Signal(Application, Runtime, Server)

    def __init__(self, store, listUI, parent=None):
        super(ServerListUI, self).__init__(parent)

        self.store = store
        self.listUI = listUI

        self.reorderServers()

        self.listUI.currentRowChanged.connect(self.selectServer)
        self.store.settings.connectKey("hiddenServers", self.reload)

    def reorderServers(self):
        hidden = self.store.settings.get("hiddenServers")
        order = self.computeServerOrder()
        self.orderedServers = list(
            sorted(
                filter(lambda s: not s.id in hidden, self.store.servers.values()),
                key = lambda s: order.index(s.id)
            )
        )

    def computeServerOrder(self):
        order = self.store.settings.get("recentServers").recent

        for id in self.store.servers.keys():
            if not id in order:
                order.append(id)

        return order

    @Slot(int)
    def selectServer(self, row):
        if len(self.orderedServers) > 0 and row > -1:
            if len(self.orderedServers) < row:
                return
            server = self.orderedServers[row]

            if server:
                app = self.store.applications.get(server.application)

                if app:
                    runtime = self.store.runtimes.get(app.runtime)

                    if runtime:
                        print("Selected server", server.id, app.id, runtime.id)
                        self.selected.emit(app, runtime, server)

    @Slot(str)
    def reload(self, key = None):
        print("Reload server list")
        if len(self.orderedServers) > 0:
            selectedServer = self.orderedServers[max(0, self.listUI.currentRow())]
        else:
            selectedServer = None

        # Side-effect! This reorders the UI internal server storage
        self.reorderServers()

        self.listUI.clear()

        # Now we sync the new order up to the actual displayed UI
        if len(self.orderedServers) > 0:
            newIndex = 0

            for i, server in enumerate(self.orderedServers):
                if selectedServer and selectedServer.id == server.id:
                    newIndex = i

                QListWidgetItem(server.name, self.listUI)


            self.listUI.setCurrentRow(newIndex)
