import os

def isInstalled(store, id):
    installPath = store.settings.get("paths").binPath
    path = os.path.normpath(os.path.join(installPath, id))

    return os.path.isdir(path)
