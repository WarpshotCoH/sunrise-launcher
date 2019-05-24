from PySide2.QtCore import Slot

from helpers import isInstalled, logger
from listviewui import ListViewUI
from manifest import Server, Application, Runtime

log = logger("main.ui.gamelist")

class GameListUI(ListViewUI):
    def __init__(self, store, parent):
        super(GameListUI, self).__init__(store, parent)

        self.header.hide()
        self.list.currentRowChanged.connect(self.selectItem)
        self.offsets = [[0, 0], [0, 0], [0, 0]]

    @Slot(int)
    def selectItem(self, row):
        log.info("Offsets %s", self.offsets)
        if row > -1:
            for i, group in enumerate(self.offsets):
                if group[0] <= row and row <= group[1]:
                    index = row - group[0]
                    log.info("Selected games index %s", index)

                    if i == 0:
                        tools = self.store.getTools()
                        tool = tools[index]

                        if tool:
                            runtime = self.store.runtimes.get(tool.runtime)

                            if runtime:
                                self.selected.emit(tool, runtime, None)
                                return
                    elif i == 1:
                        clients = self.store.getClients()
                        client = clients[index]

                        if client:
                            runtime = self.store.runtimes.get(client.runtime)

                            if runtime:
                                self.selected.emit(client, runtime, None)
                                return
                    elif i == 2:
                        runtime = list(self.store.runtimes.values())[index]

                        if runtime:
                            self.selected.emit(None, runtime, None)
                            return

        # Fall through to none case
        self.selected.emit(None, None, None)

    @Slot(str)
    def reload(self, key = None):
        log.debug("Reload games list")

        self.list.clear()

        mods = self.store.getTools()
        clients = self.store.getClients()

        self.addHeader(self.store.s("GAMES_LIST_MODS_TOOLS"))
        for i, mod in enumerate(mods):
            self.addListItem(mod.name, self.store.s("GAMES_LIST_INSTALLED") if isInstalled(self.store, mod.id) else self.store.s("GAMES_LIST_NOT_INSTALLED"))

        self.offsets[0] = (1, len(mods))

        self.addHeader(self.store.s("GAMES_LIST_CLIENTS"))
        for i, client in enumerate(clients):
            self.addListItem(client.name, self.store.s("GAMES_LIST_INSTALLED") if isInstalled(self.store, client.id) else self.store.s("GAMES_LIST_NOT_INSTALLED"))

        self.offsets[1] = (self.offsets[0][1] + 2, self.offsets[0][1] + 1 + len(clients))

        self.addHeader(self.store.s("GAMES_LIST_RUNTIMES"))
        for i, runtime in enumerate(self.store.runtimes.values()):
            self.addListItem(runtime.name, self.store.s("GAMES_LIST_INSTALLED") if isInstalled(self.store, runtime.id) else self.store.s("GAMES_LIST_NOT_INSTALLED"))

        self.offsets[2] = (self.offsets[1][1] + 2, self.offsets[1][1] + 1 + len(self.store.runtimes))
