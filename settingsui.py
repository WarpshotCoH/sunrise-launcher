from PySide2.QtCore import QObject, QThread, Slot, Signal
from PySide2.QtWidgets import QFileDialog, QPushButton

from helpers import createWidget
from manifestui import ManifestUI
from settings import Settings

class SettingsUI(QObject):
    tabSelected = Signal(int)

    def __init__(self, store, parent):
        super(SettingsUI, self).__init__(parent)

        self.store = store

        self.ui = createWidget("ui/settings-v2.ui")

        header = createWidget("ui/settings-menu.ui")
        self.headerButtons = header.findChildren(QPushButton)
        self.bindHeaderButtons()

        general = createWidget("ui/settings-general.ui")
        self.ui.settingsBodyLayout.addWidget(general)

        # TODO: Break tabs into their own classes as they become complex
        self.tabs = [
            general,
            # createWidget("ui/settings-manifest.ui")
            ManifestUI(store, self.ui.settingsBodyLayout).ui
        ]

        self.ui.settingsHeaderLayout.addWidget(header)

        self.selectTab(0)

        self.tabSelected.connect(self.selectTab)

        self.store.settings.committed.connect(self.update)

        parent.addWidget(self.ui)

    def hide(self):
        self.ui.hide()

    def show(self):
        self.ui.show()

    def selectTab(self, index):
        for tab in self.tabs:
            tab.hide()

        self.tabs[index].show()

    @Slot(Settings)
    def update(self, settings):
        return True

    def bindHeaderButtons(self):
        for i, button in enumerate(self.headerButtons):
            button.clicked.connect(self.bindFactory(i))

    def bindFactory(self, i):
        def f():
            for j, button in enumerate(self.headerButtons):
                button.setProperty("Active", i == j)

                # Refresh styles
                button.setStyle(button.style())

            self.tabSelected.emit(i)

        return f
