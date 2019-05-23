import webbrowser

from PySide2.QtCore import QObject, Signal, Slot, QSize, Qt
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtWidgets import QListWidgetItem, QLabel

from helpers import createWidget, logger
from listviewui import ListViewUI

log = logger("main.ui.about")

def bindUrl(button, url):
    try:
        button.clicked.disconnect()
    except Exception:
        pass

    button.clicked.connect(lambda: openExternalSite(url))

def openExternalSite(url):
    webbrowser.open_new_tab(url)

class AboutUI(QObject):
    def __init__(self, store, parent):
        super(AboutUI, self).__init__(parent)

        self.ui = createWidget("ui/settings-about.ui")
        self.bindButtons()

        parent.addWidget(self.ui)

    def bindButtons(self):
        bindUrl(self.ui.customAbout1, "")
        bindUrl(self.ui.customAbout2, "")
        bindUrl(self.ui.sourceButton, "")

        # bindUrl(self.ui.licenseButton, "")

    @Slot()
    def displayLicenses(self, key = None):
        log.debug("Reload manifest list")
        self.list.clear()

        for url in self.store.settings.get("manifestList"):
            self.addListItem(
                self.store.manifestNames[url] if url in self.store.manifestNames else "",
                url
            )
