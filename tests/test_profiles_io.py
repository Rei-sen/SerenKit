import json
import os
import tempfile
from pathlib import Path

import pytest

from ..shared import profile


def write_toml(path, data):
    # write a minimal TOML mapping using simple key=value pairs for this test
    # For nested structures we just write a small valid TOML using toml-style strings
    with open(path, "w", encoding="utf-8") as f:
        # Use a very small manual conversion for the limited test payload
        f.write(f'profile_name = "{data["profile_name"]}"\n')


def test_load_variant_profile_file_not_found():
    with pytest.raises(FileNotFoundError):
        profile._load_profile(Path("/non/existent/path.toml"))


def test_load_variant_profile_invalid_toml(tmp_path):
    p = tmp_path / "bad.toml"
    p.write_text("not = = toml", encoding="utf-8")
    with pytest.raises(ValueError):
        profile._load_profile(p)


def test_load_variant_profiles_from_dir_skips_invalid_and_loads_valid(tmp_path):
    # create a very simple valid TOML file that Profile.from_dict can parse
    content = 'profile_name = "Good"\nstandard_materials = {}\ngroups = []\n'
    vp = tmp_path / "good.toml"
    vp.write_text(content, encoding="utf-8")

    bp = tmp_path / "bad.toml"
    bp.write_text("not toml", encoding="utf-8")

    loaded = profile._load_profiles_from_directory(tmp_path)
    assert "Good" in loaded
    assert isinstance(loaded["Good"], profile.Profile)


def test_get_profile_items_and_data_roundtrip(tmp_path, monkeypatch):
    # Create one profile and inject into module loaded profiles
    p = profile.Profile(profile_name="T")
    monkeypatch.setitem(profile._profiles, "T", p)

    items = profile.get_profile_items()
    assert any(i[0] == "T" for i in items)
    assert profile.get_profile_data("T") is p
