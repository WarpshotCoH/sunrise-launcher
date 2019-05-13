from PySide2.QtCore import QFile, QObject, Signal, Slot, QSize
from PySide2.QtGui import QIcon, QImage, QPixmap
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QListWidgetItem, QLabel
import requests

from manifest import Server, Application, Runtime

class ServerListUI(QObject):
    selected = Signal(Application, Runtime, Server)

    def __init__(self, store, listUI, parent=None):
        super(ServerListUI, self).__init__(parent)

        self.store = store
        self.listUI = listUI

        self.reorderServers()

        self.listUI.currentRowChanged.connect(self.selectServer)

        # Connect the server list so that it updates when hidden servers are added / removed
        self.store.settings.connectKey("hiddenServers", self.reload)

        # Connect the server list so that it updates when servers update
        self.store.updated.connect(self.reload)

        # Refresh the server manager list when manifests update
        self.store.updated.connect(self.reload)

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

                application = self.store.applications.get(server.application)

                itemWidget = ServerListUI.createItemWidget("serverlist-item.ui")
                itemWidget.findChild(QLabel, "server").setText(server.name)
                itemWidget.findChild(QLabel, "application").setText(application.name)

                # TODO: Move off-thread for slow loading. Maybe an image loading pool?
                if not self.store.cache.get(application.icon):
                    data = requests.get(application.icon, stream=True, allow_redirects=True).content # TODO: handle 404/missing icon?
                    qImage = QImage.fromData(data)
                    self.store.cache[application.icon] = QPixmap.fromImage(qImage)

                itemWidget.findChild(QLabel, "icon").setPixmap(self.store.cache.get(application.icon))

                item = QListWidgetItem()
                self.listUI.addItem(item)

                item.setSizeHint(QSize(-1, 64))

                self.listUI.setItemWidget(item, itemWidget)


            self.listUI.setCurrentRow(newIndex)

    @staticmethod
    def createItemWidget(ui_file):
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        widget = loader.load(ui_file)
        ui_file.close()

        return widget
