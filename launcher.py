import os
import subprocess
import sys
import threading

from PySide2.QtCore import QObject, QThread, Slot, Signal

class Launcher(QObject):
    started = Signal(str)
    exited = Signal(str)

    def __init__(self, store, parent = None):
        super(Launcher, self).__init__(parent)

        self.store = store

    def launchCmd(self, server):
        if server and server.application:
            app = self.store.applications.get(server.application)
        else:
            app = self.store.applications.get(id)

        if server and server.launcher and server.launcher.exec:
            ex = server.launcher.exec
        else:
            ex = app.launcher.exec

        runPath = os.path.abspath(os.path.join(self.store.settings.get("paths").binPath, app.runtime if app.runtime else app.id))

        cmd = os.path.join(runPath, ex)

        if app.launcher.params:
            cmd = cmd + " " + app.launcher.params

        if server and server.launcher and server.launcher.params:
            cmd = cmd + " " + server.launcher.params

        return (cmd, runPath)

    @Slot(str)
    def launch(self, id):
        print("Launching application" + id)
        print("Running")
        print(self.launchCmd(id))

        server = self.store.servers.get(id)

        if server:
            if server.id in self.store.settings.get("lockedServers"):
                # TODO: Require stored parental pin to be entered. On failure display dialog and short circuit
                True

            (cmd, path) = self.launchCmd(server)

            recentList = self.store.settings.get("recentServers")

            recentList.push(id)
            print("New recent list", recentList.recent)
            self.store.settings.set("recentServers", recentList)
            self.store.settings.commit()

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
            print(sys.exc_info())
            pass

        onExit()
        return

    thread = threading.Thread(target=runInThread,
                              args=(onExit, popenArgs, popenKWArgs))
    thread.start()

    return thread # returns immediately after the thread starts
