from .openvr_mod_cfg import OpenVRModCfgSetting, OpenVRModSettings


class FsrSettings(OpenVRModSettings):
    def __init__(self):
        self.enabled = OpenVRModCfgSetting(
            key='enabled',
            name='Enabled',
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.useNIS = OpenVRModCfgSetting(
            key='useNIS',
            name="Use NVIDIA's Image Scaling",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.renderScale = OpenVRModCfgSetting(
            key='renderScale',
            name='Render Scale',
            value=0.77,
            settings=[{'settingType': 'range', 'min': 0.10, 'max': 3.0, 'step': 0.01, 'display': 'floatpercent'}]
        )
        self.sharpness = OpenVRModCfgSetting(
            key='sharpness',
            name='Sharpness',
            value=0.9,
            settings=[{'settingType': 'range', 'min': 0.10, 'max': 3.0, 'step': 0.01, 'display': 'floatpercent'}]
        )
        self.radius = OpenVRModCfgSetting(
            key='radius',
            name='Radius',
            value=0.50,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 2.00, 'step': 0.01}]
        )
        self.applyMIPBias = OpenVRModCfgSetting(
            key='applyMIPBias',
            name='Apply MIP Bias',
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.debugMode = OpenVRModCfgSetting(
            key='debugMode',
            name='Debug Mode',
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        options = [self.enabled.key, self.useNIS.key, self.renderScale.key, self.sharpness.key, self.radius.key,
                   self.applyMIPBias.key, self.debugMode.key]
        super(FsrSettings, self).__init__(options, 'fsr')
