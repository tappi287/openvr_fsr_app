from pathlib import WindowsPath

from app.mod import BaseModType
from app.mod.mod_utils import update_mod_data_dirs
from app.globals import get_data_dir


def test_get_mod_data_dirs(app_settings, open_vr_fsr_test_mod_dir):
    test_dirs = dict()
    for mod_type in BaseModType.mod_types.keys():
        data_dir_name = BaseModType.mod_data_dir_names[mod_type]
        test_dirs[mod_type] = str(WindowsPath(get_data_dir() / data_dir_name))

    # -- Test default paths
    mod_dirs = update_mod_data_dirs()
    for key, value in mod_dirs.items():
        assert test_dirs[key] == value

    # -- Test custom path
    test_dir = str(WindowsPath(open_vr_fsr_test_mod_dir))
    app_settings.mod_data_dirs[0] = test_dir
    mod_dirs = update_mod_data_dirs()
    assert mod_dirs[0 == test_dir]
