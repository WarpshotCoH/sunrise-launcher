import json
import os

from zipfile import ZipFile

class Theme:
    def __init__(self, props = None, css = None):
        self.props = props
        self.css = css

class Loader:
    @staticmethod
    def load(path):
        themeName = os.path.basename(path).replace(".sunrisetheme", "")

        with ZipFile(path, "r") as z:
            z.extractall("themes")

            theme = Theme()

            propsPath = os.path.join("themes", themeName, "props.json")
            stylePath = os.path.join("themes", themeName, "styles.css")

            with open(propsPath, "r") as props:
                theme.props = json.loads(props.read())

            with open(stylePath, "r") as styles:
                theme.css = styles.read()

            return theme

        return None
