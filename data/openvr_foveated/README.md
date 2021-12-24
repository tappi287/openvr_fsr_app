Fixed Foveated Rendering mod for SteamVR games
---

This modified openvr_api.dll will enable Fixed Foveated Rendering (FFR) in D3D11-based
SteamVR games.

### About Fixed Foveated Rendering

The idea behind "fixed foveated" rendering is to save some GPU performance by rendering the
outer areas of the VR images at a lower resolution while still rendering the center of the image
at full resolution. Due to current HMD optics, the edges of the image are blurry, anyway, so
rendering those parts at a lower resolution can save performance without impacting the visual
fidelity too badly.

This mod divides the image into 4 rings, with each ring's radius being configurable.
The inner-most ring (image center) is rendered at full resolution, the second ring at half
resolution, the third ring at a quarter of the original resolution, and the remainder of the
image is rendered at 1/16th of the original resolution.

Optionally, a sharpening filter can be applied to the final image. While this doesn't strictly
have anything to do with FFR, most VR games benefit from a bit of sharpening.

### Notes about game compatibility

This mod injects itself into the rendering process of the game. Unfortunately, not all games
will work well with the chosen approach and may either break completely or display only the
inner-most ring of the image properly. In some cases, disabling certain graphics settings may
be required to get FFR working. In other instances, the game may simply be incompatible.

Please refer to the [Wiki](https://github.com/fholger/openvr_foveated/wiki) for information
about particular games that have been tested by myself or others. Feel free to add your own
test results.

### Installation instructions

First, download the `openvr_foveated.zip` file from the [latest release](https://github.com/fholger/openvr_foveated/releases/latest) under "Assets".

Then find the location of the openvr_api.dll in the game's installation
folder: 
- It might be located right next to the main executable (e.g. Skyrim, FO4).
- For Unity games, look in: `<GameDir>\<Game>_Data\Plugins`
- For Unreal 4 games, look in: `<GameDir>\Engine\Binaries\ThirdParty\OpenVR\OpenVRvX_Y_Z`

Rename the existing `openvr_api.dll` to `openvr_api.orig.dll`, then extract both
the `openvr_api.dll` and the `openvr_mod.cfg` from the archive to this directory.
You can now edit the `openvr_mod.cfg` to your liking or just use the defaults.

In case you want to uninstall the mod, simply remove the `openvr_api.dll` file again
and rename the original `openvr_api.orig.dll` back to `openvr_api.dll`.

In case you run into issues, the log file (`openvr_mod.log`) may provide clues to
what's going on.

### Configuration

The mod is configured by editing the values in its config file, `openvr_mod.cfg`. The
parameters `innerRadius`, `midRadius` and `outerRadius` determine the size of the four
rings as described above. The smaller the values for the radii, the fewer pixels are rendered,
but visual fidelity will suffer. Experiment at will.

If `enableHotkeys` is set to true, you can use hotkeys to toggle mod settings on the fly.
Available hotkeys:

* <F1> - toggle Fixed Foveated Rendering on or off.


OpenVR SDK
---

OpenVR is an API and runtime that allows access to VR hardware from multiple 
vendors without requiring that applications have specific knowledge of the 
hardware they are targeting. This repository is an SDK that contains the API 
and samples. The runtime is under SteamVR in Tools on Steam. 

### Documentation

Documentation for the API is available on the [GitHub Wiki](https://github.com/ValveSoftware/openvr/wiki/API-Documentation)

More information on OpenVR and SteamVR can be found on http://steamvr.com
