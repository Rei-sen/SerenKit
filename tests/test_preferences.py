import types
import subprocess
import os


def test_reload_profiles_success(monkeypatch):
    import bpy
    # ensure AddonPreferences exists on the bpy.types shim
    setattr(bpy.types, 'AddonPreferences', type('AddonPreferences', (), {}))
    from .. import preferences as prefs

    # monkeypatch load_profiles and get_loaded_profiles
    monkeypatch.setattr(prefs, 'load_profiles', lambda: None)
    monkeypatch.setattr(prefs, 'get_loaded_profiles', lambda: {'A': 1, 'B': 2})

    op = prefs.MODKIT_OT_reload_profiles()

    def report(self, categories, message):
        self._last_report = (categories, message)

    import types as _types
    op.report = _types.MethodType(report, op)

    res = op.execute(None)
    assert res == {'FINISHED'}
    assert 'Reloaded 2 variant profiles' in op._last_report[1]


def test_reload_profiles_failure(monkeypatch):
    import bpy
    setattr(bpy.types, 'AddonPreferences', type('AddonPreferences', (), {}))
    from .. import preferences as prefs

    def bad_reload():
        raise RuntimeError('boom')

    monkeypatch.setattr(prefs, 'load_profiles', bad_reload)

    op = prefs.MODKIT_OT_reload_profiles()

    def report(self, categories, message):
        self._last_report = (categories, message)

    import types as _types
    op.report = _types.MethodType(report, op)

    res = op.execute(None)
    assert res == {'CANCELLED'}
    assert 'Failed to reload profiles' in op._last_report[1]


def test_open_profiles_folder_windows_and_linux(monkeypatch, tmp_path):
    import bpy
    setattr(bpy.types, 'AddonPreferences', type('AddonPreferences', (), {}))
    from .. import preferences as prefs

    # return tmp path as builtin profiles dir
    monkeypatch.setattr(prefs, 'get_profiles_dir', lambda: tmp_path)

    # Windows path
    monkeypatch.setattr(prefs.platform, 'system', lambda: 'Windows')

    started = {}

    def fake_startfile(path):
        started['called'] = path

    monkeypatch.setattr(prefs.os, 'startfile', fake_startfile, raising=False)

    op = prefs.MODKIT_OT_open_profiles_folder()

    def report(self, categories, message):
        self._last_report = (categories, message)

    import types as _types
    op.report = _types.MethodType(report, op)

    res = op.execute(None)
    assert res == {'FINISHED'}
    assert 'Opened' in op._last_report[1]
    assert str(tmp_path) in started['called']

    # Linux branch (subprocess.Popen)
    monkeypatch.setattr(prefs.platform, 'system', lambda: 'Linux')

    calls = {}

    class FakePopen:
        def __init__(self, args):
            calls['args'] = args

    monkeypatch.setattr(prefs.subprocess, 'Popen', FakePopen)

    op2 = prefs.MODKIT_OT_open_profiles_folder()
    op2.report = _types.MethodType(report, op2)
    res2 = op2.execute(None)
    assert res2 == {'FINISHED'}
    assert 'xdg-open' in calls['args'][0]
