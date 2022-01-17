from pathlib import Path

from .app_settings import AppSettings
from .vrperfkit_cfg import VRPerfKitSettings
from .globals import DXGI_DLL
from .openvr_mod import OpenVRMod, OpenVRModType


class VRPerfKitMod(OpenVRMod):
    TYPE = OpenVRModType.vrp
    VAR_NAMES = {
        'installed': 'vrpInstalled',
        'version': 'vrpVersion',
        'settings': 'vrp_settings',
    }

    def __init__(self, manifest: dict):
        self.settings = VRPerfKitSettings()
        self.settings.from_js_dict(manifest.get(self.VAR_NAMES['settings']))
        vrp_mod_dll = Path(AppSettings.vrperfkit_dir) / DXGI_DLL

        super(VRPerfKitMod, self).__init__(manifest, self.settings, vrp_mod_dll)
