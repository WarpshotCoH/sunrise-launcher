# Sunrise Launcher
**Sunrise** is an open-source game launcher designed to service an MMO with multiple communities, supporting their various code forks and servers under one launcher.

Sunrise uses a special manifest format to support downloading games (split into "servers", "applications", and "runtimes"), which can be found at https://github.com/WarpshotCoH/sunrise-specs.

## Installation
> **NOTE:** If you're not planning to actually edit/debug the code, you don't want to follow these steps, you'll want to use the packages provided by the game/communities you wish to play with. Sunrise in its default state here doesn't support any games.

### System requirements
 - [Python 3](https://www.python.org/)
 - [Pip](https://pypi.org/project/pip/)
 - [Virtualenv](https://virtualenv.pypa.io)

The launcher will currently run on Windows, macOS, and Linux, but Wine support for the latter two is not yet ready, so you can't launch games.

After downloading the code and changing to the current folder, run:

```sh
# Setup virtualenv
$ virtualenv venv

# Windows only
> venv\Scripts\activate

# macOS/Linux only
$ source venv/bin/activate

# Install dependencies
$ pip install -r requirements.txt
```

### Configuration
You need to edit `config.json` with values relating to your target game.
```json
{
    "about": {
        "about_button_1_url": "",
        "about_button_2_url": "",
        "source_url": "https://github.com/sunrise-launcher/sunrise-launcher"
    },

    "flags": {
        "add_theme": true,
        "use_symlinks": true,
        "file_db": true
    }
}
```

### Running
```sh
# Windows only
> venv\Scripts\activate

# macOS/Linux only
$ source venv/bin/activate

# Run application
$ python3 main.py
```

## License
The main code of Sunrise (the `.py` files in the root folder, as well as the entirety of the `ui/` folder) are licensed under the GPLv3.

Other portions of the project such as icons may be licensed differently - either click the *"Licenses"* button in Sunrise's About screen, or see the `resources/licenses/` folder for further information.

The Sunrise name, logo and icon remain copyright of the Sunrise launcher project. Please replace these with your game's branding upon redistribution. Referring to the project as "based on Sunrise" or "powered by Sunrise" is perfectly fine however.
