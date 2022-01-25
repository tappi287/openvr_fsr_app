from app.globals import OPEN_VR_FSR_CFG
from app.cfg import BaseModCfgSetting, BaseModSettings, BaseModCfgType


class FsrSettings(BaseModSettings):
    cfg_key = 'fsr'
    format = 'cfg'
    CFG_FILE = OPEN_VR_FSR_CFG
    CFG_TYPE = BaseModCfgType.open_vr_mod

    def __init__(self):
        self.enabled = BaseModCfgSetting(
            key='enabled',
            name='Enabled',
            category='FSR Settings',
            desc="enable image upscaling through AMD's FSR or NVIDIA's NIS",
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.useNIS = BaseModCfgSetting(
            key='useNIS',
            name="Use NVIDIA's Image Scaling",
            category='FSR Settings',
            desc="if enabled, uses NVIDIA's Image Scaling instead of the default "
                 "AMD FidelityFX SuperResolution. Both algorithms work similarly, but produce"
                 "somewhat different results. You may want to experiment switching between the"
                 "two to determine which one you like better for a particular game.",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.renderScale = BaseModCfgSetting(
            key='renderScale',
            name='Render Scale',
            category='FSR Settings',
            desc="Per-dimension render scale. If <1, will lower the game's render resolution"
                 "accordingly and afterwards upscale to the native resolution set in SteamVR. "
                 "If >1, the game will render at its native resolution, and afterwards the "
                 "image is upscaled to a higher resolution as per the given value. "
                 "If =1, effectively disables upsampling, but you'll still get the sharpening stage. "
                 "AMD presets: Ultra Quality => 0.77 Quality       => 0.67 Balanced      => 0.59 "
                 "Performance   => 0.50",
            value=0.77,
            settings=[{'settingType': 'range', 'min': 0.10, 'max': 3.0, 'step': 0.01, 'display': 'floatpercent'}]
        )
        self.sharpness = BaseModCfgSetting(
            key='sharpness',
            name='Sharpness',
            category='FSR Settings',
            desc="tune sharpness, values range from 0 to 1",
            value=0.9,
            settings=[{'settingType': 'range', 'min': 0.10, 'max': 3.0, 'step': 0.01, 'display': 'floatpercent'}]
        )
        self.radius = BaseModCfgSetting(
            key='radius',
            name='Radius',
            category='FSR Settings',
            desc="Only apply FSR/NIS to the given radius around the center of the image. "
                 "Anything outside this radius is upscaled by simple bilinear filtering,"
                 " which is cheaper and thus saves a bit of performance. Due to the design"
                 " of current HMD lenses, you can experiment with fairly small radii and may"
                 " still not see a noticeable difference."
                 " Sensible values probably lie somewhere between [0.2, 1.0]. However, note"
                 " that, since the image is not spheric, even a value of 1.0 technically still"
                 " skips some pixels in the corner of the image, so if you want to completely"
                 " disable this optimization, you can choose a value of 2."
                 " IMPORTANT: if you face issues like the view appearing offset or mismatched"
                 " between the eyes, turn this optimization off by setting the value to 2.0",
            value=0.50,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 2.00, 'step': 0.01}]
        )
        self.applyMIPBias = BaseModCfgSetting(
            key='applyMIPBias',
            name='Apply MIP Bias',
            category='FSR Settings',
            desc="if enabled, applies a negative LOD bias to texture MIP levels"
                 " should theoretically improve texture detail in the upscaled image"
                 " IMPORTANT: if you experience issues with rendering like disappearing"
                 " textures or strange patterns in the rendering, try turning this off"
                 " by setting the value to false.",
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.debugMode = BaseModCfgSetting(
            key='debugMode',
            name='Debug Mode',
            category='FSR Settings',
            desc="If enabled, will visualize the radius to which FSR/NIS is applied."
                 " Will also periodically log the GPU cost for applying FSR/NIS in the"
                 " current configuration.",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )

        # ---
        # Hotkey Settings
        # ---
        self.hotkeys = BaseModCfgSetting(
            key='hotkeys',
            name='Hotkeys',
            category='Hotkey Settings',
            hidden=True,
            value=dict(),
            settings=list(),
        )
        self.hotkeysEnabled = BaseModCfgSetting(
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
        self.hotkeysRequireCtrl = BaseModCfgSetting(
            key='requireCtrl',
            parent=self.hotkeys.key,
            name='Require Ctrl',
            category='Hotkey Settings',
            desc="if enabled, must also be holding CTRL key to use hotkeys",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.hotkeysRequireAlt = BaseModCfgSetting(
            key='requireAlt',
            parent=self.hotkeys.key,
            name='Require Alt',
            category='Hotkey Settings',
            desc="if enabled, must also be holding ALT key to use hotkeys",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.hotkeysRequireShift = BaseModCfgSetting(
            key='requireShift',
            parent=self.hotkeys.key,
            name='Require Shift',
            category='Hotkey Settings',
            desc="if enabled, must also be holding SHIFT key to use hotkeys",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.hotkeysToggleUseNIS = BaseModCfgSetting(
            key='toggleUseNIS',
            parent=self.hotkeys.key,
            name='Toggle NIS',
            category='Hotkeys',
            desc='switch between FSR and NIS',
            value=112,  # F1
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysToggleDebugMode = BaseModCfgSetting(
            key='toggleDebugMode',
            parent=self.hotkeys.key,
            name='Toggle Debug Mode',
            category='Hotkeys',
            desc='toggle debug mode on or off',
            value=113,  # F2
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysDecreaseSharpness = BaseModCfgSetting(
            key='decreaseSharpness',
            parent=self.hotkeys.key,
            name='Decrease Sharpness',
            category='Hotkeys',
            desc='decrease sharpness by 0.05',
            value=114,  # F3
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysIncreaseSharpness = BaseModCfgSetting(
            key='increaseSharpness',
            parent=self.hotkeys.key,
            name='Increase Sharpness',
            category='Hotkeys',
            desc='increase sharpness by 0.05',
            value=115,  # F4
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysDecreaseRadius = BaseModCfgSetting(
            key='decreaseRadius',
            parent=self.hotkeys.key,
            name='Decrease Radius',
            category='Hotkeys',
            desc='decrease sharpening radius by 0.05',
            value=116,  # F5
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysIncreaseRadius = BaseModCfgSetting(
            key='increaseRadius',
            parent=self.hotkeys.key,
            name='Increase Radius',
            category='Hotkeys',
            desc='increase sharpening radius by 0.05',
            value=117,  # F6
            settings=[{'settingType': 'key'}]
        )
        self.hotkeysCaptureOutput = BaseModCfgSetting(
            key='captureOutput',
            parent=self.hotkeys.key,
            name='Capture Output',
            category='Hotkeys',
            desc='take a screenshot of the final output sent to the HMD',
            value=118,  # F7
            settings=[{'settingType': 'key'}]
        )
        super(FsrSettings, self).__init__()
