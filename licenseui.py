import os

from PySide2.QtCore import QObject, Signal, Slot, QSize, Qt
from PySide2.QtWidgets import QToolBox, QLabel

from helpers import createWidget, logger

log = logger("main.ui.about.license")

class LicenseUI(QObject):
    def __init__(self, store, parent = None):
        super(LicenseUI, self).__init__(parent)

        self.store = store
        self.ui = createWidget("ui/settings-about-license.ui")
        self.ui.setWindowTitle(self.store.s("ABOUT_LICENSE_HEADER"))
        self.licenseList = self.ui.licenseList

        self.getLicenses()
        self.setLicenseList()

    # Grab any .txt file from the licenses folder.
    def getLicenses(self):
        log.debug("Searching for licenses")
        self.licenses = {}

        for root, dirs, files in os.walk(os.path.abspath("resources/licenses")):
            for file in files:
                if not file.endswith(".txt"): continue

                log.debug("Found license %s", file)
                txt = open(os.path.join(root, file), "r")
                self.licenses[file.replace(".txt", "")] = txt.read()

    # Add licenses dictionary to a Qt ToolBox.
    def setLicenseList(self):
        log.debug("Adding licenses to UI")

        for licenseName, licenseText in sorted(self.licenses.items()):
            label = QLabel(licenseText)
            label.setWordWrap(True)

            self.licenseList.addItem(label, licenseName)
