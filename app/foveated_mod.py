from pathlib import Path

from .app_settings import AppSettings
from .foveated_cfg import FoveatedSettings
from .globals import OPEN_VR_DLL
from .openvr_mod import OpenVRMod, OpenVRModType


class FoveatedMod(OpenVRMod):
    TYPE = OpenVRModType.foveated
    VAR_NAMES = {
        'installed': 'fovInstalled',
        'version': 'fovVersion'
    }

    def __init__(self, manifest: dict):
        self.settings = FoveatedSettings()
        self.settings.from_js_dict(manifest.get('fov_settings'))
        fov_mod_dll = Path(AppSettings.openvr_foveated_dir) / OPEN_VR_DLL

        super(FoveatedMod, self).__init__(manifest, self.settings, fov_mod_dll)
