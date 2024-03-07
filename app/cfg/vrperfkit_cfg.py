from app.cfg import BaseModCfgSetting, BaseModSettings, BaseModCfgType
from app.globals import VRPERFKIT_CFG


# TODO: update to support all parameters of C:\py\openvr_fsr_app\data\vrperfkit\vrperfkit_RSF.yml
class VRPerfKitSettings(BaseModSettings):
    cfg_key = None
    format = 'yml'
    CFG_FILE = VRPERFKIT_CFG
    CFG_TYPE = BaseModCfgType.vrp_mod

    def __init__(self):
        # Settings matching the parameters of C:\py\openvr_fsr_app\data\vrperfkit\vrperfkit_RSF.yml
        # --
        # Upscaling Settings
        # --
        self.upscaling = BaseModCfgSetting(
            key='upscaling',
            name='Upscaling',
            category='Upscaling',
            hidden=True,
            value=dict(),
            settings=list(),
        )
        self.upEnabled = BaseModCfgSetting(
            key='enabled',
            name='Enabled',
            category=self.upscaling.category,
            parent=self.upscaling.key,
            desc="Enable Upscaling: render the game at a lower resolution (thus saving performance), "
                 "then upscale the image to the target resolution to regain some of the lost "
                 "visual fidelity.",
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.upMethod = BaseModCfgSetting(
            key='method',
            name='Method',
            category=self.upscaling.category,
            parent=self.upscaling.key,
            desc="Method to use for upscaling. Available options (all of them work on all GPUs): "
                 "fsr (AMD FidelityFX Super Resolution), "
                 "nis (NVIDIA Image Scaling), "
                 "cas (AMD FidelityFX Contrast Adaptive Sharpening)",
            value='nis',
            settings=[{'value': 'fsr', 'name': 'FSR'}, {'value': 'nis', 'name': 'NIS'}, {'value': 'cas', 'name': 'CAS'}]
        )
        self.upRenderScale = BaseModCfgSetting(
            key='renderScale',
            name='Render Scale',
            category=self.upscaling.category,
            parent=self.upscaling.key,
            desc="Control how much the render resolution is lowered. The renderScale is the percentage "
                 "used to scale resolution used by the GPU to render. For example, a value of 50 (50%) "
                 "means GPU will use half of pixels. This is same from how render scale works in SteamVR. "
                 "If you set a value higher than 100 for renderScale, then the game will render at the native "
                 "resolution, i.e. the one configured in SteamVR. But FSR/NIS/CAS will then take this render and "
                 "upscale it to a resolution increased by the value of renderScale percentage.",
            value=70.0,
            settings=[{'settingType': 'range', 'min': 0.10, 'max': 999.00, 'step': 1.00, 'display': 'percent'}]
        )
        self.upSharpness = BaseModCfgSetting(
            key='sharpness',
            name='Sharpness',
            category=self.upscaling.category,
            parent=self.upscaling.key,
            desc="Configure how much the image is sharpened during upscaling. "
                 "This parameter works differently for each of the upscaling methods, so you "
                 "will have to tweak it after you have chosen your preferred upscaling method.",
            value=0.3,
            settings=[{'settingType': 'range', 'min': 0.00, 'max': 3.00, 'step': 0.01, 'display': 'floatpercent'}]
        )
        self.upSharpnessRadius = BaseModCfgSetting(
            key='radius',
            name='Radius',
            category=self.upscaling.category,
            parent=self.upscaling.key,
            desc="Performance optimization: only apply the (more expensive) upscaling method "
                 "to an inner area of the rendered image and use cheaper bi-linear sampling on "
                 "the rest of the image. The radius parameter determines how large the area "
                 "with the more expensive upscaling is. Upscaling happens within a circle "
                 "centered at the projection centre of the eyes. You can use debugMode (below) "
                 "to visualize the size of the circle. "
                 "Note: to disable this optimization entirely, choose an arbitrary high value "
                 "(e.g. 100) for the radius.",
            value=0.95,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 3.00, 'step': 0.01}]
        )
        self.upApplyMIPBias = BaseModCfgSetting(
            key='applyMipBias',
            name='Apply MIP Bias',
            category=self.upscaling.category,
            parent=self.upscaling.key,
            desc="When enabled, applies a MIP bias to texture sampling in the game. This will "
                 "make the game treat texture lookups as if it were rendering at the higher "
                 "target resolution, which can improve image quality a little bit. However, "
                 "it can also cause render artifacts in rare circumstances. So if you experience "
                 "issues, you may want to turn this off.",
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )

        # --
        # Fixed Foveated Settings
        # --
        self.ffr = BaseModCfgSetting(
            key='fixedFoveated',
            name='Fixed Foveated Rendering',
            category='FFR',
            hidden=True,
            value=dict(),
            settings=list(),
        )
        self.ffrEnabled = BaseModCfgSetting(
            key='enabled',
            name='Enabled',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Enable fixed foveated rendering: continue rendering the center of the image at full"
                 " resolution, but drop the resolution when going to the edges of the image."
                 " There are four rings whose radii you can configure below. The inner ring/circle"
                 " is the area that's rendered at full resolution and reaches from the center to innerRadius."
                 " The second ring reaches from innerRadius to midRadius and is rendered at half resolution."
                 " The third ring reaches from midRadius to outerRadius and is rendered at 1/4th resolution."
                 " The final fourth ring reaches from outerRadius to the edges of the image and is rendered"
                 " at 1/16th resolution."
                 " Fixed foveated rendering is achieved with Variable Rate Shading. This technique is only"
                 " available on NVIDIA RTX and GTX 16xx cards.",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        # RSF additions
        self.ffrMethod = BaseModCfgSetting(
            key='method',
            name='Method',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Select the method to use for fixed foveated rendering. Available options: "
                 "vrs (Variable Rate Shading: This is only available on NVIDIA RTX and GTX 16xx cards). "
                 "rdm (Radial Density Mask: Compatible with any GPU. Hidden Mask will be disabled and "
                 "Upscaling wil be enabled)",
            value='vrs',
            settings=[{'value': 'vrs', 'name': 'Variable Rate Shading'},
                      {'value': 'rdm', 'name': 'Radial Density Mask'}]
        )
        self.ffrDynamic = BaseModCfgSetting(
            key='dynamic',
            name='Dynamic',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="FFR is applied only when needed to try to maintain at least target FPS",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.ffrTargetFps = BaseModCfgSetting(
            key='targetFPS',
            name='Target FPS',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Target FPS",
            value=60.0,
            settings=[{'settingType': 'range', 'min': 1.0, 'max': 999.00, 'step': 1.00}]
        )
        self.ffrMarginFps = BaseModCfgSetting(
            key='marginFPS',
            name='Margin FPS',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="FPS to start decreasing radius.",
            value=65.0,
            settings=[{'settingType': 'range', 'min': 1.0, 'max': 999.00, 'step': 1.00}]
        )
        self.ffrDynamicChangeRadius = BaseModCfgSetting(
            key='dynamicChangeRadius',
            name='Dynamic Change Radius',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Change default dynamic behavior: FFR is always enabled but dynamic mode changes radius dynamically",
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.ffrMinRadius = BaseModCfgSetting(
            key='minRadius',
            name='Min Radius',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="This is the minimal radius applied to Inner Radius when dynamic is enabled",
            value=0.30,
            settings=[{'settingType': 'range', 'min': 0.01, 'max': 1.00, 'step': 0.01}]
        )
        self.ffrDecreaseRadiusStep = BaseModCfgSetting(
            key='decreaseRadiusStep',
            name='Decrease Radius Step',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Decreased radius amount applied for each frametime check when needed",
            value=0.01,
            settings=[{'settingType': 'range', 'min': 0.01, 'max': 1.00, 'step': 0.01}]
        )
        self.ffrIncreaseRadiusStep = BaseModCfgSetting(
            key='increaseRadiusStep',
            name='Increase Radius Step',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Increased radius amount applied for each frametime check when needed",
            value=0.02,
            settings=[{'settingType': 'range', 'min': 0.01, 'max': 1.00, 'step': 0.01}]
        )
        # /RSF additions
        self.ffrInnerRadius = BaseModCfgSetting(
            key='innerRadius',
            name='Inner Radius',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Configure the end of the inner circle, which is the area that will be rendered at full resolution",
            value=0.50,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 1.00, 'step': 0.01}]
        )
        self.ffrMidRadius = BaseModCfgSetting(
            key='midRadius',
            name='Mid Radius',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Configure the end of the second ring, which will be rendered at half resolution",
            value=0.65,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 1.00, 'step': 0.01}]
        )
        self.ffrOuterRadius = BaseModCfgSetting(
            key='outerRadius',
            name='Outer Radius',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Configure the end of the third ring, which will be rendered at 1/4th resolution",
            value=0.80,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 2.00, 'step': 0.01}]
        )
        # RSF additions
        self.ffrEdgeRadius = BaseModCfgSetting(
            key='edgeRadius',
            name='Edge Radius',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Creates a Hidden Radial Mask. Available only in RDM mode",
            value=1.15,
            settings=[{'settingType': 'range', 'min': 0.10, 'max': 10.00, 'step': 0.10}]
        )
        self.ffrPreciseResolution = BaseModCfgSetting(
            key='preciseResolution',
            name='Precise Resolution',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Only applies FFR to target renders that matches equal resolution to final render. "
                 "Some games require to disable it.",
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.ffrRenderOnlyTarget = BaseModCfgSetting(
            key='renderOnlyTarget',
            name='Render Only Target',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="If not 0, FFR will be applied only to specific render target. Using a negative value will cause that "
                 "used target will be count from last. For example, -1 will be applied to the last target.",
            value=0,
            settings=[{'settingType': 'range', 'min': -999, 'max': 999, 'step': 1}]
        )
        self.ffrIgnoreFirstTargetRenders = BaseModCfgSetting(
            key='ignoreFirstTargetRenders',
            name='Ignore First Target Renders',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="FFR will not be applied to first and last specified target renders. Some games needs to skip some "
                 "target renders to avoid crashes. This is different from HRM option. Target renders from VSR mode "
                 "are different to RDM mode target renders.",
            value=0,
            settings=[{'settingType': 'range', 'min': -999, 'max': 999, 'step': 1}]
        )
        self.ffrIgnoreLastTargetRenders = BaseModCfgSetting(
            key='ignoreLastTargetRenders',
            name="Ignore Last Target Renders",
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="FFR will not be applied to first and last specified target renders. Some games needs to skip some "
                 "target renders to avoid crashes. This is different from HRM option. Target renders from VSR mode "
                 "are different to RDM mode target renders.",
            value=0,
            settings=[{'settingType': 'range', 'min': -999, 'max': 999, 'step': 1}]
        )
        # /RSF additions
        self.ffrFavorHorizontal = BaseModCfgSetting(
            key='favorHorizontal',
            name='Favor Horizontal',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="When reducing resolution, prefer to keep horizontal or vertical resolution",
            value=True,
            settings=[{'value': True, 'name': 'Horizontal'}, {'value': False, 'name': 'Vertical'}]
        )
        # RSF Additions to FFR
        self.ffrFastMode = BaseModCfgSetting(
            key='fastMode',
            name='Fast Mode',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="Fast mode: When game renders each eye separatelly, enabling this will save a bit of performance, "
                 "But overrideSingleEyeOrder will be ignored. Available only in VRS mode.",
            value=False,
            settings=[{'value': True, 'name': 'Enabled'}, {'value': False, 'name': 'Disabled'}]
        )
        self.ffrFastModeUsesHRMCount = BaseModCfgSetting(
            key='fastModeUsesHRMCount',
            name='Fast Mode Uses HRM Count',
            category=self.ffr.category,
            parent=self.ffr.key,
            desc="When fastMode is used, you can use HRM render targets counter instead default VRS counter. This will"
                 "force to enable HRM. Ignored target renders configuration will be used from hiddenMask section "
                 "instead.",
            value=False,
            settings=[{'value': True, 'name': 'Enabled'}, {'value': False, 'name': 'Disabled'}]
        )

        # --
        # HotKeys
        # --
        self.hotkeys = BaseModCfgSetting(
            key='hotkeys',
            name='Hotkeys',
            category='Hotkeys',
            hidden=True,
            value=dict(),
            settings=list(),
        )
        self.hkEnabled = BaseModCfgSetting(
            key='enabled',
            name='Enabled',
            category=self.hotkeys.category,
            parent=self.hotkeys.key,
            desc="Hotkeys allow you to modify certain settings of the mod on the fly, which is useful "
                 "for direct comparisons inside the headset. Note that any changes you make via hotkeys "
                 "are not currently persisted in the config file and will reset to the values in the "
                 "config file when you next launch the game.",
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.hkToggleDebugMode = BaseModCfgSetting(
            key='toggleDebugMode',
            name='Toggle Debug Mode',
            category=self.hotkeys.category,
            parent=self.hotkeys.key,
            desc='Toggles debugMode',
            value=["ctrl", "f1"],
            settings=[{'settingType': 'keyCombo'}]
        )
        self.hkCycleUpscalingMethod = BaseModCfgSetting(
            key='cycleUpscalingMethod',
            name='Cycle Upscaling Method',
            category=self.hotkeys.category,
            parent=self.hotkeys.key,
            desc='Cycle through the available upscaling methods',
            value=["ctrl", "f2"],
            settings=[{'settingType': 'keyCombo'}]
        )
        self.hkIncreaseUpscalingRadius = BaseModCfgSetting(
            key='increaseUpscalingRadius',
            name='Increase Upscaling Radius',
            category=self.hotkeys.category,
            parent=self.hotkeys.key,
            desc="Increase the upscaling circle's radius by 0.05",
            value=["ctrl", "f3"],
            settings=[{'settingType': 'keyCombo'}]
        )
        self.hkDecreaseUpscalingRadius = BaseModCfgSetting(
            key='decreaseUpscalingRadius',
            name='Decrease Upscaling Radius',
            category=self.hotkeys.category,
            parent=self.hotkeys.key,
            desc="Decrease the upscaling circle's radius by 0.05",
            value=["ctrl", "f4"],
            settings=[{'settingType': 'keyCombo'}]
        )
        self.hkIncreaseUpscalingSharpness = BaseModCfgSetting(
            key='increaseUpscalingSharpness',
            name='Increase Upscaling Sharpness',
            category=self.hotkeys.category,
            parent=self.hotkeys.key,
            desc="Increase the upscaling sharpness by 0.05",
            value=["ctrl", "f5"],
            settings=[{'settingType': 'keyCombo'}]
        )
        self.hkDecreaseUpscalingSharpness = BaseModCfgSetting(
            key='decreaseUpscalingSharpness',
            name='Decrease Upscaling Sharpness',
            category=self.hotkeys.category,
            parent=self.hotkeys.key,
            desc="Decrease the upscaling sharpness by 0.05",
            value=["ctrl", "f6"],
            settings=[{'settingType': 'keyCombo'}]
        )
        self.hkToggleUpscalingApplyMipBias = BaseModCfgSetting(
            key='toggleUpscalingApplyMipBias',
            name='Toggle Upscaling Apply Mip Bias',
            category=self.hotkeys.category,
            parent=self.hotkeys.key,
            desc="Toggle the application of MIP bias",
            value=["ctrl", "f7"],
            settings=[{'settingType': 'keyCombo'}]
        )
        self.hkCaptureOutput = BaseModCfgSetting(
            key='captureOutput',
            name='Capture Output',
            category=self.hotkeys.category,
            parent=self.hotkeys.key,
            desc="Take a screen grab of the final (post-processed, up-scaled) image. "
                 "The screen grab is stored as a dds file next to the DLL.",
            value=["ctrl", "f8"],
            settings=[{'settingType': 'keyCombo'}]
        )
        self.hkToggleFixedFoveated = BaseModCfgSetting(
            key='toggleFixedFoveated',
            name='Toggle Fixed Foveated',
            category=self.hotkeys.category,
            parent=self.hotkeys.key,
            desc="Toggle fixed foveated rendering",
            value=["alt", "f1"],
            settings=[{'settingType': 'keyCombo'}]
        )
        self.hkToggleFFRFavorHorizontal = BaseModCfgSetting(
            key='toggleFFRFavorHorizontal',
            name='Toggle FFR favor Horizontal',
            category=self.hotkeys.category,
            parent=self.hotkeys.key,
            desc="Toggle if you want to prefer horizontal or vertical resolution",
            value=["alt", "f2"],
            settings=[{'settingType': 'keyCombo'}]
        )

        # --
        # Debug mode
        # --
        self.debugMode = BaseModCfgSetting(
            key='debugMode',
            name='Debug Mode',
            category='Debug Mode',
            desc="Enabling debugMode will visualize the radius to which upscaling is applied (see above). "
                 "It will also output additional log messages and regularly report how much GPU frame time "
                 "the post-processing costs.",
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )

        super(VRPerfKitSettings, self).__init__()
