import json
import os
from zipfile import ZipFile

from PySide2.QtGui import QFontDatabase

from helpers import SunriseSettings, pi, logger

log = logger("main.theme")

class Theme:
    def __init__(self, props = None, css = None):
        self.props = props
        self.css = css

    @staticmethod
    def fromPath(path):
        theme = Theme()

        log.info("Loading theme from %s", path)

        propsPath = os.path.join(path, "props.json")
        log.info("Loading props form %s", propsPath)

        stylePath = os.path.join(path, "styles.css")
        log.info("Loading styles form %s", stylePath)

        with open(propsPath, "r") as props:
            theme.props = json.loads(props.read().replace("$PATH", path))

        with open(stylePath, "r") as styles:
            theme.css = styles.read().replace("$PATH", path)

        log.info("Loaded theme %s", theme)

        return theme

    def activate(self, application):
        try:
            default = Theme.fromPath(pi("resources"))

            if default.props and "fonts" in default.props:
                for font in default.props["fonts"]:
                    QFontDatabase.addApplicationFont(font)

            if self.props and "fonts" in self.props:
                for font in self.props["fonts"]:
                    QFontDatabase.addApplicationFont(font)

            application.setStyleSheet(default.css + self.css)
        except Exception as e:
            log.error("Theme activation failure: %s", e)

class Loader:
    @staticmethod
    def load(path):
        themeName = os.path.basename(path).replace(".sunrisetheme", "")
        themeInstallPath = os.path.join(SunriseSettings.settingsPath, "themes")

        if not os.path.isdir(themeInstallPath):
            os.makedirs(themeInstallPath)

        with ZipFile(path, "r") as z:
            z.extractall(themeInstallPath)

            return Theme.fromPath(os.path.join(themeInstallPath, themeName))

        return None
