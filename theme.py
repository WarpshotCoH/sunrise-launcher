import json
import os

from zipfile import ZipFile

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

        with ZipFile(path, "r") as z:
            z.extractall("themes")

            return Theme.fromPath(os.path.join("themes", themeName))

        return None
