from app.cfg.foveated_cfg import FoveatedSettings
from app.mod import BaseMod, BaseModType


class FoveatedMod(BaseMod):
    TYPE = BaseModType.foveated
    VAR_NAMES = {
        'installed': 'fovInstalled',
        'version': 'fovVersion',
        'settings': 'fov_settings',
    }

    def __init__(self, manifest: dict):
        self.settings = FoveatedSettings()
        self.settings.from_js_dict(manifest.get(self.VAR_NAMES['settings']))

        super(FoveatedMod, self).__init__(manifest, self.settings)
