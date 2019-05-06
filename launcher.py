import os
import subprocess

from PySide2.QtCore import QObject, QThread, Slot, Signal

class Launcher:
    def __init__(self):
        self.app = None

    def load(self, application, installPath, server = None):
        self.app = application
        self.installPath = installPath
        self.server = server

    def launchCmd(self):
        cmd = os.path.join(self.installPath, self.app.launcher.exec)

        if self.app.launcher.params:
            cmd = cmd + " " + self.app.launcher.params

        if self.server:
            if self.server.auth:
                cmd = cmd + " -auth " + self.server.auth

            if self.server.db:
                cmd = cmd + " -db " + self.server.db

        return cmd

    @Slot()
    def launch(self):
        print("Launching application " + self.app.name)
        print("Running: ")
        print(self.launchCmd())
        # subprocess.Popen(self.launchCmd().split(' '), cwd=self.installPath)

