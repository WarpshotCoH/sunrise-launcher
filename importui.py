from PySide2.QtCore import QObject, Signal, Slot

from helpers import createWidget, logger, uList

log = logger("main.ui.import")

class ImportUI(QObject):
    def __init__(self, store, parent = None):
        super(ImportUI, self).__init__(parent)

        self.store = store
        self.parent = parent
        self.ui = createWidget("ui/url-handler-modal.ui", parent)

        self.url = None
        self.ui.hide()

        self.ui.urlDialog.rejected.connect(lambda: self.ui.hide())
        self.ui.urlDialog.accepted.connect(self.add)

    def resize(self, width, height = None):
        if height:
            self.ui.resize(width, height)
        else:
            self.ui.resize(width)

    def display(self, url):
        self.url = url
        self.parent.raise_()
        self.parent.activateWindow()
        self.ui.urlText.setText(url)
        self.ui.show()
        log.debug("Show url modal %s", url)

    @Slot()
    def add(self):
        try:
            if self.url:
                url = self.url.replace(self.store.config.protocol + "://", "https://")

                log.info("Importing manifest url %s", url)
                mList = self.store.settings.get("manifestList")

                if not mList:
                    mList = uList()

                mList.push(url)
                self.store.settings.set("manifestList", mList)
                self.store.settings.commit()

                self.ui.hide()
        except Exception as e:
            log.error(e)
