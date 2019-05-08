import os, errno
import subprocess

from PySide2.QtCore import QObject, QThread, Slot, Signal

class Launcher:
    def __init__(self):
        self.app = None

    def load(self, paths, application, runtime = None, server = None):
        self.app = application
        self.runtime = runtime
        self.server = server
        self.runPath = os.path.join(paths.binPath, self.runtime.id if runtime else self.app.id)

    def launchCmd(self):
        cmd = os.path.abspath(os.path.join('.', self.runPath, self.app.launcher.exec))

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
        print(self.launchCmd(), self.runPath)
        subprocess.Popen(self.launchCmd().split(' '), cwd=os.path.abspath(self.runPath))

    # TODO: Implement symlinked runner directory for actually launching the app at
    #       runtime. This is just a prototype and needs a lot of work
    # def buildRunner(self):
    #     if self.runtime:
    #         for file in self.runtime.files:
    #             self.createRunnerSymlink(self.runtime.id, file)

    #     for file in self.app.files:
    #         self.createRunnerSymlink(self.app.id, file)

    # def createRunnerSymlink(self, id, file):
    #     path = os.path.join(self.runPath, os.path.dirname(file.name))

    #     if not os.path.isdir(path):
    #         os.makedirs(path)

    #     src = os.path.abspath(os.path.join(self.paths.binPath, id, file.name))
    #     dst = os.path.abspath(os.path.join(self.runPath, file.name))

    #     try:
    #         os.symlink(src, dst)
    #     except OSError as e:
    #         if e.errno == errno.EEXIST:
    #             os.remove(dst)
    #             os.symlink(src, dst)
    #         else:
    #             raise e
