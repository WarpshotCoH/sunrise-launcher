from PySide2.QtCore import Slot

from listviewui import ListViewUI
from manifest import Server, Application, Runtime

from helpers import logger

log = logger("main.ui.serverlist")

class ServerListUI(ListViewUI):
    def __init__(self, store, parent):
        super(ServerListUI, self).__init__(store, parent)

        self.header.hide()
        self.list.currentRowChanged.connect(self.selectServer)

        # Connect the server list so that it updates when hidden servers are added / removed
        self.store.settings.connectKey("hiddenServers", self.reload)

    def computeServerOrder(self):
        recentSettings = self.store.settings.get("recentServers")

        if recentSettings:
            order = recentSettings.recent

            for id in self.store.servers.keys():
                if not id in order:
                    order.append(id)

            return order

        return []

    @Slot(int)
    def selectServer(self, row):
        if row < len(self.store.servers) + 1 and row > -1:
            # Offset row by one to account for header element
            server = list(self.store.servers.values())[row - 1]

            if server:
                app = self.store.applications.get(server.application)

                if app:
                    runtime = self.store.runtimes.get(app.runtime)

                    if runtime:
                        log.info("Selected server %s %s %s", server.id, app.id, runtime.id)
                        self.selected.emit(app, runtime, server)
        else:
            self.selected.emit(None, None, None)

    @Slot(str)
    def reload(self, key = None):
        log.debug("Reload server list")
        order = self.computeServerOrder()
        servers = sorted(self.store.servers.values(), key = lambda s: order.index(s.id))

        if len(servers) > 0:
            selectedServer = servers[max(0, self.list.currentRow())]
        else:
            selectedServer = None

        hidden = self.store.settings.get("hiddenServers")

        self.list.clear()

        # Now we sync the new order up to the actual displayed UI
        if len(servers) > 0:
            self.addHeader("Servers")

            newIndex = -1

            for i, server in enumerate(servers):
                if selectedServer and selectedServer.id == server.id and not server.id in hidden:
                    newIndex = i

                application = self.store.applications.get(server.application)

                self.addListItem(server.name, application.name, application.icon)

                if server.id in hidden:
                    item.hide()

            self.list.setCurrentRow(newIndex)
