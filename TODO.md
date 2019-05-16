# TODO

* Refactor serverlistui and gamelistui to a single or base class
* Extract helper functions for creating widgets from ui files
* Expand downloader states. Needs Not Installed state, and Downloaded / Verified but not playable state (ie. for clients / runtimes)
* Verification / download for runtimes without connection to application
* Lots of text extraction into external file (can we support translation?)
* Redo server list ordering hiding, the current impl is dumb
* Impl server, application, and runtime settings
* Impl server, application, runtime repair
* Impl global settings
* Manifest adding ui
* Details view. News / website / etc
* Impl Sunrise auto-patching
* Launching on non-Windows
* Theme management and installing
* User setting persistance / loading (research appdirs)
* Auto-patch server, applicatio, runtime on selection
* Track install state in user settings
* Watcher timer shutdown bug
* Play / Download button language
* Create default theme
* Refactor application to be idiomatic to Python / Qt styles (custom widgets?)