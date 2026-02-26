from typing import Any
from ..shared.profile import Profile, Group, GroupMode
from ..shared.variants import (
    filter_profile_shapekeys,
    generate_variant_combinations,
    name_variant,
)
from ..shared.export.shapekey_utils import collect_collection_shapekeys

from .helpers import Object, Collection


def test_generate_combinations_exclusive_and_optional() -> None:
    # two exclusive groups with 2 choices each, and two optional keys
    support_list: list[Any] = [
        Group(
            group_name="G1",
            mode=GroupMode.EXCLUSIVE,
            shapekeys=[("a1", "A1"), ("a2", "A2")],
        ),
        Group(
            group_name="G2",
            mode=GroupMode.EXCLUSIVE,
            shapekeys=[("b1", "B1"), ("b2", "B2")],
        ),
        Group(
            group_name="OPT",
            mode=GroupMode.OPTIONAL,
            shapekeys=[("o1", "O1"), ("o2", "O2")],
        ),
    ]

    # generate combinations using empty incompatibilities
    variants = generate_variant_combinations(support_list, {})
    # exclusive combinations: 2 * 2 = 4
    # optional subsets: 2^2 = 4
    assert len(variants) == 4 * 4

    # check structure: each variant is a list of tuples
    assert all(isinstance(v, list) for v in variants)
    assert all(
        all(isinstance(t, tuple) and len(t) == 2 for t in v) for v in variants
    )


def test_empty_variant_name() -> None:
    assert name_variant([]) == ""


def test_name_variant_tuple_and_legacy() -> None:
    variant: list[str] = ["Alpha", "Beta Two"]
    label = name_variant(variant)
    assert label == "Alpha - Beta Two"


def test_summarize_detects_existing_keys() -> None:
    profile_dict = {
        "profile_name": "Test",
        "standard_materials": {},
        "groups": [
            {
                "group_name": "G",
                "mode": "exclusive",
                "shapekeys": {"A": "A_out", "B": "B_out"},
            },
            {
                "group_name": "O",
                "mode": "optional",
                "shapekeys": {"C": "C", "D": "D"},
            },
        ],
    }
    profile = Profile.from_dict(profile_dict)
    shapekeys = {"A", "C"}

    support = filter_profile_shapekeys(shapekeys, profile)

    g = next((x for x in support if x.group_name == "G"), None)
    assert g
    assert ("A", "A_out") in g.shapekeys
    assert not any(b == "B" for b, _ in g.shapekeys)

    o = next((x for x in support if x.group_name == "O"), None)
    assert o
    assert ("C", "C") in o.shapekeys
    assert not any(b == "D" for b, _ in o.shapekeys)
