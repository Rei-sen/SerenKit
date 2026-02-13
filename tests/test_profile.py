
import json
import pytest

from ..shared.profile import VariantProfile, get_loaded_profiles, get_profile_data, get_profile_items, load_variant_profiles_from_dir


def test_validate_variant_profile_accepts_minimal() -> None:
    data = {
        "profile_name": "test",
        "standard_materials": {},
        "groups": [],
    }

    # Should not raise (use VariantProfile validation)
    VariantProfile.validate_dict(data)


def test_validate_variant_profile_rejects_bad_structures() -> None:

    with pytest.raises(ValueError):
        VariantProfile.validate_dict(None)

    with pytest.raises(ValueError):
        VariantProfile.validate_dict({})

    # bad types for keys
    with pytest.raises(ValueError):
        VariantProfile.validate_dict({"profile_name": 123, "groups": []})


def test_load_variant_profile_and_dir(tmp_path) -> None:
    good = {"profile_name": "good", "groups": []}

    (tmp_path / "good.json").write_text(json.dumps(good))
    (tmp_path / "bad.json").write_text("{ invalid json }")

    loaded = load_variant_profiles_from_dir(str(tmp_path))
    assert "good" in loaded

    # Should be a VariantProfile with expected attributes
    profile = loaded["good"]
    assert isinstance(profile, VariantProfile)
    assert profile.profile_name == "good"
    assert profile.groups == []

    # The invalid bad.json should not appear in loaded
    assert "bad" not in loaded


def test_get_profile_items_and_loaded_profiles_mutation() -> None:
    # Ensure the module-level cache can be manipulated and returned
    cache = get_loaded_profiles()
    cache.clear()
    prof: VariantProfile = {"profile_name": "P1",
                            "standard_materials": {}, "groups": []}
    # Insert a VariantProfile instance into the module-level cache
    cache["P1"] = prof

    items = get_profile_items()
    assert any(item[0] == "P1" for item in items)
