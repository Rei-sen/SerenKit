import types
import sys

from ..shared.profile import Profile
import pytest

from ..properties import model_settings
from .helpers import Collection


def test_get_modkit_collection_props_and_model_props_return_values():
    col = Collection([])
    mod = types.SimpleNamespace()
    model = types.SimpleNamespace(
        export_enabled=True, game_path="/game/path", assigned_profile="P")
    mod.model = model
    col.modkit = mod

    got = model_settings.get_modkit_collection_props(col)
    assert got is mod

    got_model = model_settings.get_model_props(col)
    assert got_model is model


def test_get_model_props_none_when_missing():
    col = Collection([])
    assert model_settings.get_model_props(col) is None


def test_get_game_path_uses_bpy_data_collections(monkeypatch):
    # Ensure bpy.data.collections mapping exists and is used
    fake_bpy = sys.modules.get("bpy")
    if fake_bpy is None:
        fake_bpy = types.ModuleType("bpy")
        sys.modules["bpy"] = fake_bpy

    # Create a collection with modkit.model providing game_path
    col = Collection([])
    mod = types.SimpleNamespace()
    model = types.SimpleNamespace(
        export_enabled=True, game_path="/my/game/path", assigned_profile="")
    mod.model = model
    col.modkit = mod

    # Inject into bpy.data.collections
    fake_data = types.SimpleNamespace()
    fake_data.collections = {"MyCol": col}
    fake_bpy.data = fake_data

    gp = model_settings.get_game_path("MyCol")
    assert gp == "/my/game/path"
