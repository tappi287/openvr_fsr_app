from pathlib import Path

from .app_settings import AppSettings
from .fsr_cfg import FsrSettings
from .globals import OPEN_VR_DLL
from .openvr_mod import OpenVRMod, OpenVRModType


class FsrMod(OpenVRMod):
    TYPE = OpenVRModType.fsr
    VAR_NAMES = {
        'installed': 'fsrInstalled',
        'version': 'fsrVersion'
    }

    def __init__(self, manifest: dict):
        self.settings = FsrSettings()
        self.settings.from_js_dict(manifest.get('settings'))
        fsr_mod_dll = Path(AppSettings.openvr_fsr_dir) / OPEN_VR_DLL

        super(FsrMod, self).__init__(manifest, self.settings, fsr_mod_dll)
