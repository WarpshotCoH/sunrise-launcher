import os
import subprocess
import sys
import threading

from PySide2.QtCore import QObject, QThread, Slot, Signal

from helpers import logger

log = logger("main.launcher")

class Launcher(QObject):
    started = Signal(str)
    exited = Signal(str)

    def __init__(self, store, parent = None):
        super(Launcher, self).__init__(parent)

        self.store = store

    def getApplicationCmd(self, application):
        runPath = os.path.abspath(os.path.join(self.store.settings.get("paths").binPath, application.runtime if application.runtime else application.id))

        cmd = os.path.join(runPath, application.launcher.exec)

        if application.launcher.params:
            cmd = cmd + " " + application.launcher.params

        return (cmd, runPath)


    def getServerCmd(self, server):
        application = self.store.applications.get(server.application)

        if server and server.launcher and server.launcher.exec:
            ex = server.launcher.exec
        else:
            ex = application.launcher.exec

        runPath = os.path.abspath(os.path.join(self.store.settings.get("paths").binPath, application.runtime if application.runtime else application.id))

        cmd = os.path.join(runPath, ex)

        if application.launcher.params:
            cmd = cmd + " " + application.launcher.params

        if server and server.launcher and server.launcher.params:
            cmd = cmd + " " + server.launcher.params

        return (cmd, runPath)

    def launchCmd(self, id):
        server = self.store.servers.get(id)

        if server:
            return self.getServerCmd(server)

        application = self.store.applications.get(id)

        if application:
            return self.getApplicationCmd(application)

        return (None, None)

    @Slot(str)
    def launch(self, id):
        log.info("Launching application %s", id)

        (cmd, path) = self.launchCmd(id)

        if cmd:
            server = self.store.servers.get(id)

            if server:
                recentList = self.store.settings.get("recentServers")
                recentList.push(id)
                log.info("New recent list %s", recentList.recent)
                self.store.settings.set("recentServers", recentList)
                self.store.settings.commit()

            log.debug("Run command: %s %s", cmd, path)
            # popenAndCall(lambda: self.started.emit(id), lambda: self.exited.emit(id), cmd.split(" "), cwd=path)

# https://stackoverflow.com/questions/2581817/python-subprocess-callback-when-cmd-exits
def popenAndCall(onStart, onExit, *popenArgs, **popenKWArgs):
    """
    Runs a subprocess.Popen, and then calls the function onExit when the
    subprocess completes.

    Use it exactly the way you'd normally use subprocess.Popen, except include a
    callable to execute as the first argument. onExit is a callable object, and
    *popenArgs and **popenKWArgs are simply passed up to subprocess.Popen.
    """
    def runInThread(onExit, popenArgs, popenKWArgs):
        onStart()
        try:
            proc = subprocess.Popen(*popenArgs, **popenKWArgs)
            proc.wait()
        except Exception:
            log.error(sys.exc_info())
            pass

        onExit()
        return

    thread = threading.Thread(target=runInThread,
                              args=(onExit, popenArgs, popenKWArgs))
    thread.start()

    return thread # returns immediately after the thread starts
