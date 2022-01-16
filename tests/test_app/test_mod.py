import json
from pathlib import Path

from app import app_fn


def test_get_fsr_dir_fn(open_vr_fsr_dir):
    result = app_fn.get_fsr_dir_fn()
    assert Path(result) == open_vr_fsr_dir


def test_set_fsr_dir_fn(app_settings, open_vr_fsr_test_dir):
    result_dict = json.loads(app_fn.set_fsr_dir_fn(open_vr_fsr_test_dir.as_posix()))

    assert result_dict['result'] is True
    assert Path(app_settings.openvr_fsr_dir) == open_vr_fsr_test_dir


def test_update_mod_fn(test_app):
    result_dict = json.loads(app_fn.update_mod_fn(test_app, 0))
    assert result_dict['result'] is True
