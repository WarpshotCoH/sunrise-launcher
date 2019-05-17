from PySide2.QtCore import Slot

from helpers import isInstalled
from listviewui import ListViewUI
from manifest import Server, Application, Runtime

class GameListUI(ListViewUI):
    def __init__(self, store, parent):
        super(GameListUI, self).__init__(store, parent)

        self.header.hide()
        self.list.currentRowChanged.connect(self.selectItem)
        self.offsets = [[0, 0], [0, 0], [0, 0]]

    @Slot(int)
    def selectItem(self, row):
        if row > -1:
            for i, group in enumerate(self.offsets):
                if group[0] <= row and row <= group[1]:
                    index = row - group[0]
                    print("Selected games index", index)

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
        else:
            self.selected.emit(None, None, None)

    @Slot(str)
    def reload(self, key = None):
        print("Reload games list")

        self.list.clear()

        mods = self.store.getTools()
        clients = self.store.getClients()

        self.addHeader("Mods / Tools")
        for i, mod in enumerate(mods):
            self.addListItem(mod.name, "Installed" if isInstalled(self.store, mod.id) else "Not Installed")
        self.offsets[0] = (1, 1 + len(mods))

        self.addHeader("Clients")
        for i, client in enumerate(clients):
            self.addListItem(client.name, "Installed" if isInstalled(self.store, client.id) else "Not Installed")
        self.offsets[1] = [self.offsets[0][1] + 1, self.offsets[0][1] + 1 + len(clients)]

        self.addHeader("Runtimes")
        for i, runtime in enumerate(self.store.runtimes.values()):
            self.addListItem(runtime.name, "Installed" if isInstalled(self.store, runtime.id) else "Not Installed")
        self.offsets[2] = [self.offsets[1][1] + 1, self.offsets[1][1] + 1 + len(self.store.runtimes)]
