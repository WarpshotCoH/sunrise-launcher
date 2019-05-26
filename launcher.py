from os import makedirs, symlink
from os.path import join, abspath, normpath, basename, dirname, isdir, isfile
from shutil import rmtree
import subprocess
import sys
import threading

from PySide2.QtCore import QObject, QThread, Slot, Signal

from helpers import logger

log = logger("main.launcher")

class ServerArgs:
    def __init__(self, store, server):
        binPath = self.store.settings.get("paths").binPath
        absBin = abspath(binPath)

        application = self.store.applications.get(server.application)

        if application and application.runtime:
            runtime = self.store.runtimes.get(application.runtime)
        else:
            runtime = None

        self.APP_ID = application.id if application else None
        self.APP_VERSION = application.version if application else None
        self.RT_ID = runtime.id if runtime else ""
        self.APP_PATH = join(binPath, application.id) if application else ""
        self.RT_PATH = join(binPath, runtime.id) if runtime else ""
        self.APP_ABSPATH = join(absBin, application.id) if application else ""
        self.RT_ABSPATH = join(absBin, runtime.id) if runtime else ""

class ApplicationArgs:
    def __init__(self, store, application):
        binPath = self.store.settings.get("paths").binPath
        absBin = abspath(binPath)

        if application and application.runtime:
            runtime = self.store.runtimes.get(application.runtime)
        else:
            runtime = None

        self.APP_ID = application.id if application else None
        self.APP_VERSION = application.id if application else None
        self.RT_ID = application.id if application else None
        self.APP_PATH = join(binPath, application.id) if application else None
        self.RT_PATH = join(binPath, runtime.id) if runtime else None
        self.APP_ABSPATH = join(absBin, application.id) if application else ""
        self.RT_ABSPATH = join(absBin, runtim.id) if runtim else ""

class Link:
    def __init__(self, store):
        self.store = store

    def link(self, application):
        containers = [application]
        paths = self.store.settings.get("paths")

        if application.runtime:
            if self.store.runtimes.get(application.runtime):
                containers = [self.store.runtimes.get(application.runtime)] + containers

        if isdir(paths.runPath):
            rmtree(paths.runPath)

        for container in containers:
            log.info("Linking %s", container.id)

            for file in container.files:
                fileName = join(paths.runPath, file.name)
                filePath = join(paths.runPath, dirname(file.name))

                if not isdir(filePath):
                    makedirs(filePath)

                log.info("Link %s", file.name)
                symlink(abspath(join(paths.binPath, container.id, file.name)), fileName)

class Launcher(QObject):
    started = Signal(str)
    exited = Signal(str)

    def __init__(self, store, parent = None):
        super(Launcher, self).__init__(parent)

        self.store = store

    def getApplicationCmd(self, application):
        paths = self.store.settings.get("paths")
        path = paths.runPath if self.store.f("use_symlinks") else paths.binPath

        paths = self.store.settings.get("paths")

        if self.store.f("use_symlinks"):
            runPath = abspath(paths.runPath)
        else:
            runPath = abspath(join(paths.binPath, application.runtime if application.runtime else application.id))

        cmd = join(runPath, application.launcher.exec)

        if application.launcher.params:
            cmd = cmd + " " + application.launcher.params

        return (cmd, runPath)


    def getServerCmd(self, server):
        application = self.store.applications.get(server.application)

        if server and server.launcher and server.launcher.exec:
            ex = server.launcher.exec
        else:
            ex = application.launcher.exec

        ex = "homecoming.exe"

        paths = self.store.settings.get("paths")

        if self.store.f("use_symlinks"):
            runPath = abspath(paths.runPath)
        else:
            runPath = abspath(join(paths.binPath, application.runtime if application.runtime else application.id))

        cmd = join(runPath, ex)

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

                if self.store.f("use_symlinks"):
                    link = Link(self.store)
                    link.link(self.store.applications.get(server.application))

                log.debug("Run command: %s %s", cmd, path)
                popenAndCall(lambda: self.started.emit(id), lambda: self.exited.emit(id), cmd.split(" "), cwd=path)

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
