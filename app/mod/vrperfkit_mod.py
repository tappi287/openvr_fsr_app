from pathlib import Path

from app.app_settings import AppSettings
from app.cfg.vrperfkit_cfg import VRPerfKitSettings
from app.globals import DXGI_DLL
from .base_mod import BaseMod, BaseModType


class VRPerfKitMod(BaseMod):
    TYPE = BaseModType.vrp
    VAR_NAMES = {
        'installed': 'vrpInstalled',
        'version': 'vrpVersion',
        'settings': 'vrp_settings',
    }
    DLL_LOC_KEY_SELECTED = 'executablePathsSelected'
    DLL_LOC_KEY = 'executablePaths'
    DLL_NAME = DXGI_DLL

    def __init__(self, manifest: dict):
        vrp_mod_dll = Path(AppSettings.vrperfkit_dir) / DXGI_DLL
        self.settings = VRPerfKitSettings(vrp_mod_dll)
        self.settings.from_js_dict(manifest.get(self.VAR_NAMES['settings']))

        super(VRPerfKitMod, self).__init__(manifest, self.settings, vrp_mod_dll)
