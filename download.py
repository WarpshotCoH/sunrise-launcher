import hashlib
import math
import os
import posixpath
import random
import sys
import time
import urllib.request as request
import urllib.parse

import requests

from manifest import algoMap

# TODO: Refactor to take a File from manifest and a writePath as constructor args
class FileDownload():
  def __init__(self, writePath, urls, name, size, check, algo):
    self.path = writePath
    self.urls = urls
    self.name = name
    self.size = size
    self.check = check
    self.algo = algoMap[algo]
    self.interrupt = False

  def start(self, init, progress):
    print("Start file download")
    urlNumToTry = random.randint(0, len(self.urls) - 1)
    downloaded = False
    tries = 0

    while (not downloaded and tries < len(self.urls)):

      # Allow downloads to be interrupted
      if self.interrupt:
        return downloaded

      print(downloaded, urlNumToTry, tries, self.urls[urlNumToTry])
      if (tries > len(self.urls) - 1):
        print("Ran out of tries")
        return downloaded
      url = self.urls[urlNumToTry]
      downloaded = self.downloadUrl(url, init, progress)
      urlNumToTry += 1
      if (urlNumToTry > len(self.urls) - 1):
        urlNumToTry = 0
      tries += 1

    return downloaded

  def downloadUrl(self, url, init, progress):
    print("Start url download", url)

    complete = False

    try:
      r = requests.get(url, stream=True)

      remoteFilename = posixpath.basename(urllib.parse.urlparse(url).path)
      # TODO: Handle Transfer-Encoding: chunked; unable to know the remote filesize there.
      remoteFilesize = int(r.headers['Content-Length'])

      init.emit(0, 0, remoteFilesize, remoteFilename)

      print("Downloading %s from: %s" % (remoteFilename, url))

      fileProgress = 0

      with r:
        r.raise_for_status()
        with open(self.path, 'wb') as f:
          for chunk in r.iter_content(chunk_size=8192):
            # Allow downloads to be interrupted
            if self.interrupt:
              return complete

            if chunk: # filter out keep-alive new chunks
              f.write(chunk)
              fileProgress += len(chunk)
              progress.emit(fileProgress)
              # f.flush()
      if (os.path.getsize(self.path) == remoteFilesize):
        complete = True

    except:
      print(sys.exc_info())

    return complete


  def verify(self, verify, progress):
    verified = False

    chunks = math.ceil(self.size/4096)

    verify.emit(0, 0, chunks, self.name)

    hashProgress = 0

    try:
      if (os.path.getsize(self.path) == self.size):
        # filesize matches, so check the hash; size + hash is more secure than hash alone
        with open(self.path, 'rb+') as f:
          hasher = self.algo()
          for chunk in iter(lambda: f.read(4096), b''):
            # Allow downloads to be interrupted
            if self.interrupt:
              return verified

            hasher.update(chunk)
            hashProgress += 1
            progress.emit(hashProgress)
          check = hasher.hexdigest()

        if (check == self.check):
          verified = True
        else:
          print("Hash mismatch")
      else:
        print("Filesize mismatch")
    except Exception:
      print(sys.exc_info())

    return verified

  def stop(self):
    self.interrupt = True
