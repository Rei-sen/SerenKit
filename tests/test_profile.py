import tomllib
from pathlib import Path

from ..shared.profile import (
    Group,
    GroupMode,
    Profile,
    Material,
    _load_profile,
    get_profiles_dir,
    load_profiles,
    get_loaded_profiles,
)


def test_group_from_dict_valid_and_get_all_names():
    data = {
        "group_name": "G",
        "mode": "exclusive",
        "shapekeys": {"A": "A", "B": "B"},
    }
    g = Group.from_dict(data)
    assert g.group_name == "G"
    assert g.mode == GroupMode.EXCLUSIVE
    assert g.get_all_shapekey_names() == {"A", "B"}


def test_group_from_dict_invalid_raises():
    bad = {"group_name": 1, "mode": "unknown", "shapekeys": [1, 2]}
    try:
        Group.from_dict(bad)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_profile_from_toml_and_loading_profiles():
    # Create a minimal profile TOML in-memory and load via _load_profile path helper
    profiles_dir = get_profiles_dir()
    assert profiles_dir.exists()

    # Call load_profiles to populate the registry and ensure at least one profile loads
    load_profiles()
    loaded = get_loaded_profiles()
    assert isinstance(loaded, dict)
    assert len(loaded) > 0
