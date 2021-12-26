from .openvr_mod_cfg import OpenVRModCfgSetting, OpenVRModSettings


class FoveatedSettings(OpenVRModSettings):
    def __init__(self):
        self.enabled = OpenVRModCfgSetting(
            key='enabled',
            name='Enabled',
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.innerRadius = OpenVRModCfgSetting(
            key='innerRadius',
            name='Inner Radius',
            value=0.60,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 1.00, 'step': 0.01}]
        )
        self.midRadius = OpenVRModCfgSetting(
            key='midRadius',
            name='Mid Radius',
            value=0.80,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 1.00, 'step': 0.01}]
        )
        self.outerRadius = OpenVRModCfgSetting(
            key='outerRadius',
            name='Outer Radius',
            value=1.00,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 2.00, 'step': 0.01}]
        )
        self.sharpen = OpenVRModCfgSetting(
            key='sharpen',
            name='Sharpen',
            hidden=True,
            value=dict(),
            settings=list(),
        )
        self.sharpenEnabled = OpenVRModCfgSetting(
            key='enabled',
            parent=self.sharpen.key,
            name='Sharpen Enabled',
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.sharpenSharpness = OpenVRModCfgSetting(
            key='sharpness',
            parent=self.sharpen.key,
            name='Sharpness',
            value=0.40,
            settings=[{'settingType': 'range', 'min': 0.00, 'max': 1.00, 'step': 0.01}]
        )
        self.sharpenRadius = OpenVRModCfgSetting(
            key='radius',
            parent=self.sharpen.key,
            name='Sharpen Radius',
            value=0.75,
            settings=[{'settingType': 'range', 'min': 0.25, 'max': 1.00, 'step': 0.01}]
        )
        self.debugMode = OpenVRModCfgSetting(
            key='debugMode',
            name='Debug Mode',
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.enableHotkeys = OpenVRModCfgSetting(
            key='enableHotkeys',
            name='Enable Hotkeys',
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        options = [self.enabled.key, self.innerRadius.key, self.midRadius.key, self.outerRadius.key,
                   self.sharpen.key, 'sharpenEnabled', 'sharpenSharpness', 'sharpenRadius',
                   self.debugMode.key, self.enableHotkeys.key]
        super(FoveatedSettings, self).__init__(options, 'foveated')