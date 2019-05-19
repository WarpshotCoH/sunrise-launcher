from PySide2.QtCore import Slot

from helpers import createWidget

class GeneralSettingsUI:
    def __init__(self, store, parent):
        self.store = store

        self.ui = createWidget("ui/settings-general.ui")
        self.themeSelect = self.ui.themeSelector

        self.themeSelect.currentIndexChanged.connect(self.themeChange)
        self.store.updated.connect(lambda: self.reload(None))

        parent.addWidget(self.ui)

    @Slot(str)
    def reload(self, key = None):
        print("Reload general settings")
        self.themeSelect.clear()

        for themeName in sorted(self.store.themes.keys()):
            self.themeSelect.addItem(themeName)

    @Slot(int)
    def themeChange(self, index):
        if not index == -1:
            self.store.settings.set("theme", self.themeSelect.itemText(index))
            self.store.settings.commit()
