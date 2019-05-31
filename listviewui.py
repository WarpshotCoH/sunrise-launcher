import sys

import requests
from PySide2.QtCore import QObject, Signal, Slot, QSize, Qt
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtWidgets import QListWidgetItem, QLabel, QToolButton, QMenu, QAction

from downloadui import DownloadUI
from helpers import createWidget, logger
from manifest import Server, Application, Runtime
from widgets.rightalignqmenu import RightAlignQMenu

log = logger("main.ui.details")

# TODO: Can / should this be abstract? Is that idomatic in Python?
#       Does that work with signals and slots?
class ListViewUI(QObject):
    selected = Signal(Application, Runtime, Server)
    verificationRequested = Signal()

    def __init__(self, store, parent):
        super(ListViewUI, self).__init__(parent)

        self.store = store
        self.ui = createWidget("ui/listview.ui")

        menu = RightAlignQMenu(self.ui.detailSettings)
        self.action1 = QAction(self.store.s("GAMES_DETAILS_SETTINGS_VERIFY"))
        self.action1.triggered.connect(lambda: self.verificationRequested.emit())
        self.action2 = QAction(self.store.s("GAMES_DETAILS_SETTINGS_UNINSTALL"))
        menu.addAction(self.action1)
        menu.addAction(self.action2)

        self.menu = menu

        self.ui.detailSettings.setMenu(self.menu)
        self.ui.detailSettings.setToolTip(self.store.s("GAMES_DETAILS_SETTINGS_BUTTON"))

        self.ui.detailWebsite.setToolTip(self.store.s("GAMES_DETAILS_WEBSITE_BUTTON"))

        self.listUI = createWidget("ui/list.ui")
        self.ui.serverListLayout.addWidget(self.listUI)

        self.header = self.listUI.listHeader
        self.list = self.listUI.listList

        self.downloadUI = DownloadUI(store, self.ui.downloadLayout)
        self.launch = self.downloadUI.launch

        self.selected.connect(self.downloadUI.load)
        self.selected.connect(self.loadDetails)

        self.verificationRequested.connect(self.downloadUI.fullVerifyDownload)

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

    @Slot(Application, Runtime, Server)
    def loadDetails(self, application = None, runtime = None, server = None):
        if server:
            self.ui.detailsName.setText(server.name)
            self.ui.detailsSubname1.setText(application.name)
            self.ui.detailsSubname1.show()
            self.ui.detailsSubname2.setText(runtime.name)
            self.ui.detailsSubname2.show()

            # We do not need to load here as the icon is either in the cache
            # from being loaded by the item list or it failed to load in the
            # item list and we are just going to ignore it
            if server.icon and self.store.cache.get(server.icon):
                self.ui.icon.setPixmap(self.store.cache.get(server.icon))
        elif application:
            if application:
                self.ui.detailsName.setText(application.name)
                self.ui.detailsSubname1.setText(runtime.name)
                self.ui.detailsSubname1.show()
                self.ui.detailsSubname2.setText("")
                self.ui.detailsSubname2.show()

                # We do not need to load here as the icon is either in the cache
                # from being loaded by the item list or it failed to load in the
                # item list and we are just going to ignore it
                if application.icon and self.store.cache.get(application.icon):
                    self.ui.icon.setPixmap(self.store.cache.get(application.icon))
        elif runtime:
            if runtime:
                self.ui.detailsName.setText(runtime.name)
                self.ui.detailsSubname1.hide()
                self.ui.detailsSubname2.hide()

                # We do not need to load here as the icon is either in the cache
                # from being loaded by the item list or it failed to load in the
                # item list and we are just going to ignore it
                if runtime.icon and self.store.cache.get(runtime.icon):
                    self.ui.icon.setPixmap(self.store.cache.get(runtime.icon))

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

        listItem.setSizeHint(w.sizeHint())

        self.list.setItemWidget(listItem, w)

        return listItem
