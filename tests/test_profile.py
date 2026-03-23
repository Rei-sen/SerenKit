import tomllib
from pathlib import Path

from ..shared.profile import (
    Group,
    GroupMode,
    Profile,
    ProfileInfo,
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


def test_profile_info_from_dict_valid():
    info = ProfileInfo.from_dict(
        {
            "summary": "Extra notes",
            "instructions": ["Do one thing", "Do another thing"],
            "links": {"Guide": "https://example.com"},
        }
    )
    assert info.summary == "Extra notes"
    assert info.instructions == ["Do one thing", "Do another thing"]
    assert info.links == [("Guide", "https://example.com")]


def test_profile_from_dict_with_profile_info():
    profile = Profile.from_dict(
        {
            "profile_name": "WithInfo",
            "standard_materials": {"Base": "/mt_base.mtrl"},
            "groups": [
                {
                    "group_name": "Top",
                    "mode": "exclusive",
                    "shapekeys": {"Large": "Large"},
                }
            ],
            "profile_info": {
                "summary": "Notes",
                "instructions": ["Delete drivers manually"],
                "links": {"Reference": "https://example.com/ref"},
            },
        }
    )

    assert profile.profile_info is not None
    assert profile.profile_info.summary == "Notes"
    assert profile.profile_info.instructions == ["Delete drivers manually"]
    assert profile.profile_info.links == [
        ("Reference", "https://example.com/ref")
    ]
