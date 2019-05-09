from PySide2.QtCore import QObject, QThread, Slot, Signal

class SettingsUI(QObject):
    change = Signal(str, Union[str, int, bool])
    commit = Signal(dict)
    cancel = Signal()

    def __init__(self, parent = None)
        super(SettingsUI, self).__init__(parent)

        # Settings are a simple key value store
        settings = {}

    def load(self, settings):
        self.settings = settings

    # TODO: Wire to the UI
