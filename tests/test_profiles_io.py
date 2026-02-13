import json
import os
import tempfile

import pytest

from ..shared import profile


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def test_load_variant_profile_file_not_found():
    with pytest.raises(FileNotFoundError):
        profile.load_variant_profile("/non/existent/path.json")


def test_load_variant_profile_invalid_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{ invalid json }", encoding="utf-8")
    with pytest.raises(ValueError):
        profile.load_variant_profile(str(p))


def test_load_variant_profiles_from_dir_skips_invalid_and_loads_valid(tmp_path):
    valid = {"profile_name": "Good", "standard_materials": {}, "groups": [], "shpx": []}
    bad = "not a json"

    vp = tmp_path / "good.json"
    write_json(vp, valid)

    bp = tmp_path / "bad.json"
    bp.write_text(bad, encoding="utf-8")

    loaded = profile.load_variant_profiles_from_dir(str(tmp_path))
    assert "Good" in loaded
    assert isinstance(loaded["Good"], profile.VariantProfile)


def test_get_profile_items_and_data_roundtrip(tmp_path, monkeypatch):
    # Create one profile and inject into module loaded profiles
    p = profile.VariantProfile(profile_name="T", standard_materials=[], groups=[], shpx=[], export_aliases={})
    monkeypatch.setitem(profile._loaded_profiles, "T", p)

    items = profile.get_profile_items()
    assert any(i[0] == "T" for i in items)
    assert profile.get_profile_data("T") is p
