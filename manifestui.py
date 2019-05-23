from PySide2.QtCore import Slot, QSize
from PySide2.QtWidgets import QListWidgetItem, QLabel, QPushButton

from helpers import createWidget, logger

log = logger("main.ui.manifests")

class ManifestUI:
    def __init__(self, store, parent):
        self.store = store

        self.ui = createWidget("ui/settings-manifest.ui")
        self.list = self.ui.manifestSourceList

        self.ui.manifestSourceAdd.clicked.connect(self.addManifestSource)
        self.ui.manifestSourceInput.returnPressed.connect(self.addManifestSource)

        self.store.settings.connectKey("manifestList", self.reload)

        self.layoutText()

        parent.addWidget(self.ui)

    def layoutText(self):
        self.ui.manifestSourceLabel.setText(self.store.s("MANIFEST_SOURCES"))
        self.ui.manifestSourceHelp.setText(self.store.s("MANIFEST_DESCRIPTION"))
        self.ui.manifestSourceInput.setPlaceholderText(self.store.s("MANIFEST_URL_PLACEHOLDER"))
        self.ui.manifestSourceAdd.setText(self.store.s("MANIFEST_URL_ADD"))

    @Slot(str)
    def reload(self, key = None):
        log.debug("Reload manifest list")
        self.list.clear()

        for url in self.store.settings.get("manifestList"):
            self.addListItem(
                self.store.manifestNames[url] if url in self.store.manifestNames else "",
                url
            )

    @Slot()
    def addManifestSource(self):
        if len(self.ui.manifestSourceInput.text()) > 0:
            mList = self.store.settings.get("manifestList")
            mList.push(self.ui.manifestSourceInput.text())
            self.store.settings.set("manifestList", mList)
            self.store.settings.commit()

            self.ui.manifestSourceInput.clear()
        else:
            log.warning("Ignoring empty manifest source input")

    def addListItem(self, name, url):
        w = createWidget("ui/settings-manifest-item.ui")

        w.findChild(QLabel, "manifestItemName").setText(name)

        if (len(name) == 0):
            w.findChild(QLabel, "manifestItemName").hide()

        w.findChild(QLabel, "manifestItemUrl").setText(url)

        if (len(url) == 0):
            w.findChild(QLabel, "manifestItemUrl").hide()

        listItem = QListWidgetItem()
        self.list.addItem(listItem)

        w.findChild(QPushButton, "manifestItemRemove").clicked.connect(self.removeFactory(url))
        w.findChild(QPushButton, "manifestItemUp").clicked.connect(self.moveUpFactory(listItem))
        w.findChild(QPushButton, "manifestItemDown").clicked.connect(self.moveDownFactory(listItem))

        listItem.setSizeHint(w.sizeHint())

        self.list.setItemWidget(listItem, w)

        return listItem

    def moveUpFactory(self, widgetItem):
        def f():
            index = self.list.indexFromItem(widgetItem).row()

            if index > 0:
                mList = self.store.settings.get("manifestList")
                mList.swap(index, index - 1)
                self.store.settings.set("manifestList", mList)
                self.store.settings.commit()

        return f

    def moveDownFactory(self, widgetItem):
        def f():
            index = self.list.indexFromItem(widgetItem).row()

            if index < self.list.count() - 1:
                mList = self.store.settings.get("manifestList")
                mList.swap(index, index + 1)
                self.store.settings.set("manifestList", mList)
                self.store.settings.commit()

        return f

    def removeFactory(self, url):
        def f():
            mList = self.store.settings.get("manifestList")
            mList.remove(url)
            self.store.settings.set("manifestList", mList)
            self.store.settings.commit()

        return f
