from app.cfg.vrperfkit_rsf_cfg import VRPerfKitRsfSettings
from app.globals import DXGI_DLL
from app.mod import BaseModType, BaseMod


class VRPerfKitRsfMod(BaseMod):
    TYPE = BaseModType.vrp_rsf
    VAR_NAMES = {
        'installed': 'vrpRsfInstalled',
        'version': 'vrpRsfVersion',
        'settings': 'vrp_rsf_settings',
    }
    DLL_LOC_KEY_SELECTED = 'executablePathsSelected'
    DLL_LOC_KEY = 'executablePaths'
    DLL_NAME = DXGI_DLL  # Alternative would be d3d11.dll

    def __init__(self, manifest: dict):
        self.settings = VRPerfKitRsfSettings()
        self.settings.from_js_dict(manifest.get(self.VAR_NAMES['settings']))

        super(VRPerfKitRsfMod, self).__init__(manifest, self.settings)
