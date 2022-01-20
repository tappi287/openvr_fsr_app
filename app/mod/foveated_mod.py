from pathlib import Path

from app.app_settings import AppSettings
from app.cfg.foveated_cfg import FoveatedSettings
from app.globals import OPEN_VR_DLL
from app.mod.openvr_mod import OpenVRMod, OpenVRModType


class FoveatedMod(OpenVRMod):
    TYPE = OpenVRModType.foveated
    VAR_NAMES = {
        'installed': 'fovInstalled',
        'version': 'fovVersion',
        'settings': 'fov_settings',
    }

    def __init__(self, manifest: dict):
        self.settings = FoveatedSettings()
        self.settings.from_js_dict(manifest.get(self.VAR_NAMES['settings']))
        fov_mod_dll = Path(AppSettings.openvr_foveated_dir) / OPEN_VR_DLL

        super(FoveatedMod, self).__init__(manifest, self.settings, fov_mod_dll)
