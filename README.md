# Sonic R Blender Utilities v2

This is an updated version of the Sonic R importer for Blender. This add-on requires Blender 4.2 or greater, and has been tested with 4.3.

Because this is a Blender add-on, it is licensed under the GPLv3.

## Setup

First, download the add-on from the Releases tab on GitHub. You can also build it yourself by running `blender --command extension build` in the root directory of this respository.

In Blender's Preferences window, navigate to "Add-ons" and select "Install from Disk" from the drop-down menu in the top right. Select the .ZIP file you downloaded or built.

You'll also need to prepare the files that this add-on expects. As of right now, the directory structure needs to be like so:

- island_e.bin
- city_b.bin
- [...].bin
- general\
    - general00.png
    - general01.png
    - ...
- island\
    - island00.png
    - island01.png
    - ...
- city\
    - ...
- ...

Future versions should be able to work directly with the Sonic R files.

## Usage

One the plug-in is installed and activated, go to File > Import, and select "Sonic R Track (.bin)". Select the .bin file you prepared in the setup step. In the sidebar on the right, select the name of the track you selected and, optionally, the weather and time of day to enable custom lighting.

As of right now, only imports are supported.