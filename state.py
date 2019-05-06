from manifest import fromXML

# Storage of metadata about the users current install
class Store():
    def __init__(self):
        self.applications = []
        self.runtimes = {}
        self.servers = []
        self.cache = {}

    def load(self, manifestFile):
        manifest = fromXMLpyh(manifestFile)

        self.applications = list(set().union(self.applications, manifest.applications))
        self.runtimes.update(manifest.runtimes)
        self.servers = list(set().union(self.servers, manifest.servers))
