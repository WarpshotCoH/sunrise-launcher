from PySide2.QtCore import Slot

from helpers import InstallState, isInstalled, logger
from listviewui import ListViewUI
from manifest import Server, Application, Runtime

log = logger("main.ui.gamelist")

def installMsg(store, state):
    if state == InstallState.NOTINSTALLED:
        return store.s("GAMES_LIST_NOT_INSTALLED")
    if state == InstallState.INSTALLED:
        return store.s("GAMES_LIST_INSTALLED")
    if state == InstallState.UPDATEAVAILABLE:
        return store.s("GAMES_LIST_UPDATE_AVAILABLE")
    if state == InstallState.UPDATING:
        return store.s("GAMES_LIST_UPDATING")

    return ""

class GameListUI(ListViewUI):
    def __init__(self, store, parent):
        super(GameListUI, self).__init__(store, parent)

        self.header.hide()
        self.list.currentRowChanged.connect(self.selectItem)
        self.currentSelectedContainerId = None
        self.offsets = [[0, 0], [0, 0], [0, 0]]

    @Slot(int)
    def selectItem(self, row):
        log.debug("Offsets %s", self.offsets)
        if row > -1:
            for i, group in enumerate(self.offsets):
                if group[0] <= row and row <= group[1]:
                    index = row - group[0]
                    log.debug("Selected games index %s", index)

                    if i == 0:
                        tools = self.store.getTools()
                        tool = tools[index]

                        if tool:
                            runtime = self.store.runtimes.get(tool.runtime)

                            if runtime:
                                self.selected.emit(tool, runtime, None)
                                self.currentSelectedContainerId = tool.id
                                return
                    elif i == 1:
                        clients = self.store.getClients()
                        client = clients[index]

                        if client:
                            runtime = self.store.runtimes.get(client.runtime)

                            if runtime:
                                self.selected.emit(client, runtime, None)
                                self.currentSelectedContainerId = client.id
                                return
                    elif i == 2:
                        runtime = list(self.store.runtimes.values())[index]

                        if runtime:
                            self.selected.emit(None, runtime, None)
                            self.currentSelectedContainerId = runtime.id
                            return

        log.info("Empty selection from games list")

        # Fall through to none case
        self.selected.emit(None, None, None)

    @Slot(str)
    def reload(self, key = None):
        log.debug("Reload games list")

        try:
            self.list.currentRowChanged.disconnect()
        except Exception:
            pass

        self.list.clear()

        reselectIndex = -1
        log.debug("%s should be reselected after reload", self.currentSelectedContainerId)

        mods = self.store.getTools()
        clients = self.store.getClients()

        self.addHeader(self.store.s("GAMES_LIST_MODS_TOOLS"))
        for i, mod in enumerate(mods):
            if mod.id == self.currentSelectedContainerId:
                reselectIndex = self.list.count()

            installState = isInstalled(self.store, mod.id)
            self.addListItem(mod.id, mod.name, installMsg(self.store, installState))

        self.offsets[0] = (1, len(mods))

        self.addHeader(self.store.s("GAMES_LIST_CLIENTS"))
        for i, client in enumerate(clients):
            if client.id == self.currentSelectedContainerId:
                reselectIndex = self.list.count()

            installState = isInstalled(self.store, client.id)
            self.addListItem(client.id, client.name, installMsg(self.store, installState))

        self.offsets[1] = (self.offsets[0][1] + 2, self.offsets[0][1] + 1 + len(clients))

        self.addHeader(self.store.s("GAMES_LIST_RUNTIMES"))
        for i, runtime in enumerate(self.store.runtimes.values()):
            if runtime.id == self.currentSelectedContainerId:
                reselectIndex = self.list.count()

            installState = isInstalled(self.store, runtime.id)
            self.addListItem(runtime.id, runtime.name, installMsg(self.store, installState))

        self.offsets[2] = (self.offsets[1][1] + 2, self.offsets[1][1] + 1 + len(self.store.runtimes))

        self.list.currentRowChanged.connect(self.selectItem)

        log.debug("Reselecting index %s", reselectIndex)
        self.list.setCurrentRow(reselectIndex)
