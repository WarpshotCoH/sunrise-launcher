from PySide2.QtCore import QObject, QThread, Slot, Signal
from PySide2.QtWidgets import QFileDialog, QPushButton

from aboutui import AboutUI
from generalsettingsui import GeneralSettingsUI
from helpers import createWidget
from manifestui import ManifestUI
from settings import Settings

class SettingsUI(QObject):
    tabSelected = Signal(int)

    def __init__(self, store, parent):
        super(SettingsUI, self).__init__(parent)

        self.store = store

        self.ui = createWidget("ui/settings-v2.ui")

        self.header = createWidget("ui/settings-menu.ui")

        self.headerButtons = self.header.findChildren(QPushButton)
        self.bindHeaderButtons()

        # TODO: Break tabs into their own classes as they become complex
        self.tabs = [
            GeneralSettingsUI(store, self.ui.settingsBodyLayout).ui,
            ManifestUI(store, self.ui.settingsBodyLayout).ui,
            None,
            AboutUI(store, self.ui.settingsBodyLayout).ui
        ]

        self.ui.settingsHeaderLayout.addWidget(self.header)

        self.selectTab(0)

        self.tabSelected.connect(self.selectTab)

        self.store.settings.committed.connect(self.update)

        self.layoutText()

        # Disabled until server settings are implemented
        self.header.settingsServerButton.hide()

        parent.addWidget(self.ui)

    def layoutText(self):
        self.header.settingsGeneralButton.setText(self.store.s("SETTINGS_MENU_GENERAL"))
        self.header.settingsManifestButton.setText(self.store.s("SETTINGS_MENU_MANIFESTS"))
        self.header.settingsServerButton.setText(self.store.s("SETTINGS_MENU_SERVERS"))
        self.header.settingsAboutButton.setText(self.store.s("SETTINGS_MENU_ABOUT"))

    def hide(self):
        self.ui.hide()

    def show(self):
        self.ui.show()

    def selectTab(self, index):
        for tab in self.tabs:
            if tab:
                tab.hide()

        if self.tabs[index]:
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
