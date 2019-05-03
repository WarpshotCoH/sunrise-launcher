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
    self.size = size
    self.check = check
    self.algo = Algos(algo)
    self.urls = urls

  @staticmethod
  def fromXML(file):
    return File(
      file.attrib.get("name", ""),
      file.attrib.get("size", ""),
      file.attrib.get("check", ""),
      # TODO: Fixme
      "md5",
      list(map(lambda e: e.text, file.findall(".//url")))
    )

class Launcher:
  def __init__(self, exec, params):
    self.exec = exec
    self.params = params

  @staticmethod
  def fromXML(launcher):
    return Launcher(
      launcher.attrib.get("exec", ""),
      launcher.attrib.get("params", ""),
    )

class Website:
  def __init__(self, type, address):
    self.type = type
    self.address = address

  @staticmethod
  def fromXML(website):
    return Website(
      website.attrib.get("type", ""),
      website.text,
    )

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
      "" if post.find("image") == None else post.find("image").text,
    )

class News:
  def __init__(self, posts):
    self.posts = posts

  @staticmethod
  def fromXML(news):
    return News(
      list(map(Post.fromXML, news.findall(".//post")))
    )

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
      server.attrib.get("auth", ""),
      server.attrib.get("db", "")
    )

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
    runtimes = list(map(
      Runtime.fromXML,
      manifest.findall(".//runtimes/runtime")
    ))
    
    return Manifest(name, servers, applications, runtimes)

def fromXML(file):
  return Manifest.fromXML(ET.parse(file).getroot())

# TODO: Implement me
def fromYML(file):
  return False

# TODO: Implement me
def fromJSON(file):
  return False