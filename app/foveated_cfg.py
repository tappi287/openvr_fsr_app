from .openvr_mod_cfg import OpenVRModCfgSetting, OpenVRModSettings


class FoveatedSettings(OpenVRModSettings):
    cfg_key = 'foveated'

    def __init__(self):
        self.enabled = OpenVRModCfgSetting(
            key='enabled',
            name='Enabled',
            category='FFR Settings',
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.useVariableRateShading = OpenVRModCfgSetting(
            key='useVariableRateShading',
            name='Use Variable Rate Shading',
            category='FFR Settings',
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )

        # ---
        # Radius Settings
        # ---
        self.innerRadius = OpenVRModCfgSetting(
            key='innerRadius',
            name='Inner Radius',
            category='FFR Radius',
            value=0.60,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 1.00, 'step': 0.01}]
        )
        self.midRadius = OpenVRModCfgSetting(
            key='midRadius',
            name='Mid Radius',
            category='FFR Radius',
            value=0.80,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 1.00, 'step': 0.01}]
        )
        self.outerRadius = OpenVRModCfgSetting(
            key='outerRadius',
            name='Outer Radius',
            category='FFR Radius',
            value=1.00,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 2.00, 'step': 0.01}]
        )

        # ---
        # Sharpness Settings
        # ---
        self.sharpen = OpenVRModCfgSetting(
            key='sharpen',
            name='Sharpen',
            category='Sharpness Settings',
            hidden=True,
            value=dict(),
            settings=list(),
        )
        self.sharpenEnabled = OpenVRModCfgSetting(
            key='enabled',
            parent=self.sharpen.key,
            name='Sharpen Enabled',
            category='Sharpness Settings',
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.sharpenSharpness = OpenVRModCfgSetting(
            key='sharpness',
            parent=self.sharpen.key,
            name='Sharpness',
            category='Sharpness Settings',
            value=0.40,
            settings=[{'settingType': 'range', 'min': 0.00, 'max': 1.00, 'step': 0.01}]
        )
        self.sharpenRadius = OpenVRModCfgSetting(
            key='radius',
            parent=self.sharpen.key,
            name='Sharpen Radius',
            category='Sharpness Settings',
            value=0.75,
            settings=[{'settingType': 'range', 'min': 0.25, 'max': 1.00, 'step': 0.01}]
        )
        # ---
        # End of Sharpness Settings
        # ---

        self.debugMode = OpenVRModCfgSetting(
            key='debugMode',
            name='Debug Mode',
            category='FFR Settings',
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )

        # ---
        # Hotkey Settings
        # ---
        self.hotkeys = OpenVRModCfgSetting(
            key='hotkeys',
            name='Hotkeys',
            category='Hotkey Settings',
            hidden=True,
            value=dict(),
            settings=list(),
        )
        self.hotkeysEnabled = OpenVRModCfgSetting(
            key='enabled',
            parent=self.hotkeys.key,
            name='Hotkeys Enabled',
            category='Hotkey Settings',
            desc="If enabled, you can change certain settings of the mod on the fly by"
                 " pressing certain hotkeys. Good to see the visual difference. But you"
                 " may want to turn off hotkeys during regular play to prevent them from"
                 " interfering with game hotkeys.",
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.hotkeysRequireCtrl = OpenVRModCfgSetting(
            key='requireCtrl',
            parent=self.hotkeys.key,
            name='Require Ctrl',
            category='Hotkey Settings',
            desc="if enabled, must also be holding CTRL key to use hotkeys",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.hotkeysRequireAlt = OpenVRModCfgSetting(
            key='requireAlt',
            parent=self.hotkeys.key,
            name='Require Alt',
            category='Hotkey Settings',
            desc="if enabled, must also be holding ALT key to use hotkeys",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.hotkeysRequireShift = OpenVRModCfgSetting(
            key='requireShift',
            parent=self.hotkeys.key,
            name='Require Shift',
            category='Hotkey Settings',
            desc="if enabled, must also be holding SHIFT key to use hotkeys",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.hotkeysToggleFFR = OpenVRModCfgSetting(
            key='toggleFFR',
            parent=self.hotkeys.key,
            name='Toggle FFR',
            category='Hotkeys',
            desc='toggle fixed foveated rendering on or off',
            value=112,
            keyName='F1',
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysToggleDebugMode = OpenVRModCfgSetting(
            key='toggleDebugMode',
            parent=self.hotkeys.key,
            name='Toggle Debug mode',
            category='Hotkeys',
            desc='toggle debug mode on or off',
            value=113,
            keyName='F2',
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysDecreaseSharpness = OpenVRModCfgSetting(
            key='decreaseSharpness',
            parent=self.hotkeys.key,
            name='Decrease Sharpness',
            category='Hotkeys',
            desc='decrease sharpness by 0.05',
            value=114,
            keyName='F3',
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysIncreaseSharpness = OpenVRModCfgSetting(
            key='increaseSharpness',
            parent=self.hotkeys.key,
            name='Increase Sharpness',
            category='Hotkeys',
            desc='increase sharpness by 0.05',
            value=115,
            keyName='F4',
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysDecreaseRadius = OpenVRModCfgSetting(
            key='decreaseRadius',
            parent=self.hotkeys.key,
            name='Decrease Radius',
            category='Hotkeys',
            desc='decrease currently selected radius by 0.05',
            value=116,
            keyName='F5',
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysIncreaseRadius = OpenVRModCfgSetting(
            key='increaseRadius',
            parent=self.hotkeys.key,
            name='Increase Radius',
            category='Hotkeys',
            desc='increase currently selected radius by 0.05',
            value=117,
            keyName='F6',
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysSelectInnerRadius = OpenVRModCfgSetting(
            key='selectInnerRadius',
            parent=self.hotkeys.key,
            name='Select Inner Radius',
            category='Hotkeys',
            desc='select the inner FFR radius for manipulation',
            value=49,
            keyName='1',
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysSelectMidRadius = OpenVRModCfgSetting(
            key='selectMidRadius',
            parent=self.hotkeys.key,
            name='Select Mid Radius',
            category='Hotkeys',
            desc='select the middle FFR radius for manipulation',
            value=50,
            keyName='2',
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysSelectOuterRadius = OpenVRModCfgSetting(
            key='selectOuterRadius',
            parent=self.hotkeys.key,
            name='Select Outer Radius',
            category='Hotkeys',
            desc='select the outer FFR radius for manipulation',
            value=51,
            keyName='3',
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysSelectSharpenRadius = OpenVRModCfgSetting(
            key='selectSharpenRadius',
            parent=self.hotkeys.key,
            name='Select Sharpen Radius',
            category='Hotkeys',
            desc='select the sharpening radius for manipulation',
            value=52,
            keyName='4',
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysCaptureOutput = OpenVRModCfgSetting(
            key='captureOutput',
            parent=self.hotkeys.key,
            name='Capture Output',
            category='Hotkeys',
            desc='take a screenshot of the final output sent to the HMD',
            value=118,
            keyName='F7',
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysToggleUseVRS = OpenVRModCfgSetting(
            key='toggleUseVRS',
            parent=self.hotkeys.key,
            name='Toggle use VRS',
            category='Hotkeys',
            desc='toggle between variable rate shading (VRS) and radial density masking (RDM)',
            value=119,
            keyName='F8',
            settings=[{'settingType': 'key'}]
        )

        self.option_field_names = self.get_setting_fields()
