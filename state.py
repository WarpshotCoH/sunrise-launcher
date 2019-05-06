import xml.etree.ElementTree as ET
import sys

from manifest import fromXML, Manifest

# Storage of metadata about the users current install
class Store():
    def __init__(self):
        self.applications = {}
        self.runtimes = {}
        self.servers = []
        self.cache = {}

        try:
            stored = Manifest.fromXML(ET.parse("store/manifests.xml").getroot())
            self.applications = stored.applications
            self.runtimes = stored.runtimes
            self.servers = stored.servers

            print(self.runtimes)
        except Exception:
            print(sys.exc_info())
            pass

    def load(self, manifestFile):
        manifest = fromXML(manifestFile)

        self.applications.update(manifest.applications)
        self.runtimes.update(manifest.runtimes)
        self.servers = list(set().union(self.servers, manifest.servers))

    def resolveDownload(self, id):
        # TODO: Do we need to handle collisions between app and runtime ids
        requested = self.applications.get(id, self.runtimes.get(id))
        print("resolved", requested.id)

        if requested:
            if hasattr(requested, "runtime") and requested.runtime:
                return self.resolveDownload(requested.runtime) + [requested]
            else:
                return [requested]
        else:
            return []

    def save(self):
        m = Manifest("store", self.servers, self.applications, self.runtimes)
        output = ET.tostring(m.toXML(), encoding='utf8', method='xml')

        f = open("store/manifests.xml", "wb+")
        f.write(output)
        f.close()
