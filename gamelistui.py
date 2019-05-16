from PySide2.QtCore import QFile, QObject, Signal, Slot, QSize, QEvent, Qt
from PySide2.QtGui import QIcon, QImage, QPixmap, QWheelEvent
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QListWidgetItem, QLabel, QListWidget, QScrollArea
import requests

from manifest import Server, Application, Runtime

class GameListUI(QObject):
    selected = Signal(Application, Runtime, Server)

    def __init__(self, store, uiFile, parent=None):
        super(GameListUI, self).__init__(parent)

        self.store = store
        self.ui = GameListUI.createWidget(uiFile)
        self.header = self.ui.findChild(QLabel, "listHeader")
        self.header.hide()
        self.list = self.ui.findChild(QListWidget, "listList")

        self.offsets = [[0, 0], [0, 0], [0, 0]];

        self.store.updated.connect(self.reload)
        self.list.currentRowChanged.connect(self.selectItem)

    def show(self):
        self.ui.show()

    def hide(self):
        self.ui.hide()

    @Slot(int)
    def selectItem(self, row):
        if row > -1:
            for i, group in enumerate(self.offsets):
                if group[0] <= row and row <= group[1]:
                    index = row - group[0]
                    print("Selected games index", index)

                    if i == 0:
                        tools = self.store.getTools()
                        tool = tools[index]

                        if tool:
                            runtime = self.store.runtimes.get(tool.runtime)

                            if runtime:
                                self.selected.emit(tool, runtime, None)
                                return
                    elif i == 1:
                        clients = self.store.getClients()
                        client = clients[index]

                        if client:
                            runtime = self.store.runtimes.get(client.runtime)

                            if runtime:
                                self.selected.emit(client, runtime, None)
                                return
                    elif i == 2:
                        runtime = list(self.store.runtimes.values())[index]

                        if runtime:
                            self.selected.emit(None, runtime, None)
                            return

    @Slot(str)
    def reload(self, key = None):
        print("Reload games list")

        self.list.clear()

        mods = self.store.getTools()
        clients = self.store.getClients()

        self.addHeader(self.list, "Mods / Tools")
        for i, mod in enumerate(mods):
            self.addListItem(self.list, mod)
        self.offsets[0] = (1, 1 + len(mods))

        self.addHeader(self.list, "Clients")
        for i, client in enumerate(clients):
            self.addListItem(self.list, client)
        self.offsets[1] = [self.offsets[0][1] + 1, self.offsets[0][1] + 1 + len(clients)]

        self.addHeader(self.list, "Runtimes")
        for i, runtime in enumerate(self.store.runtimes.values()):
            self.addListItem(self.list, runtime)
        self.offsets[2] = [self.offsets[1][1] + 1, self.offsets[1][1] + 1 + len(self.store.runtimes)]

    def addHeader(self, uiList, label):
        header = QLabel()
        header.setText(label)
        header.setProperty("ListSubhead", True)
        font = header.font()
        font.setPointSize(12)
        header.setFont(font)

        listItem = QListWidgetItem()
        listItem.setFlags(listItem.flags() & ~Qt.ItemIsSelectable)
        uiList.addItem(listItem)

        # TODO: Supposed to be able to get the size hint from the custom
        #       widget and assign it here, but I can not seem to figure
        #       it out
        listItem.setSizeHint(QSize(-1, 24))

        uiList.setItemWidget(listItem, header)

    def addListItem(self, uiList, item):
        w = GameListUI.createWidget("serverlist-item.ui")
        w.findChild(QLabel, "server").setText(item.name)
        w.findChild(QLabel, "application").setText("Not installed")

        # TODO: Move off-thread for slow loading. Maybe an image loading pool?
        if hasattr(item, "icon"):
            if not self.store.cache.get(item.icon):
                data = requests.get(item.icon, stream=True, allow_redirects=True).content # TODO: handle 404/missing icon?
                qImage = QImage.fromData(data)
                self.store.cache[item.icon] = QPixmap.fromImage(qImage)

            w.findChild(QLabel, "icon").setPixmap(self.store.cache.get(item.icon))

        listItem = QListWidgetItem()
        uiList.addItem(listItem)

        # TODO: Supposed to be able to get the size hint from the custom
        #       widget and assign it here, but I can not seem to figure
        #       it out
        listItem.setSizeHint(QSize(-1, 64))

        uiList.setItemWidget(listItem, w)

    @staticmethod
    def createWidget(ui_file):
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        widget = loader.load(ui_file)
        ui_file.close()

        return widget
