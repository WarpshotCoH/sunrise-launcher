import os
import subprocess

from PySide2.QtCore import QObject, QThread, Slot, Signal

class Launcher:
    def __init__(self):
        self.app = None

    def load(self, application, installPath, runtime = None, server = None):
        self.app = application
        self.installPath = installPath
        self.runtime = runtime
        self.server = server

    def buildRunner(self):
        if self.runtime:
            for file in self.runtime.files:
                self.createRunnerSymlink(file)

        for file in self.app.files:
            self.createRunnerSymlink(file)

    def createRunnerSymlink(self, file):
        path = os.path.join('./run', self.app.id, os.path.dirname(file.name))

        if not os.path.isdir(path):
            os.makedirs(path)

        os.symlink(
            os.path.join(self.installPath, file.name),
            os.path.join('./run', self.app.id, file.name)
        )

    def launchCmd(self):
        self.buildRunner()

        cmd = os.path.join('./run', self.app.id, self.app.launcher.exec)

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

