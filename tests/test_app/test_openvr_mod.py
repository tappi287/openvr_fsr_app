import json
import shutil
from pathlib import Path
from typing import Tuple

from app import app_fn, globals
from app.mod import BaseModType
from app.mod.fsr_mod import FsrMod


def test_get_fsr_dir_fn(app_settings, open_vr_fsr_dir):
    app_settings.mod_data_dirs[0] = open_vr_fsr_dir
    result = app_fn.get_mod_dir_fn(0)
    assert Path(result) == open_vr_fsr_dir


def test_set_fsr_dir_fn(app_settings, open_vr_fsr_test_mod_dir):
    result_dict = json.loads(app_fn.set_mod_dir_fn(open_vr_fsr_test_mod_dir.as_posix(), 0))

    assert result_dict['result'] is True
    assert Path(app_settings.mod_data_dirs[0]) == open_vr_fsr_test_mod_dir


def test_reset_fsr_dir_fn(app_settings, open_vr_fsr_dir, open_vr_fsr_test_mod_dir):
    app_settings.mod_data_dirs[0] = open_vr_fsr_dir
    json.loads(app_fn.set_mod_dir_fn(open_vr_fsr_test_mod_dir, 0))
    result_dict = json.loads(app_fn.set_mod_dir_fn('', 0))

    assert result_dict['result'] is True
    assert Path(app_settings.mod_data_dirs[0]) == open_vr_fsr_dir


def _create_test_output(output_path, open_vr_fsr_dir) -> Tuple[Path, Path]:
    test_openvr_dll = output_path / globals.OPEN_VR_DLL
    test_mod_cfg_path = output_path / globals.OPEN_VR_FSR_CFG
    # -- Create dummy file
    with open(test_openvr_dll, 'w') as f:
        f.write('')
    # -- Create default cfg file
    shutil.copy(open_vr_fsr_dir / globals.OPEN_VR_FSR_CFG, test_mod_cfg_path)
    return test_openvr_dll, test_mod_cfg_path


def test_update_mod_fn(test_app, output_path, open_vr_fsr_dir):
    mod_settings = test_app[FsrMod.VAR_NAMES['settings']]
    test_setting_key = 'enabled'
    test_setting_value = False

    # -- Create test output
    open_vr_dll_output, open_vr_mod_cfg_output = _create_test_output(output_path, open_vr_fsr_dir)

    # -- Manipulate a setting
    for s in mod_settings:
        if s.get('key') == test_setting_key:
            s['value'] = test_setting_value

    # -- Point to test output dir
    test_app['openVrDllPaths'] = [open_vr_dll_output.as_posix()]
    test_app['openVrDllPathsSelected'] = [open_vr_dll_output.as_posix()]

    # -- Test Fn
    result_dict = json.loads(app_fn.update_mod_fn(test_app, BaseModType.fsr, True))

    # -- Check returned manifest setting
    result_manifest_setting_value = None
    for s in result_dict['manifest'][FsrMod.VAR_NAMES['settings']]:
        if s.get('key') == test_setting_key:
            result_manifest_setting_value = s['value']

    # -- Read settings back
    mod = FsrMod(test_app)
    mod.update_from_disk()

    assert result_dict['result'] is True
    assert result_manifest_setting_value is test_setting_value
    assert mod.settings.get_option_by_key(test_setting_key).value is test_setting_value
    assert open_vr_mod_cfg_output.exists() is True

    # -- Cleanup output
    open_vr_dll_output.unlink()
    open_vr_mod_cfg_output.unlink()


def test_toggle_mod_install_fn(app_settings, test_app_writeable, open_vr_fsr_dir):
    # -- Use the actual mod to have a dll bigger than 0 bytes
    app_settings.mod_data_dirs[0] = open_vr_fsr_dir
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
