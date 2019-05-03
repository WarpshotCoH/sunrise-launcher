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

from downloadui import DownloadUI

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

def projectSelected():
    app = manifest.applications[mainForm.window.projectsListWidget.currentRow()]

    runtime = manifest.runtimes.get(app.runtime)
    downloadUI.load(runtime.files, './runtimes/' + runtime.id)

    if len(app.websites) > 1:
        home = next(w for w in app.websites if w.type == "home")

        if home:
            buttonUrl = home.address
        else:
           buttonUrl = app.websites[0].address
    elif len(app.websites) == 1:
        buttonUrl = app.websites[0].address

    if app.name:
        mainForm.window.projectNameLabel.setText(app.name)

    if app.publisher:
        mainForm.window.projectPublisherLabel.setText(app.publisher)

    mainForm.window.projectUptimeLabel.setText("Uptime Unknown") # TODO: handle this... servers will have to provide a query service, specified in the manifest?

    # TODO: How do we disconnect if we don't have apriori knowledge of connections
    try:
        mainForm.window.projectWebsiteButton.clicked.disconnect()
    except Exception:
        pass

    if buttonUrl:
        mainForm.window.projectWebsiteButton.clicked.connect(lambda: webbrowser.open(buttonUrl))

    try:
        if app.icon:
           projectIconData = requests.get(app.icon, stream=True, allow_redirects=True).content # TODO: handle 404/missing icon?
           projectIconImage = QImage.fromData(projectIconData)
           mainForm.window.projectIconLabel.setPixmap(QPixmap.fromImage(projectIconImage))
    except Exception:
        pass

    print("Selected Project: %s" % app.id)

if __name__ == "__main__":
    application = QApplication(sys.argv)

    mainForm = Form("sunrise.ui")
    settingsForm = Form("settings-dialog.ui")
    #runtimesForm = Form("runtimes-dialog.ui")

    downloadUI = DownloadUI(
        mainForm.window.overallProgressBar,
        mainForm.window.fileProgressBar,
        mainForm.window.progressLabel,
        mainForm.window.playButton
    )

    # clear out the placeholder labels
    placeholdersToClear = [
        mainForm.window.progressLabel,
        mainForm.window.projectNameLabel,
        mainForm.window.projectPublisherLabel,
        mainForm.window.projectUptimeLabel
    ]
    for placeholder in placeholdersToClear:
        placeholder.setText("")

    manifest = fromXML("manifest.xml")

    for app in manifest.applications:
        QListWidgetItem(app.name, mainForm.window.projectsListWidget)

    mainForm.window.projectsListWidget.setCurrentRow(0)
    projectSelected()

    mainForm.window.projectsListWidget.itemSelectionChanged.connect(projectSelected)

    # bind button clicks
    mainForm.window.settingsButton.clicked.connect(settingsForm.window.show)
    # mainForm.window.runtimesButton.clicked.connect(runtimesForm.window.show)

    # things are ready, show the main window
    mainForm.window.show()

    application.aboutToQuit.connect(downloadUI.shutdown)

    sys.exit(application.exec_())
