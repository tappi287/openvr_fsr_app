from app.cfg.fsr_cfg import FsrSettings
from app.mod import BaseMod, BaseModType


class FsrMod(BaseMod):
    TYPE = BaseModType.fsr
    VAR_NAMES = {
        'installed': 'fsrInstalled',
        'version': 'fsrVersion',
        'settings': 'settings',
    }

    def __init__(self, manifest: dict):
        self.settings = FsrSettings()
        self.settings.from_js_dict(manifest.get(self.VAR_NAMES['settings']))

        super(FsrMod, self).__init__(manifest, self.settings)
