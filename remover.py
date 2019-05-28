class Remover:
    def __init__(self, store):
        self.store = store

    def computeDependents(self, fileCheck):
        # TODO: Walk the runtimes ->> applications -> servers to find everyone
        #       that depends on this file, either directly or transitively
        return []

    def computeFilesToRemove(self, containerId):
        # TODO: Compute dep list for each file that containerId directly lists.
        #       Return the list of files that are only in use by containerId
        return []

    def uninstall(self, containerId):
        # TODO: Delete the files owned by containerId
        return True

    def canBeRemoved(self, containerId):
        # TODO: Check if this container can be removed. To be able to be
        #       removed, the container must only exist in the locally stored
        #       manifest and not be referenced by any remote file
        return True

    def remove(self, containerId):
        # TODO: Delete the files owned by containerId and remove the container
        #       from the internal store
        return True
