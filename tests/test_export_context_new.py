import pytest

from ..shared import export_context
from ..shared import profile
from .helpers import Model, Collection


def make_collection_with_model(export_enabled=False, game_path="", assigned_profile=""):
    col = Collection(all_objects=[])
    col.modkit = type("M", (), {})()
    col.modkit.model = Model(export_enabled=export_enabled,
                             game_path=game_path, assigned_profile=assigned_profile)
    return col


def test_validate_export_readiness_not_enabled():
    col = make_collection_with_model(export_enabled=False)
    ok, msg = export_context.validate_export_readiness(col)
    assert not ok
    assert "not enabled" in msg.lower()


def test_validate_export_readiness_missing_game_path():
    col = make_collection_with_model(
        export_enabled=True, game_path="", assigned_profile="P")
    ok, msg = export_context.validate_export_readiness(col)
    assert not ok
    assert "no game_path" in msg.lower()


def test_validate_export_readiness_no_assigned_profile():
    col = make_collection_with_model(
        export_enabled=True, game_path="path", assigned_profile="")
    ok, msg = export_context.validate_export_readiness(col)
    assert not ok
    assert "no variant profile assigned" in msg.lower()


def test_validate_export_readiness_profile_not_loaded():
    col = make_collection_with_model(
        export_enabled=True, game_path="path", assigned_profile="X")
    ok, msg = export_context.validate_export_readiness(col)
    assert not ok
    assert "not loaded" in msg.lower()


def test_validate_export_readiness_success():
    col = make_collection_with_model(
        export_enabled=True, game_path="path", assigned_profile="T")
    p = profile.Profile(profile_name="T")
    profile._profiles["T"] = p

    ok, msg = export_context.validate_export_readiness(col)
    assert ok
    assert msg is None
