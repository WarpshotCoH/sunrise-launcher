from PySide2.QtCore import Slot, Qt

from helpers import createWidget

class GeneralSettingsUI:
    def __init__(self, store, parent):
        self.store = store

        self.ui = createWidget("ui/settings-general.ui")
        self.themeSelect = self.ui.themeSelector

        self.ui.autoCloseOption.stateChanged.connect(self.autoCloseChange)
        self.ui.autoPatchOption.stateChanged.connect(self.autoPatchChange)
        self.themeSelect.currentIndexChanged.connect(self.themeChange)

        self.store.updated.connect(lambda: self.reload(None))

        parent.addWidget(self.ui)

    @Slot(Qt.CheckState)
    def autoCloseChange(self, state):
        self.store.settings.set("autoClose", state == Qt.Checked)

    @Slot(Qt.CheckState)
    def autoPatchChange(self, state):
        self.store.settings.set("autoPatch", state == Qt.Checked)

    @Slot(int)
    def themeChange(self, index):
        print("Theme change", index)
        if not index == -1:
            self.store.settings.set("theme", self.themeSelect.itemText(index))
            self.store.settings.commit()

    @Slot(str)
    def reload(self, key = None):
        print("Reload general settings")
        selectedTheme = self.store.settings.get("theme")
        self.themeSelect.clear()

        for themeName in sorted(self.store.themes.keys()):
            self.themeSelect.addItem(themeName)

        # TODO: This requires a key existance check. User may have deleted the theme between runs
        self.themeSelect.setCurrentText(selectedTheme)
