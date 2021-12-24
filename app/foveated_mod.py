import logging
from pathlib import Path
from typing import Optional

from .app_settings import AppSettings
from .fsr_cfg import FsrSettings
from .globals import OPEN_VR_DLL
from .openvr_mod import OpenVRMod
from .utils import get_file_hash


class FoveatedMod(OpenVRMod):
    def __init__(self, manifest: dict):
        self.settings = FsrSettings()
        self.settings.from_js_dict(manifest.get('fov_settings'))
        fsr_mod_dll = Path(AppSettings.openvr_foveated_dir) / OPEN_VR_DLL

        super(FoveatedMod, self).__init__(manifest, self.settings, fsr_mod_dll)

    @staticmethod
    def get_foveated_version_from_dll(openvr_dll: Path) -> Optional[str]:
        file_hash = get_file_hash(openvr_dll.as_posix())
        for version, hash_str in AppSettings.open_vr_foveated_versions.items():
            if file_hash != hash_str:
                continue
            return version

    def get_version(self) -> str:
        results = list()
        for open_vr_dll in self.manifest.get('openVrDllPathsSelected'):
            if not self._update_open_vr_dll_path(open_vr_dll):
                continue
            try:
                results.append(self.get_foveated_version_from_dll(self.open_vr_dll))
            except Exception as e:
                msg = f'Error reading dll version: {e}'
                self.error = msg
                logging.error(msg)

        version = ''
        for result in results:
            if version and result != version:
                logging.warning('Found multiple installed OpenVR Foveated versions for the same app!')
            version = result

        if not version:
            version = 'Unknown Version'

        return version
