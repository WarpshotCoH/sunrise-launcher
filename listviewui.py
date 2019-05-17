import requests
from PySide2.QtCore import QObject, Signal, Slot, QSize, Qt
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtWidgets import QListWidgetItem, QLabel

from downloadui import DownloadUI
from helpers import createWidget
from manifest import Server, Application, Runtime

# TODO: Can / should this be abstract? Is that idomatic in Python?
#       Does that work with signals and slots?
class ListViewUI(QObject):
    selected = Signal(Application, Runtime, Server)

    def __init__(self, store, parent):
        super(ListViewUI, self).__init__(parent)

        self.store = store
        self.ui = createWidget("ui/listview.ui")

        self.listUI = createWidget("ui/list.ui")
        self.ui.serverListLayout.addWidget(self.listUI)

        self.header = self.listUI.listHeader
        self.list = self.listUI.listList

        self.downloadUI = DownloadUI(store, self.ui.downloadLayout)
        self.launch = self.downloadUI.launch

        self.selected.connect(self.downloadUI.load)

        parent.addWidget(self.ui)

        # Refresh the server manager list when manifests update
        self.store.updated.connect(self.reload)

    # TODO: Implement updating the details section on selection

    def show(self):
        self.ui.show()

    def hide(self):
        self.ui.hide()

    def clear(self):
        self.list.setCurrentRow(-1)

    def shutdown(self):
        self.downloadUI.shutdown()

    @Slot(str)
    def reload(self, key = None):
        return True

    def addHeader(self, label):
        header = QLabel()
        header.setText(label)
        header.setProperty("ListSubhead", True)
        header.setAlignment(Qt.AlignVCenter)

        listItem = QListWidgetItem()
        listItem.setFlags(listItem.flags() & ~Qt.ItemIsSelectable)
        self.list.addItem(listItem)

        # TODO: Supposed to be able to get the size hint from the custom
        #       widget and assign it here, but I can not seem to figure
        #       it out
        listItem.setSizeHint(QSize(-1, 24))

        self.list.setItemWidget(listItem, header)

    def addListItem(self, name, label, icon = None):
        w = createWidget("ui/listview-item.ui")
        w.findChild(QLabel, "name").setText(name)
        w.findChild(QLabel, "label").setText(label)

        # TODO: Move off-thread for slow loading. Maybe an image loading pool?
        if icon:
            if not self.store.cache.get(icon):
                data = requests.get(icon, stream=True, allow_redirects=True).content # TODO: handle 404/missing icon?
                qImage = QImage.fromData(data)
                self.store.cache[icon] = QPixmap.fromImage(qImage)

            w.findChild(QLabel, "icon").setPixmap(self.store.cache.get(icon))

        listItem = QListWidgetItem()
        self.list.addItem(listItem)

        # TODO: Supposed to be able to get the size hint from the custom
        #       widget and assign it here, but I can not seem to figure
        #       it out
        listItem.setSizeHint(w.sizeHint())

        self.list.setItemWidget(listItem, w)

        return listItem
