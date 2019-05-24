import webbrowser

from PySide2.QtCore import QObject, Signal, Slot, QSize, Qt
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtWidgets import QListWidgetItem, QLabel

from helpers import createWidget, logger
from licenseui import LicenseUI
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

        self.store = store
        self.ui = createWidget("ui/settings-about.ui")
        self.licenses = LicenseUI(store).ui

        self.bindButtons()

        self.layoutText()

        parent.addWidget(self.ui)

    def layoutText(self):

        # Set application and credit text
        self.ui.title.setText(self.store.s("ABOUT_TITLE"))
        self.ui.updatedAt.setText(self.store.s("ABOUT_UPDATED"))
        self.ui.baseCredit.setText(self.store.s("ABOUT_CREDIT"))

        # Set informational button text
        self.ui.customAbout1.setText(self.store.s("ABOUT_CUSTOM_BUTTON_1"))
        self.ui.customAbout2.setText(self.store.s("ABOUT_CUSTOM_BUTTON_2"))
        self.ui.sourceButton.setText(self.store.s("ABOUT_SOURCE_BUTTON"))
        self.ui.licenseButton.setText(self.store.s("ABOUT_LICENSE_BUTTON"))

        # Set dev text
        self.ui.creditHeader1.setText(self.store.s("ABOUT_DEV_HEADER_1"))
        self.ui.creditContent1.setText("\n".join(self.store.s("ABOUT_DEV_CONTENT_1")))
        self.ui.creditHeader2.setText(self.store.s("ABOUT_DEV_HEADER_2"))
        self.ui.creditContent2.setText("\n".join(self.store.s("ABOUT_DEV_CONTENT_2")))

    def bindButtons(self):
        bindUrl(self.ui.customAbout1, self.store.config['about']['about_button_1_url'])
        bindUrl(self.ui.customAbout2, self.store.config['about']['about_button_2_url'])
        bindUrl(self.ui.sourceButton, self.store.config['about']['source_url'])

        self.ui.licenseButton.clicked.connect(lambda: self.licenses.show())

    @Slot()
    def displayLicenses(self, key = None):
        log.debug("Reload manifest list")
        self.list.clear()

        for url in self.store.settings.get("manifestList"):
            self.addListItem(
                self.store.manifestNames[url] if url in self.store.manifestNames else "",
                url
            )
