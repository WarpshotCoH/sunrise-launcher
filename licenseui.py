from PySide2.QtCore import QObject, Signal, Slot, QSize, Qt
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtWidgets import QListWidgetItem, QLabel

from helpers import createWidget, logger

log = logger("main.ui.about.license")

class LicenseUI(QObject):
    def __init__(self, store, parent = None):
        super(LicenseUI, self).__init__(parent)

        self.store = store
        self.ui = createWidget("ui/settings-about-license.ui")
        self.ui.setWindowTitle(self.store.s("ABOUT_LICENSE_HEADER"))

        self.layoutText()

    def layoutText(self):
        return True
