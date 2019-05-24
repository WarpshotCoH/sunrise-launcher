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
from PySide2.QtWidgets import QWidget, QApplication, QProgressBar, QMainWindow, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem

from detailsui import DetailsUI
from downloadui import DownloadUI
from gamelistui import GameListUI
from headerui import HeaderUI
from helpers import createWidget
from serverlistui import ServerListUI
from settingsui import SettingsUI

from launcher import Launcher
from manifestpool import ManifestPool
from patcher import Patcher
from state import Store
from watcher import WatcherPool

from manifest import fromXML

@Slot(int)
def selectPage(index):
    for page in pages:
        page.hide()

    pages[index].show()

if __name__ == "__main__":
    QThread.currentThread().setObjectName("Main")
    application = QApplication(sys.argv)

    # Construct the main ui window
    window = createWidget("ui/sunrise-v3.ui")

    # Boot the initial data store
    store = Store()

    # Initialize the global UI elements
    headerUI = HeaderUI(window.gridLayout)

    # Initialize the main pages
    serverListUI = ServerListUI(store, window.gridLayout)
    gameListUI = GameListUI(store, window.gridLayout)
    settingsUI = SettingsUI(store, window.gridLayout)

    pages = [serverListUI, gameListUI, settingsUI]

    # Show the first page by default
    selectPage(0)

    # Initialize background data fetching pools
    autoPatchPool = None

    pool = ManifestPool(store)

    if store.settings.get("autoPatch"):
        autoPatchPool = WatcherPool()
        patcher = Patcher("https://url.to.the.patcher.endpoint/manifest.xml", autoPatchPool)

    # Initialize the application launcher
    launcher = Launcher(store)

    # Wire the inidivudal components together

    # Connect the main header buttons to their pages
    headerUI.itemSelected.connect(selectPage)

    # Update the state store when a manifest update is received
    pool.updated.connect(store.loadManifest)

    # Connect the store to the launcher so a list of running applications
    # can be maintained
    launcher.started.connect(store.addRunning)
    launcher.exited.connect(store.removeRunning)

    # Connect the list views to the launcher
    serverListUI.launch.connect(launcher.launch)
    gameListUI.launch.connect(launcher.launch)

    # Bind shutdown handlers for closing out background threads
    application.aboutToQuit.connect(serverListUI.shutdown)
    application.aboutToQuit.connect(gameListUI.shutdown)

    application.aboutToQuit.connect(pool.shutdown)

    if autoPatchPool:
        application.aboutToQuit.connect(autoPatchPool.shutdown)

    # Connect to theme selection
    # TODO: This requires a key existance check. User may have deleted the theme between runs
    store.settings.connectKey("theme", lambda _: store.themes[store.settings.get("theme")].activate(application))

    # Load any settings store for the user
    store.load()

    # pool.add("manifests/manifest1.xml")
    # pool.add("manifests/manifest2.xml")
    # pool.add("manifests/manifest3.xml")

    # Show the application
    window.show()

    sys.exit(application.exec_())
