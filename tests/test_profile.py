
import json
import pytest

from ..shared.profile import Profile, get_loaded_profiles, get_profile_data, get_profile_items, _load_profiles_from_directory


def test_validate_variant_profile_accepts_minimal() -> None:
    data = {
        "profile_name": "test",
        "standard_materials": {},
        "groups": [],
    }

    # Should not raise (use Profile.from_dict validation)
    Profile.from_dict(data)


def test_validate_variant_profile_rejects_bad_structures() -> None:

    with pytest.raises(ValueError):
        Profile.from_dict(None)

    with pytest.raises(ValueError):
        Profile.from_dict({})

    # bad types for keys
    with pytest.raises(ValueError):
        Profile.from_dict({"profile_name": 123, "groups": []})


def test_load_variant_profile_and_dir(tmp_path) -> None:
    # create a minimal valid TOML file
    content = 'profile_name = "good"\nstandard_materials = {}\ngroups = []\n'
    (tmp_path / "good.toml").write_text(content)
    (tmp_path / "bad.toml").write_text("not toml")

    loaded = _load_profiles_from_directory(tmp_path)
    assert "good" in loaded

    # Should be a Profile with expected attributes
    profile = loaded["good"]
    assert isinstance(profile, Profile)
    assert profile.profile_name == "good"
    assert profile.groups == []

    # The invalid bad.toml should not appear in loaded
    assert "bad" not in loaded


def test_get_profile_items_and_loaded_profiles_mutation() -> None:
    # Ensure the module-level cache can be manipulated and returned
    cache = get_loaded_profiles()
    cache.clear()
    prof = Profile(profile_name="P1")
    # Insert a Profile instance into the module-level cache
    cache["P1"] = prof

    items = get_profile_items()
    assert any(item[0] == "P1" for item in items)
