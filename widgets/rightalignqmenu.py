from PySide2.QtWidgets import QMenu

from helpers import logger

log = logger("main.ui.widgets.rightalignqmenu")

class RightAlignQMenu(QMenu):
    def __init__(self, parent = None):
        super(RightAlignQMenu, self).__init__(parent)
        self.parent = parent

    def showEvent(self, event):
        pos = self.pos();
        geo = self.parent.geometry();
        self.move(pos.x() + geo.width() - self.geometry().width(), pos.y() + 6)
