import webbrowser
import sys

import requests
from PySide2.QtCore import QObject, Signal, Slot
from PySide2.QtGui import QImage, QPixmap

from helpers import logger
from manifest import Server, Application, Runtime

log = logger("main.ui.details")

class DetailsUI(QObject):
    selected = Signal(Server, Application, Runtime)

    # TODO: Refactor to accept whole UI element
    def __init__(self, store, nameLabel, applicationLabel, runtimeLabel, uptimeLabel, websiteButton, icon, parent=None):
        super(DetailsUI, self).__init__(parent)

        self.store = store
        self.nameLabel = nameLabel
        self.applicationLabel = applicationLabel
        self.runtimeLabel = runtimeLabel
        self.uptimeLabel = uptimeLabel
        self.websiteButton = websiteButton
        self.icon = icon

    @Slot(Application, Runtime, Server)
    def load(self, application = None, runtime = None, server = None):
        if application:
            if len(application.websites) > 1:
                home = next(w for w in application.websites if w.type == "home")

                if home:
                    buttonUrl = home.address
                else:
                   buttonUrl = application.websites[0].address
            elif len(application.websites) == 1:
                buttonUrl = application.websites[0].address

            self.nameLabel.setText("")
            self.applicationLabel.setText("")
            self.runtimeLabel.setText("")

            if server and server.name:
                self.nameLabel.setText(server.name)

                if application.name:
                    self.applicationLabel.setText(application.name)

                if runtime.name:
                    self.runtimeLabel.setText(runtime.name)
            else:
                if application.name:
                    self.nameLabel.setText(application.name)


            # if application.publisher:
            #     self.publisherLabel.setText(application.publisher)

            # self.uptimeLabel.setText("Uptime Unknown") # TODO: handle this... servers will have to provide a query service, specified in the manifest?

            # TODO: How do we disconnect if we don't have apriori knowledge of connections
            try:
                self.websiteButton.clicked.disconnect()
            except Exception:
                pass

            # if buttonUrl:
                # self.websiteButton.clicked.connect(lambda: webbrowser.open(buttonUrl))

            try:
                # TODO: Move this off the ui thread. Should this be a on-off task or pooled to reuse resources
                if application.icon:
                    if not self.store.cache.get(application.icon):
                        projectIconData = requests.get(application.icon, stream=True, allow_redirects=True).content # TODO: handle 404/missing icon?
                        projectIconImage = QImage.fromData(projectIconData)
                        self.store.cache[application.icon] = QPixmap.fromImage(projectIconImage)

                    self.icon.setPixmap(self.store.cache.get(application.icon))
            except Exception:
                log.error(sys.exc_info())
                pass
