import sys
import types
import pytest

from ..shared import variants, profile


def test_generate_variant_combinations_and_powerset():
    g1 = profile.Group(
        group_name="g1", mode=profile.GroupMode.EXCLUSIVE, shapekeys=[("A", "a"), ("B", "b")]
    )
    g2 = profile.Group(
        group_name="g2", mode=profile.GroupMode.OPTIONAL, shapekeys=[("C", "c")]
    )

    support = [g1, g2]
    combos = variants.generate_variant_combinations(support, {})

    # exclusive group: 2 choices, optional keys: 1 -> total 2 * 2 = 4
    assert len(combos) == 4
    assert any(("A", "a") in combo for combo in combos)
    assert any(("B", "b") in combo for combo in combos)


def test_count_variants_from_support():
    g1 = profile.Group(
        group_name="g1", mode=profile.GroupMode.EXCLUSIVE, shapekeys=[("A", "a")]
    )
    g2 = profile.Group(
        group_name="g2", mode=profile.GroupMode.OPTIONAL, shapekeys=[("B", "b"), ("C", "c")]
    )

    combos = variants.generate_variant_combinations([g1, g2], {})
    assert len(combos) == 1 * (2 ** 2)


def test_detect_export_alias_override():
    vp = profile.Profile(
        profile_name="P", export_aliases={"x": "X_ALIAS"}
    )
    override, remaining = variants.detect_export_alias(["a", "x", "b"], vp)
    assert override == "X_ALIAS"
    assert "x" not in remaining
