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
from PySide2.QtWidgets import QApplication, QMainWindow, QPushButton, QListWidget, QListWidgetItem

from detailsui import DetailsUI
from downloadui import DownloadUI
from serverlistui import ServerListUI
from servermanagerui import ServerManagerUI
from settingsui import SettingsUI
from launcher import Launcher
from patcher import PatcherPool
from state import Store

from manifest import fromXML

class Form(QObject):
    def __init__(self, ui_file, parent=None):
        super(Form, self).__init__(parent)

        # Init the download background thread
        self.downloadThread = QThread()

        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

if __name__ == "__main__":
    application = QApplication(sys.argv)

    mainForm = Form("sunrise.ui")
    settingsForm = Form("settings-dialog.ui")
    serverManagerForm = Form("server-manager.ui")

    # clear out the placeholder labels
    placeholdersToClear = [
        mainForm.window.progressLabel,
        mainForm.window.projectNameLabel,
        mainForm.window.projectPublisherLabel,
        mainForm.window.projectUptimeLabel
    ]
    for placeholder in placeholdersToClear:
        placeholder.setText("")

    store = Store()

    pool = PatcherPool()

    downloadUI = DownloadUI(
        store,
        mainForm.window.overallProgressBar,
        mainForm.window.fileProgressBar,
        mainForm.window.progressLabel,
        mainForm.window.playButton
    )

    detailsUI = DetailsUI(
        store,
        mainForm.window.projectNameLabel,
        mainForm.window.projectPublisherLabel,
        mainForm.window.projectUptimeLabel,
        mainForm.window.projectWebsiteButton,
        mainForm.window.projectIconLabel
    )

    serverListUI = ServerListUI(
        store,
        mainForm.window.projectsListWidget
    )

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

    # TODO: Move connections to store updates into the respective UI classes

    # Update the state store when a manifest update is received
    pool.updated.connect(store.load)

    # Connect the server list so that it updates when servers update
    store.updated.connect(serverListUI.reload)

    # Refresh the server manager list when manifests update
    store.updated.connect(serverListUI.reload)

    # Update the download and server details views when a server is selected
    serverListUI.selected.connect(detailsUI.load)
    serverListUI.selected.connect(downloadUI.load)

    # Connect the store to the launcher so a list of running applications
    # can be maintained
    launcher.started.connect(store.addRunning)
    launcher.exited.connect(store.removeRunning)

    # DownloadUI controls the main "Play" button. Connect its launch
    # event to the file launcher
    downloadUI.launch.connect(launcher.launch)

    # Load the default manifest files
    pool.add("manifests/manifest1.xml")
    pool.add("manifests/manifest2.xml")

    # bind button clicks
    mainForm.window.settingsButton.clicked.connect(settingsForm.window.show)
    mainForm.window.runtimesButton.clicked.connect(serverManagerUI.show)

    # things are ready, show the main window
    mainForm.window.show()

    application.aboutToQuit.connect(downloadUI.shutdown)
    application.aboutToQuit.connect(pool.shutdown)

    sys.exit(application.exec_())
