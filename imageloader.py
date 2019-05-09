from PySide2.QtCore import QObject, Signal, Slot

# TODO: Make a global thread pool for image loading
class ImageLoader(QObject):
    selected = Signal()

    def __init__(self):
        super(ImageLoader, self).__init__(parent)
