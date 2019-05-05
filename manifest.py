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

class Launcher:
    def __init__(self, exec, params):
        self.exec = exec
        self.params = params

    @staticmethod
    def fromXML(launcher):
        return Launcher(
            launcher.attrib.get("exec", ""),
            launcher.attrib.get("params", None)
        )

    def toXML(self):
        launcher = ET.Element("launcher")
        launcher.attrib["exec"] = self.exec
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
    def __init__(self, id, runtime, custom, name, publisher, icon, websites, launcher, news, files):
        self.id = id
        self.runtime = runtime
        self.custom = custom
        self.name = name
        self.publisher = publisher
        self.icon = icon
        self.websites = websites
        self.launcher = launcher
        self.news = news
        self.files = files

    @staticmethod
    def fromXML(app):
        return Application(
            app.attrib["id"],
            app.attrib["runtime"],
            app.attrib.get("custom-server", False) == "true",
            "" if app.find("name") == None else app.find("name").text,
            "" if app.find("publisher") == None else app.find("publisher").text,
            "" if app.find("icon") == None else app.find("icon").text,
            list(map(Website.fromXML, app.findall(".//website"))),
            # TODO: How can this be written cleaner? it looks pretty verbose
            None if app.find("launcher") == None else Launcher.fromXML(app.find("launcher")),
            None if app.find("news") == None else News.fromXML(app.find("news")),
            list(map(File.fromXML, app.findall(".//files/file")))
        )

    def toXML(self):
        application = ET.Element("application")

        application.attrib["id"] = self.id
        application.attrib["runtime"] = self.runtime

        if self.custom:
            application.attrib["custom-server"] = "true"

        if self.name:
            ET.SubElement(application, "name").text = self.name

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

        application.append(files)

        return application

class Server:
    def __init__(self, name, application, auth, db):
        self.name = name
        self.application = application
        self.auth = auth
        self.db = db

    @staticmethod
    def fromXML(server):
        return Server(
            server.attrib.get("name", ""),
            server.attrib.get("application", ""),
            server.attrib.get("auth"),
            server.attrib.get("db")
        )

    def toXML(self):
        server = ET.Element("server")
        server.attrib["name"] = self.name
        server.attrib["application"] = self.application

        if self.auth:
            server.attrib["auth"] = self.auth

        if self.db:
            server.attrib["db"] = self.db

        return server

class Runtime:
    def __init__(self, id, name, publisher, files):
        self.id = id
        self.name = name
        self.publisher = publisher
        self.files = files

    @staticmethod
    def fromXML(runtime):
        return Runtime(
            runtime.attrib.get("id", ""),
            "" if runtime.find("name") == None else runtime.find("name").text,
            "" if runtime.find("publisher") == None else runtime.find("publisher").text,
            list(map(File.fromXML, runtime.findall(".//files/file")))
        )

    def toXML(self):
        runtime = ET.Element("runtime")
        runtime.attrib["name"] = self.name
        runtime.attrib["publisher"] = self.publisher

        files = ET.Element("files")
        for f in map(lambda f: f.toXML(), self.files):
            files.append(f)

        runtime.append(files)

        return runtime

class Manifest:
    def __init__(self, name, servers, applications, runtimes):
        self.name = name
        self.servers = servers
        self.applications = applications
        self.runtimes = runtimes

    @staticmethod
    def fromXML(manifest):
        name = manifest.find("name").text
        servers = list(map(
            Server.fromXML,
            manifest.findall(".//servers/server")
        ))
        applications = list(map(
            Application.fromXML,
            manifest.findall(".//applications/application")
        ))
        runtimeList = list(map(
            Runtime.fromXML,
            manifest.findall(".//runtimes/runtime")
        ))

        runtimes = dict((runtime.id,runtime) for runtime in runtimeList)

        return Manifest(name, servers, applications, runtimes)

    def toXML(self):
        manifest = ET.Element("sunrise-manifest")
        manifest.attrib["version"] = "1.0"

        ET.SubElement(manifest, "name").text = self.name

        if self.runtimes:
            servers = ET.SubElement(manifest, "servers")

            for server in map(lambda s: s.toXML(), self.servers):
                servers.append(server)

        if self.runtimes:
            applications = ET.SubElement(manifest, "applications")

            for application in map(lambda s: s.toXML(), self.applications):
                applications.append(application)

        if self.runtimes:
            runtimes = ET.SubElement(manifest, "runtimes")

            for runtime in map(lambda r: r.toXML(), self.runtimes.values()):
                runtimes.append(runtime)

        return manifest

def fromXML(file):
    return Manifest.fromXML(ET.parse(file).getroot())

# TODO: Implement me
def fromYML(file):
    return False

# TODO: Implement me
def fromJSON(file):
    return False
