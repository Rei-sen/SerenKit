import pytest

from ..shared import profile


def make_group_dict(name="group1", mode="EXCLUSIVE", shapekeys=None):
    if shapekeys is None:
        shapekeys = {"A": "a", "B": "b"}
    return {"group_name": name, "mode": mode, "shapekeys": shapekeys}


def test_variant_group_from_dict_and_get_all_names():
    gdict = make_group_dict()
    vg = profile.Group.from_dict(gdict)

    assert vg.group_name == "group1"
    assert vg.mode == profile.GroupMode.EXCLUSIVE
    assert isinstance(vg.shapekeys, list)
    names = vg.get_all_shapekey_names()
    assert names == {"A", "B"}


def test_variant_group_validate_missing_keys_raises():
    bad = {"group_name": "g"}
    with pytest.raises(ValueError):
        profile.Group.from_dict(bad)


def test_variant_profile_from_dict_and_to_dict_roundtrip():
    data = {
        "profile_name": "P",
        "standard_materials": {"mat": "path/to/mat"},
        "groups": [make_group_dict()],
        "shpx": ["keep"],
        "export_aliases": {"X": "x_alias"},
    }

    vp = profile.Profile.from_dict(data)

    assert vp.profile_name == "P"
    assert any(m.name == "mat" and m.path == "path/to/mat" for m in vp.standard_materials)
    assert isinstance(vp.groups, list)
    assert vp.export_aliases.get("X") == "x_alias"


def test_variant_profile_validate_errors():
    with pytest.raises(ValueError):
        profile.Profile.from_dict(123)  # not a dict

    with pytest.raises(ValueError):
        profile.Profile.from_dict({})  # missing profile_name
