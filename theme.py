import json
import os
from zipfile import ZipFile

from settings import SunriseSettings

class Theme:
    def __init__(self, props = None, css = None):
        self.props = props
        self.css = css

    @staticmethod
    def fromPath(path):
        theme = Theme()

        propsPath = os.path.join(path, "props.json")
        stylePath = os.path.join(path, "styles.css")

        with open(propsPath, "r") as props:
            theme.props = json.loads(props.read())

        with open(stylePath, "r") as styles:
            theme.css = styles.read()

        return theme

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
