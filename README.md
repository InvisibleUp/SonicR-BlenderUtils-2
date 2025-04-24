# Sonic R Blender Utilities v2

This is an updated version of the Sonic R importer for Blender. This add-on requires Blender 4.2 or greater, and has been tested with 4.3.

Because this is a Blender add-on, it is licensed under the GPLv3.

Builds are provided for:
- Windows on x86-64
- Linux on x86-64
- macOS 11+ on ARM

If you're using another operating system or archiecture, you will need to build the extension yourself.

## Building

Install Python 3.11 or greater, and ensure Blender is on your path.

After that, you'll need to acquire the Python wheels listed in `blender_manifest.toml` from PyPI. This is not currently automated; you can either download them via your web browser or via `pip`. See https://docs.blender.org/manual/en/latest/advanced/extensions/python_wheels.html for details.

Then run `blender --command extension build` to create the .ZIP file for the add-on.

You can also try running `blender --command extension build --split-platforms`. This will generate one .ZIP file for each platform. This is a good idea due to the sheer size of Pillow and Numpy.

## Setup

First, download the add-on from the Releases tab on GitHub. You can also build it yourself by running `blender --command extension build` in the root directory of this respository.

In Blender's Preferences window, navigate to "Add-ons" and select "Install from Disk" from the drop-down menu in the top right. Select the .ZIP file you downloaded or built.

## Usage

One the plug-in is installed and activated, go to File > Import, and select "Sonic R Track (.bin)". Select a track .bin file from your Sonic R install directory. In the sidebar on the right, you can select the weather and time of day to enable custom lighting. You can also override the track metadata file to use, if needed.

As of writing, floor maps are not automatically converted from Sonic R's native format. If you wish to view them, use [MapConverter](https://gamebanana.com/tools/8471) and move the resulting `map.png` to the course's directory, naming it `[course]floor.png`. (ex: `islandfloor.png`). Future versions of this converter will do this for you automatically.

As of right now, only track imports are supported. Character imports will be worked on next. It is unlikely that exporting will be supported in the near future.