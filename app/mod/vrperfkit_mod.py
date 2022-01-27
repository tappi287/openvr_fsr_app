from app.cfg.vrperfkit_cfg import VRPerfKitSettings
from app.globals import DXGI_DLL
from app.mod import BaseModType, BaseMod


class VRPerfKitMod(BaseMod):
    TYPE = BaseModType.vrp
    VAR_NAMES = {
        'installed': 'vrpInstalled',
        'version': 'vrpVersion',
        'settings': 'vrp_settings',
    }
    DLL_LOC_KEY_SELECTED = 'executablePathsSelected'
    DLL_LOC_KEY = 'executablePaths'
    DLL_NAME = DXGI_DLL  # Alternative would be d3d11.dll

    def __init__(self, manifest: dict):
        self.settings = VRPerfKitSettings()
        self.settings.from_js_dict(manifest.get(self.VAR_NAMES['settings']))

        super(VRPerfKitMod, self).__init__(manifest, self.settings)
