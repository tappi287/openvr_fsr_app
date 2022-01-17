import json
from pathlib import Path

from app import app_fn, globals
from app.openvr_mod import OpenVRModType
from app.vrperfkit_mod import VRPerfKitMod


def test_update_mod_fn(test_app, output_path, vrperfkit_dll_output, vrperfkit_mod_cfg_output):
    mod_settings = test_app[VRPerfKitMod.VAR_NAMES['settings']]
    test_setting_key = 'method'
    test_setting_parent_key = 'upscaling'
    test_setting_value = 'nis'

    # -- Manipulate a setting
    for s in mod_settings:
        if s.get('key') == test_setting_key:
            s['value'] = test_setting_value

    # -- Point to test output dir
    test_app['executablePaths'] = [vrperfkit_dll_output.as_posix()]
    test_app['executablePathsSelected'] = [vrperfkit_dll_output.as_posix()]

    # -- Test Fn
    result_dict = json.loads(app_fn.update_mod_fn(test_app, OpenVRModType.vrp, True))

    # -- Check returned manifest setting
    result_manifest_setting_value = None
    for s in result_dict['manifest'][VRPerfKitMod.VAR_NAMES['settings']]:
        if s.get('key') == test_setting_key:
            result_manifest_setting_value = s['value']

    # -- Read settings back
    mod = VRPerfKitMod(test_app)
    mod.update_from_disk()

    assert result_dict['result'] is True
    assert result_manifest_setting_value == test_setting_value

    val = mod.settings._get_option_by_key(test_setting_key, test_setting_parent_key).value
    assert val == test_setting_value

    # -- Cleanup output
    vrperfkit_dll_output.unlink()
    vrperfkit_mod_cfg_output.unlink()


def test_toggle_mod_install_fn(test_app_writeable):
    output_dlls = test_app_writeable['openVrDllPaths']

    # -- Test OpenVR Mod installation
    result_dict = json.loads(app_fn.toggle_mod_install_fn(test_app_writeable, 0))
    assert result_dict['result'] is True

    for written_dll in output_dlls:
        # -- Test dll's have size 0, installed dll's should be bigger than a few bytes
        assert Path(written_dll).stat().st_size > 50

        # -- Test backup files created
        back_up_file = Path(written_dll).with_name(f'{globals.OPEN_VR_DLL[:-4]}.orig.dll')
        assert back_up_file.exists() is True

        # -- Test config file written
        cfg_file = Path(written_dll).parent / globals.OPEN_VR_FSR_CFG
        assert cfg_file.exists() is True

    # -- Test OpenVR Mod uninstallation
    result_dict = json.loads(app_fn.toggle_mod_install_fn(test_app_writeable, 0))
    assert result_dict['result'] is True

    for written_dll in output_dlls:
        # -- Test original dll restored
        assert Path(written_dll).stat().st_size < 50

        # -- Test backup file removed
        back_up_file = Path(written_dll).with_name(f'{globals.OPEN_VR_DLL[:-4]}.orig.dll')
        assert back_up_file.exists() is False

        # -- Test config file removed
        cfg_file = Path(written_dll).parent / globals.OPEN_VR_FSR_CFG
        assert cfg_file.exists() is False
