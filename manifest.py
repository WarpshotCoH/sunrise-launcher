from enum import Enum
import hashlib
import xml.etree.ElementTree as ET

class Algos(Enum):
    MD5 = "md5"
    SHA512 = "sha512"

algoMap = {
    Algos.MD5: hashlib.md5,
    Algos.SHA512: hashlib.sha512
}

class Exclusion:
    def __init__(self, name):
        self.name = name

    @staticmethod
    def fromXML(exclusion):
        return Exclusion(
            exclusion.attrib["name"]
        )

    def toXML(self):
        exclusion = ET.Element("exclude")
        exclusion.attrib["name"] = self.name

        return exclusion

class File:
    def __init__(self, name, size, check, algo, urls):
        self.name = name
        self.size = int(size)
        self.check = check
        self.algo = Algos(algo)
        self.urls = urls

    @staticmethod
    def fromXML(file):
        algo = "sha512" if "sha512" in file.attrib else "md5"

        return File(
            file.attrib.get("name", ""),
            file.attrib.get("size", ""),
            file.attrib.get(algo, ""),
            algo,
            list(map(lambda e: e.text, file.findall(".//url")))
        )

    def toXML(self):
        file = ET.Element("file")
        file.attrib["name"] = self.name
        file.attrib["size"] = str(self.size)
        file.attrib[self.algo.value] = self.check

        for url in self.urls:
            ET.SubElement(file, "url").text = url

        return file

class Source:
    def __init__(self, tag, src):
        self.tag = tag
        self.src = src

    @staticmethod
    def fromXML(source):
        if source.tag == "torrent":
            return Source("torrent", source.attrib.get("magent"))
        else:
            return Source("http", source.attrib.get("url"))

    def toXML(self):
        tag = ET.Element(self.tag)

        if tag == "torrent":
            tag.attrib["magnet"] = self.src
        else:
            tag.attrib["url"] = self.src

        return tag

class Launcher:
    def __init__(self, exec , params):
        self.exec = exec
        self.params = params

    @staticmethod
    def fromXML(launcher):
        return Launcher(
            launcher.attrib.get("exec"),
            launcher.attrib.get("params")
        )

    def toXML(self):
        launcher = ET.Element("launcher")

        if self.exec:
            launcher.attrib["exec"] = self.exec

        if self.params:
            launcher.attrib["params"] = self.params

        return launcher

class Website:
    def __init__(self, type, address):
        self.type = type
        self.address = address

    @staticmethod
    def fromXML(website):
        return Website(
            website.attrib.get("type", ""),
            website.text
        )

    def toXML(self):
        website = ET.Element("website")
        website.attrib["type"] = self.type
        website.text = self.address

        return website

class Post:
    def __init__(self, date, title, url, image):
        self.date = date
        self.title = title
        self.url = url
        self.image = image

    @staticmethod
    def fromXML(post):
        return Post(
            post.attrib.get("date", ""),
            "" if post.find("title") == None else post.find("title").text,
            "" if post.find("url") == None else post.find("url").text,
            "" if post.find("image") == None else post.find("image").text
        )

    def toXML(self):
        post = ET.Element("post")
        post.attrib["date"] = self.date

        ET.SubElement(post, "title").text = self.title
        ET.SubElement(post, "url").text = self.url
        ET.SubElement(post, "image").text = self.image

        return post

class News:
    def __init__(self, posts):
        self.posts = posts

    @staticmethod
    def fromXML(news):
        return News(
            list(map(Post.fromXML, news.findall(".//post")))
        )

    def toXML(self):
        news = ET.Element("news")

        for post in map(lambda p: p.toXML(), self.posts):
            news.append(post)

        return news

class Application:
    def __init__(self, id, type, version, runtime, custom, name, publisher, icon, websites, launcher, news, files, sources, standalone, exclusions):
        self.id = id
        self.type = type
        self.ctype = "application"
        self.version = version
        self.runtime = runtime
        self.custom = custom
        self.name = name
        self.publisher = publisher
        self.icon = icon
        self.websites = websites
        self.launcher = launcher
        self.news = news
        self.files = files
        self.sources = sources
        self.standalone = standalone
        self.exclusions = exclusions

    def getExcludedFileNames(self):
        return list(map(lambda e: e.name, self.exclusions))

    @staticmethod
    def fromXML(app):
        return Application(
            app.attrib["id"],
            app.attrib["type"],
            None,
            app.attrib["runtime"],
            app.attrib.get("custom-server", False) == "true",
            "" if app.find("name") == None else app.find("name").text,
            "" if app.find("publisher") == None else app.find("publisher").text,
            "" if app.find("icon") == None else app.find("icon").text,
            list(map(Website.fromXML, app.findall(".//website"))),
            # TODO: How can this be written cleaner? it looks pretty verbose
            None if app.find("launcher") == None else Launcher.fromXML(app.find("launcher")),
            None if app.find("news") == None else News.fromXML(app.find("news")),
            list(map(File.fromXML, app.findall(".//files/file"))),
            list(map(Source.fromXML, app.findall(".//sources/*") if app.find("sources") else [])),
            app.attrib.get("standalone", False) == "true",
            list(map(Exclusion.fromXML, app.findall(".//files/exclude")))
        )

    def toXML(self):
        application = ET.Element("application")

        application.attrib["id"] = self.id
        application.attrib["type"] = self.type
        application.attrib["runtime"] = self.runtime

        if self.custom:
            application.attrib["custom-server"] = "true"

        if self.name:
            ET.SubElement(application, "name").text = self.name

        if self.version:
            ET.SubElement(application, "version").text = self.version

        if self.publisher:
            ET.SubElement(application, "publisher").text = self.publisher

        if self.icon:
            ET.SubElement(application, "icon").text = self.icon

        for website in map(lambda w: w.toXML(), self.websites):
            application.append(website)

        if self.launcher:
            application.append(self.launcher.toXML())

        if self.news:
            application.append(self.news.toXML())

        files = ET.Element("files")
        for f in map(lambda f: f.toXML(), self.files):
            files.append(f)
        for e in map(lambda e: e.toXML(), self.exclusions):
            files.append(e)

        application.append(files)

        sources = ET.Element("sources")
        for s in map(lambda s: s.toXML(), self.sources):
            sources.append(f)

        application.append(sources)

        return application

