import json
import shutil
from pathlib import Path

import app.mod
from app import app_fn, globals
from app.app_settings import AppSettings
from app.cfg.cfg_file_handler import ModCfgYamlHandler
from app.mod import BaseModType, VRPerfKitMod
from conftest import create_manipulated_settings


def _create_test_output(output_path, vrperfkit_dir):
    test_dxgi_dll = output_path / globals.DXGI_DLL
    # -- Create dummy file
    with open(test_dxgi_dll, 'w') as f:
        f.write('')
    test_mod_yml_path = output_path / globals.VRPERFKIT_CFG
    # -- Create default cfg file
    shutil.copy(vrperfkit_dir / globals.VRPERFKIT_CFG, test_mod_yml_path)
    return test_dxgi_dll, test_mod_yml_path


def test_update_mod_fn(test_app, output_path, vrperfkit_dir):
    # -- Create test output
    _vrp_dll_out, _vrp_mod_cfg_out = _create_test_output(output_path, vrperfkit_dir)

    # -- Update Test App
    test_app['executablePaths'] = [str(_vrp_dll_out.parent / 'SomeNoneExistingBinary.exe')]
    # test_app['executablePathsSelected'] = test_app['executablePaths']

    # -- Create Test Settings
    test_set = ([('method', 'upscaling'), ('renderScale', 'upscaling'), ('debugMode', None),
                 ('cycleUpscalingMethod', 'hotkeys')],
                ['nis', 2.50, True, ["shift", "l"]])
    test_app, test_settings = create_manipulated_settings(test_app, test_set, app.mod.get_mod(dict(), BaseModType.vrp))

    # -- Test Fn
    result_dict = json.loads(app_fn.update_mod_fn(test_app, BaseModType.vrp, True))

    # -- Reset settings and read settings back
    test_app.pop(VRPerfKitMod.VAR_NAMES['settings'])
    mod = VRPerfKitMod(test_app)
    mod.update_from_disk()

    # -- Results
    assert result_dict['result'] is True

    for _test_s in test_settings:
        # -- Verify Mod Settings object updated correctly
        _key, _parent, _test_value = _test_s['key'], _test_s['parent'], _test_s['value']
        assert mod.settings.get_option_by_key(_key, _parent).value == _test_value

        # -- Verify Result Manifest updated correctly
        for setting in result_dict['manifest'][VRPerfKitMod.VAR_NAMES['settings']]:
            if setting.get('key') == _key and setting.get('parent') == _parent:
                assert setting.get('value') == _test_value

    # -- Verify written file matches settings
    for exe_loc in test_app['executablePathsSelected']:
        cfg = Path(exe_loc).parent / mod.settings.CFG_FILE
        yml_data = ModCfgYamlHandler.read_cfg(mod.settings, cfg)
        for _test_s in test_settings:
            _key, _parent, _test_value = _test_s['key'], _test_s['parent'], _test_s['value']
            if _test_s.get('parent') is not None:
                assert yml_data[_parent][_key] == _test_value
            else:
                assert yml_data[_key] == _test_value

    # -- Cleanup output
    _vrp_dll_out.unlink()
    _vrp_mod_cfg_out.unlink()


def test_toggle_mod_install_fn(test_app_writeable):
    exe_locations = test_app_writeable['executablePaths']

    # -- Test VRP Mod installation
    result_dict = json.loads(app_fn.toggle_mod_install_fn(test_app_writeable, BaseModType.vrp))
    assert result_dict['result'] is True
    mod = VRPerfKitMod(test_app_writeable)

    # -- Verify version
    mod.update_from_disk()
    assert mod.manifest[VRPerfKitMod.VAR_NAMES['version']] == AppSettings.current_vrperfkit_version

    # -- Verify files written
    for exe_loc in exe_locations:
        written_dll = Path(exe_loc).parent / mod.DLL_NAME
        # -- Test dll's have size 0, installed dll's should be bigger than a few bytes
        assert written_dll.stat().st_size > 50

        # -- Test config file written
        cfg_file = written_dll.parent / globals.VRPERFKIT_CFG
        assert cfg_file.exists() is True

    # -- Test VRP Mod uninstallation
    result_dict = json.loads(app_fn.toggle_mod_install_fn(test_app_writeable, BaseModType.vrp))
    assert result_dict['result'] is True

    # -- Verify no version
    mod = VRPerfKitMod(test_app_writeable)
    mod.update_from_disk()
    assert mod.manifest[VRPerfKitMod.VAR_NAMES['version']] == str()

    # -- Verify files removed
    for exe_loc in exe_locations:
        written_dll = Path(exe_loc).parent / mod.DLL_NAME
        # -- Test dll's should be removed
        assert written_dll.exists() is False

        # -- Test config file removed
        cfg_file = written_dll.parent / globals.VRPERFKIT_CFG
        assert cfg_file.exists() is False


def test_reset_mod_settings_fn(test_app_writeable):
    test_set = ([('method', 'upscaling'), ('renderScale', 'upscaling'), ('debugMode', None),
                 ('cycleUpscalingMethod', 'hotkeys')],
                ['nis', 2.50, True, ["shift", "l"]])
    test_app, test_settings = create_manipulated_settings(test_app_writeable, test_set,
                                                          app.mod.get_mod(dict(), BaseModType.vrp))

    mod = app.mod.get_mod(test_app, BaseModType.vrp)
    result_dict = json.loads(app_fn.reset_mod_settings_fn(mod.manifest, BaseModType.vrp))
    assert result_dict['result'] is True

    manifest = result_dict['manifest']
    mod_settings = manifest[mod.VAR_NAMES['settings']]

    mod = app.mod.get_mod(dict(), BaseModType.vrp)
    for _s in mod_settings:
        for _test_s in test_settings:
            if _s.get('key') == _test_s.get('key') and _s.get('parent') == _test_s.get('parent'):
                # -- Test reset settings returning actual settings
                assert _s.get('value') != _test_s.get('value')

                # -- Test reset settings returning default settings
                option = mod.settings.get_option_by_key(_s.get('key'), _s.get('parent'))
                assert _s.get('value') == option.value

    # -- Test reset settings written to disk
    mod = app.mod.get_mod(test_app, BaseModType.vrp)
    mod.update_from_disk()
    for _test_s in test_settings:
        option = mod.settings.get_option_by_key(_test_s.get('key'), _test_s.get('parent'))
        assert option.value != _test_s.get('value')