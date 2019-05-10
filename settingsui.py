from PySide2.QtCore import QObject, QThread, Slot, Signal
from PySide2.QtWidgets import QFileDialog

class SettingsUI(QObject):
    def __init__(self, store, pathField, dirBrowseButton, parent = None):
        super(SettingsUI, self).__init__(parent)

        self.store = store
        self.pathField = pathField
        self.dirBrowseButton = dirBrowseButton

        self.dirBrowseButton.clicked.connect(self.selectPath)
        self.store.settings.connectKey("paths", self.updatePathLabel)

    @Slot(str)
    def updatePathLabel(self, key = None):
        self.pathField.setText(self.store.settings.get("paths").binPath)

    def selectPath(self):
        path = QFileDialog().getExistingDirectory()

        if path:
            paths = self.store.settings.get("paths")
            paths.binPath = path
            self.store.settings.set("paths", paths)
            self.store.settings.commit()