class Server:
    def __init__(self, id, application, name, publisher, icon, websites, launcher):
        self.id = id
        self.ctype = "Server"
        self.application = application
        self.name = name
        self.publisher = publisher
        self.icon = icon
        self.websites = websites
        self.launcher = launcher

    @staticmethod
    def fromXML(server):
        return Server(
            server.attrib.get("id"),
            server.attrib.get("application"),
            None if server.find("name") == None else server.find("name").text,
            None if server.find("publisher") == None else server.find("publisher").text,
            None if server.find("icon") == None else server.find("icon").text,
            list(map(Website.fromXML, server.findall(".//website"))),
            None if server.find("launcher") == None else Launcher.fromXML(server.find("launcher")),
        )

    def toXML(self):
        server = ET.Element("server")

        if self.id:
            server.attrib["id"] = self.id

        if self.application:
            server.attrib["application"] = self.application

        if self.name:
            ET.SubElement(server, "name").text = self.name

        if self.publisher:
            ET.SubElement(server, "publisher").text = self.publisher

        if self.icon:
            ET.SubElement(server, "icon").text = self.icon

        for website in map(lambda w: w.toXML(), self.websites):
            server.append(website)

        if self.launcher:
            server.append(self.launcher.toXML())

        return server

class Runtime:
    def __init__(self, id, name, publisher, icon, files, sources):
        self.id = id
        self.ctype = "runtime"
        self.name = name
        self.publisher = publisher
        self.icon = icon
        self.files = files
        self.sources = sources
        # TODO: Should this be implemented? Technically files blocks allows exclude, but we ignore them
        self.exclusions = []

    @staticmethod
    def fromXML(runtime):
        return Runtime(
            runtime.attrib.get("id", ""),
            "" if runtime.find("name") == None else runtime.find("name").text,
            "" if runtime.find("publisher") == None else runtime.find("publisher").text,
            None if runtime.find("icon") == None else runtime.find("icon").text,
            list(map(File.fromXML, runtime.findall(".//files/file"))),
            list(map(Source.fromXML, runtime.findall(".//sources/*") if runtime.find("sources") else [])),
        )

    def toXML(self):
        runtime = ET.Element("runtime")
        runtime.attrib["id"] = self.id

        ET.SubElement(runtime, "name").text = self.name
        ET.SubElement(runtime, "publisher").text = self.publisher

        if self.icon:
            ET.SubElement(runtime, "icon").text = self.icon

        files = ET.Element("files")
        for f in map(lambda f: f.toXML(), self.files):
            files.append(f)

        runtime.append(files)

        sources = ET.Element("sources")
        for s in map(lambda s: s.toXML(), self.sources):
            sources.append(f)

        runtime.append(sources)

        return runtime

class Manifest:
    def __init__(self, name, servers, applications, runtimes, source):
        self.name = name
        self.servers = servers
        self.applications = applications
        self.runtimes = runtimes
        self.source = source

    @staticmethod
    def fromXML(manifest, source):
        name = manifest.find("name").text
        serverList = list(map(
            Server.fromXML,
            manifest.findall(".//servers/server")
        ))
        applicationList = list(map(
            Application.fromXML,
            manifest.findall(".//applications/application")
        ))
        runtimeList = list(map(
            Runtime.fromXML,
            manifest.findall(".//runtimes/runtime")
        ))

        servers = dict((server.id,server) for server in serverList)
        applications = dict((application.id,application) for application in applicationList)
        runtimes = dict((runtime.id,runtime) for runtime in runtimeList)

        return Manifest(name, servers, applications, runtimes, source)

    def toXML(self):
        manifest = ET.Element("sunrise-manifest")
        manifest.attrib["version"] = "1.0"

        ET.SubElement(manifest, "name").text = self.name

        if self.servers:
            servers = ET.SubElement(manifest, "servers")

            for server in map(lambda s: s.toXML(), self.servers.values()):
                servers.append(server)

        if self.applications:
            applications = ET.SubElement(manifest, "applications")

            for application in map(lambda r: r.toXML(), self.applications.values()):
                applications.append(application)

        if self.runtimes:
            runtimes = ET.SubElement(manifest, "runtimes")

            for runtime in map(lambda r: r.toXML(), self.runtimes.values()):
                runtimes.append(runtime)

        return manifest

def fromXML(file, url):
    return Manifest.fromXML(ET.parse(file).getroot(), url)

def fromXMLString(file, url):
    return Manifest.fromXML(ET.fromstring(file), url)

# TODO: Implement me
def fromYML(file):
    return False

# TODO: Implement me
def fromJSON(file):
    return False
