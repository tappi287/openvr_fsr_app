import logging
from pathlib import Path
from typing import Optional

from .app_settings import AppSettings
from .fsr_cfg import FsrSettings
from .openvr_mod import OpenVRMod
from .utils import get_file_hash


class FsrMod(OpenVRMod):
    def __init__(self, manifest: dict):
        self.settings = FsrSettings()
        self.settings.from_js_dict(manifest.get('settings'))
        super(FsrMod, self).__init__(manifest, self.settings)

    @staticmethod
    def get_fsr_version_from_dll(openvr_dll: Path) -> Optional[str]:
        file_hash = get_file_hash(openvr_dll.as_posix())
        for version, hash_str in AppSettings.open_vr_fsr_versions.items():
            if file_hash != hash_str:
                continue
            return version

    def get_fsr_version(self) -> str:
        results = list()
        for open_vr_dll in self.manifest.get('openVrDllPathsSelected'):
            if not self._update_open_vr_dll_path(open_vr_dll):
                continue
            try:
                results.append(self.get_fsr_version_from_dll(self.open_vr_dll))
            except Exception as e:
                msg = f'Error reading dll version: {e}'
                self.error = msg
                logging.error(msg)

        version = ''
        for result in results:
            if version and result != version:
                logging.warning('Found multiple installed OpenVR FSR versions for the same app!')
            version = result

        if not version:
            version = 'Unknown Version'

        return version
