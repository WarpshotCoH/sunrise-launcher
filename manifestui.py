from PySide2.QtCore import Slot, QSize
from PySide2.QtWidgets import QListWidgetItem, QLabel

from helpers import createWidget

class ManifestUI:
    def __init__(self, store, parent):
        self.store = store

        self.ui = createWidget("ui/settings-manifest.ui")
        self.list = self.ui.manifestSourceList

        self.store.settings.connectKey("manifestList", self.reload)

        parent.addWidget(self.ui)

    @Slot(str)
    def reload(self, key):
        print("Reload manifest list")
        self.list.clear()

        for manifest in self.store.settings.get("manifestList"):
            self.addListItem(manifest[1].name, manifest[0])

    def addListItem(self, name, url):
        w = createWidget("ui/settings-manifest-item.ui")
        w.findChild(QLabel, "manifestItemName").setText(name)
        w.findChild(QLabel, "manifestItemUrl").setText(url)

        listItem = QListWidgetItem()
        self.list.addItem(listItem)

        # TODO: Supposed to be able to get the size hint from the custom
        #       widget and assign it here, but I can not seem to figure
        #       it out
        listItem.setSizeHint(w.sizeHint())

        self.list.setItemWidget(listItem, w)

        return listItem
