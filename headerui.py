from copy import copy
from enum import Enum

from PySide2.QtCore import QFile, QObject, Signal, Slot, QSize
from PySide2.QtWidgets import QLabel, QPushButton

from helpers import createWidget

class HeaderUI(QObject):
    itemSelected = Signal(int)

    def __init__(self, parent):
        super(HeaderUI, self).__init__(parent)

        self.ui = createWidget("ui/header.ui")
        parent.addWidget(self.ui)

        self.items = self.ui.findChildren(QPushButton)
        self.items[0].setProperty("Active", True)

        self.bindItems()

    def bindItems(self):
        for i, item in enumerate(self.items):
            item.clicked.connect(self.bindFactory(i))

    def bindFactory(self, i):
        def f():
            for j, item in enumerate(self.items):
                item.setProperty("Active", i == j)

                # Refresh styles
                item.setStyle(item.style())

            self.itemSelected.emit(i)

        return f

