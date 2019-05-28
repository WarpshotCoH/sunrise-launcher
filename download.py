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
from helpers import logger

log = logger("main.downloader.file")

class FileDownload():
    def __init__(self, file, writePath, mirror = None):
        self.file = file
        self.path = writePath
        self.mirror = mirror
        self.interrupt = False
        self.skipHashCheck = False

    def toggleHashCheck(self, state = None):
        if state == None:
            self.skipHashCheck = not self.skipHashCheck
        else:
            self.skipHashCheck = state

    def start(self, init, progress):
        log.info("Start file download")

        # First try downloading from the designated mirror
        if self.mirror:
            log.debug("%s mirror selected. Attempting to download from mirror first", self.mi)
            if self.downloadUrl(self.mirror + self.file.name, init, progress):
                return True

        urlNumToTry = random.randint(0, len(self.file.urls) - 1)
        downloaded = False
        tries = 0

        while (not downloaded and tries < len(self.file.urls)):

            # Allow downloads to be interrupted
            if self.interrupt:
                return downloaded

            log.debug("%s %s %s %s", downloaded, urlNumToTry, tries, self.file.urls[urlNumToTry])

            if (tries > len(self.file.urls) - 1):
                log.warning("Ran out of tries")
                return downloaded

            url = self.file.urls[urlNumToTry]
            downloaded = self.downloadUrl(url, init, progress)
            urlNumToTry += 1

            if (urlNumToTry > len(self.file.urls) - 1):
                urlNumToTry = 0

            tries += 1

        return downloaded

    def downloadUrl(self, url, init, progress):
        log.info("Start url download %s", url)

        complete = False

        try:
            r = requests.get(url, stream=True, timeout=5)

            remoteFilename = posixpath.basename(urllib.parse.urlparse(url).path)
            # TODO: Handle Transfer-Encoding: chunked; unable to know the remote filesize there.
            remoteFilesize = int(r.headers['Content-Length']) if 'Content-Length' in r.headers else self.file.size

            init.emit(0, 0, remoteFilesize, remoteFilename)

            log.info("Downloading %s from: %s", remoteFilename, url)

            fileProgress = 0

            with r:
                r.raise_for_status()
                with open(self.path, 'wb+') as f:
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
            log.error("Download error %s", self.file.name)
            log.error(sys.exc_info())

        return complete


    def verify(self, verify, progress):
        multiplier = 128
        verified = False

        chunks = math.ceil(self.file.size / (65536 * multiplier))

        verify.emit(0, 0, chunks, self.file.name)

        hashProgress = 0

        try:
            if (os.path.getsize(self.path) == self.file.size):
                if self.skipHashCheck:
                    log.debug("Skip hash check")
                    progress.emit(chunks)
                    return True

                # filesize matches, so check the hash; size + hash is more secure than hash alone
                with open(self.path, 'rb+') as f:
                    hasher = algoMap[self.file.algo]()
                    for chunk in iter(lambda: f.read(65536 * multiplier), b''):
                        # Allow downloads to be interrupted
                        if self.interrupt:
                            return verified

                        hasher.update(chunk)
                        hashProgress += 1
                        progress.emit(hashProgress)
                    check = hasher.hexdigest()

                if (check == self.file.check):
                    verified = True
                else:
                    log.warning("Hash mismatch")
            else:
                log.warning("Filesize mismatch")
        except Exception:
            log.error(sys.exc_info())

        return verified

    def stop(self):
        self.interrupt = True
