from os import makedirs, symlink, link
from os.path import join, abspath, normpath, basename, dirname, isdir, isfile
from shutil import rmtree
import platform
import subprocess
import sys
import threading

from PySide2.QtCore import QObject, QThread, Slot, Signal

from helpers import logger

log = logger("main.launcher")

class ServerArgs:
    def __init__(self, store, server):
        self.store = store

        binPath = ".."
        absBin = abspath(self.store.settings.get("paths").binPath)

        application = self.store.applications.get(server.application)

        if application and application.runtime:
            runtime = self.store.runtimes.get(application.runtime)
        else:
            runtime = None

        self.APP_ID = application.id if application else ""
        self.APP_VERSION = application.version if application and application.version else ""
        self.RT_ID = runtime.id if runtime else ""
        self.APP_PATH = join(binPath, application.id) if application else ""
        self.RT_PATH = join(binPath, runtime.id) if runtime else ""
        self.APP_ABSPATH = join(absBin, application.id) if application else ""
        self.RT_ABSPATH = join(absBin, runtime.id) if runtime else ""

class ApplicationArgs:
    def __init__(self, store, application):
        self.store = store

        binPath = ".."
        absBin = abspath(self.store.settings.get("paths").binPath)

        if application and application.runtime:
            runtime = self.store.runtimes.get(application.runtime)
        else:
            runtime = None

        self.APP_ID = application.id if application else ""
        self.APP_VERSION = application.version if application and application.version else ""
        self.RT_ID = application.id if application else ""
        self.APP_PATH = join(binPath, application.id) if application else ""
        self.RT_PATH = join(binPath, runtime.id) if runtime else ""
        self.APP_ABSPATH = join(absBin, application.id) if application else ""
        self.RT_ABSPATH = join(absBin, runtime.id) if runtime else ""

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

                log.info("Link %s %s", abspath(fileName), abspath(join(paths.binPath, container.id, file.name)))
                link(abspath(join(paths.binPath, container.id, file.name)), abspath(fileName))

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
            runPath = abspath(join(paths.binPath, application.id if application.standalone else application.runtime))

        cmd = []
        cmd.append(join(runPath, application.launcher.exec))

        if application.launcher.params:
            args = ApplicationArgs(self.store, application)
            cmd.append(self.parseParams(application.launcher.params, args))

        return (cmd, runPath)


    def getServerCmd(self, server):
        application = self.store.applications.get(server.application)

        if server and server.launcher and server.launcher.exec:
            ex = server.launcher.exec
        else:
            ex = application.launcher.exec

        paths = self.store.settings.get("paths")

        if self.store.f("use_symlinks"):
            runPath = abspath(paths.runPath)
        else:
            runPath = abspath(join(paths.binPath, application.id if application.standalone else application.runtime))

        cmd = []
        cmd.append(join(runPath, ex))

        if application.launcher.params:
            args = ApplicationArgs(self.store, application)
            cmd.append(self.parseParams(application.launcher.params, args))

        if server and server.launcher and server.launcher.params:
            args = ServerArgs(self.store, server)
            cmd.append(self.parseParams(server.launcher.params, args))

        return (cmd, runPath)

    def parseParams(self, params, args):
        log.debug("Parsing/replacing parameters")
        log.debug("Old params: %s", params)

        params = params.replace("$APP_ID", args.APP_ID)
        params = params.replace("$APP_VERSION", args.APP_VERSION)
        params = params.replace("$RT_ID", args.RT_ID)
        params = params.replace("$APP_PATH", args.APP_PATH)
        params = params.replace("$RT_PATH", args.RT_PATH)
        params = params.replace("$APP_ABSPATH", args.APP_ABSPATH)
        params = params.replace("$RT_ABSPATH", args.RT_ABSPATH)

        log.debug("New params: %s", params)

        return params

    def launchCmd(self, id):
        server = self.store.servers.get(id)

        if server:
            return self.getServerCmd(server)

        application = self.store.applications.get(id)

        if application:
            return self.getApplicationCmd(application)

        return (None, None)

    def addWineArgs(self, cmd):
        cmd.insert(0, "wine")
        return cmd

    @Slot(str)
    def launch(self, id):
        log.info("Launching application %s", id)

        (cmd, path) = self.launchCmd(id)

        if cmd:
            # TODO: Replace this with proper app-wide platform detection.
            # This is more just a quick hack so we can test launching functions without booting into a different OS.
            if (platform.system != "Windows"):
                log.info("Running with Wine")
                cmd = self.addWineArgs(cmd)

            server = self.store.servers.get(id)

            if server:
                # recentList = self.store.settings.get("recentServers")
                # recentList.push(id)
                # log.info("New recent list %s", recentList.recent)
                # self.store.settings.set("recentServers", recentList)
                # self.store.settings.commit()

                if self.store.f("use_symlinks"):
                    link = Link(self.store)
                    link.link(self.store.applications.get(server.application))

            log.info("Using base path: %s", path)
            log.info("Running command: %s", cmd)
            popenAndCall(lambda: self.started.emit(id), lambda: self.exited.emit(id), cmd, cwd=path)

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
