# TODO

* Refactor serverlistui and gamelistui to a single or base class
* Extract helper functions for creating widgets from ui files
* Lots of text extraction into external file (can we support translation?)
* Redo server list ordering hiding, the current impl is dumb
* Impl server, application, and runtime settings
* Impl global settings
* Clear details on tab switch
* Manifest adding ui
* Details view. News / website / etc
* Impl Sunrise auto-patching
* Launching on non-Windows
* Theme management and installing
* User setting persistance / loading (research appdirs)
* Auto-patch server, applicatio, runtime on selection
* Refactor application to be idiomatic to Python / Qt styles (custom widgets?)
* Pretty scrollbars
* High density image handling
* Windows layout adjustments
* Hide play from non-runable items
* Loading manifestList from stored settings generate keyerror on manifest list until manifests are loaded
* Optimizations are available pretty much everywhere

## Bugs
* Watcher timer shutdown bug
* Clicking on list subhead trigger select function to run and through index error
