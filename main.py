import hashlib
import math
import os, os.path
import posixpath
import random
import requests
import struct
import sys
import time
import urllib.request as request
import urllib.parse
import webbrowser
import xml.etree.ElementTree as ET
from PySide2.QtCore import QByteArray, QFile, QObject, QUrl, QThread, Signal, Slot
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtWidgets import QApplication, QProgressBar, QMainWindow, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem

from detailsui import DetailsUI
from downloadui import DownloadUI
from gamelistui import GameListUI
from headerui import HeaderUI
from serverlistui import ServerListUI
from servermanagerui import ServerManagerUI
from settingsui import SettingsUI

from launcher import Launcher
from patcher import Patcher
from state import Store
from watcher import WatcherPool

from manifest import fromXML

class Form(QObject):
    def __init__(self, ui_file, parent=None):
        super(Form, self).__init__(parent)

        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

@Slot(int)
def switchSection(to):
    # TODO: Clear selections and default to initial selections

    if to == 2: # Settings
        serverListUI.hide()
        serverListUI.clear()
        gameListUI.hide()
        serverListUI.clear()

    elif to == 1: # Games
        serverListUI.hide()
        serverListUI.clear()

        gameListUI.show()
    else: # Servers
        gameListUI.hide()
        gameListUI.clear()

        serverListUI.show()

if __name__ == "__main__":
    application = QApplication(sys.argv)

    mainForm = Form("sunrise-v3.ui")

    # mainForm = Form("sunrise.ui")
    settingsForm = Form("settings-dialog.ui")
    serverManagerForm = Form("server-manager.ui")

    detailsLayout = mainForm.window.detailsLayout
    detailsHeader = detailsLayout.itemAt(0)
    detailsHeaderText = detailsLayout.itemAt(0).itemAt(1)
    detailsContent = detailsLayout.itemAt(2)
    downloadLayout = detailsLayout.itemAt(1).itemAt(0).widget()

    patcher = None

    store = Store()

    pool = WatcherPool()

    if store.settings.get("autoPatch"):
        autoPatchPool = WatcherPool()
        patcher = Patcher("https://url.to.the.patcher.endpoint/manifest.xml", autoPatchPool)

    headerUI = HeaderUI(
        mainForm.window.headerWrapper.itemAt(0).widget()
    )

    headerUI.itemSelected.connect(switchSection)

    downloadUI = DownloadUI(
        store,
        downloadLayout.findChild(QProgressBar, "progress"),
        downloadLayout.findChild(QProgressBar, "fileProgress"),
        downloadLayout.findChild(QPushButton, "play"),
    )

    detailsUI = DetailsUI(
        store,
        detailsHeaderText.itemAt(0).widget(),
        detailsHeaderText.itemAt(1).widget(),
        detailsHeaderText.itemAt(2).widget(),
        None,
        detailsHeader.itemAt(1).widget(),
        detailsHeader.itemAt(0).widget()
    )

    # TODO: Someone with more experience than me should implement these correctly
    #       as a custom widget
    serverListUI = ServerListUI(
        store,
        "serverlist.ui"
    )
    mainForm.window.serverListLayout.addWidget(serverListUI.ui)

    # TODO: Someone with more experience than me should implement these correctly
    #       as a custom widget
    gameListUI = GameListUI(
        store,
        "list.ui"
    )
    mainForm.window.serverListLayout.addWidget(gameListUI.ui)

    serverManagerUI = ServerManagerUI(
        store,
        serverManagerForm.window
    )

    settingsUI = SettingsUI(
        store,
        settingsForm.window.label,
        settingsForm.window.pushButton
    )

    launcher = Launcher(store)

    if store.theme:
        application.setStyleSheet(store.theme.css)

    # TODO: Move connections to store updates into the respective UI classes

    # Update the state store when a manifest update is received
    pool.updated.connect(store.loadManifest)

    # Update the download and server details views when an item is selected
    serverListUI.selected.connect(detailsUI.load)
    serverListUI.selected.connect(downloadUI.load)
    gameListUI.selected.connect(detailsUI.load)
    gameListUI.selected.connect(downloadUI.load)

    # Connect the store to the launcher so a list of running applications
    # can be maintained
    launcher.started.connect(store.addRunning)
    launcher.exited.connect(store.removeRunning)

    # DownloadUI controls the main "Play" button. Connect its launch
    # event to the file launcher
    downloadUI.launch.connect(launcher.launch)

    # bind button clicks
    # mainForm.window.settingsButton.clicked.connect(settingsForm.window.show)
    # mainForm.window.runtimesButton.clicked.connect(serverManagerUI.show)

    application.aboutToQuit.connect(downloadUI.shutdown)
    application.aboutToQuit.connect(pool.shutdown)

    if patcher:
        application.aboutToQuit.connect(patcher.shutdown)

    switchSection(0)

    # things are ready, show the main window
    mainForm.window.show()

    # Load the default manifest files
    # pool.add("manifests/manifest1.xml")
    # pool.add("manifests/manifest2.xml")
    # pool.add("manifests/manifest3.xml")

    store.load()

    store.save()

    sys.exit(application.exec_())
