import sys
import types
import pytest

from ..shared import variants, profile


def test_generate_variant_combinations_and_powerset():
    g1 = profile.VariantGroup(group_name="g1", mode="exclusive", shapekeys=[
                              ("A", "a"), ("B", "b")])
    g2 = profile.VariantGroup(
        group_name="g2", mode="optional", shapekeys=[("C", "c")])

    support = [g1, g2]
    combos = variants.generate_variant_combinations(support)

    # exclusive group: 2 choices, optional keys: 1 -> total 2 * 2 = 4
    assert len(combos) == 4
    assert any(("A", "a") in combo for combo in combos)
    assert any(("B", "b") in combo for combo in combos)


def test_count_variants_from_support():
    g1 = profile.VariantGroup(
        group_name="g1", mode="exclusive", shapekeys=[("A", "a")])
    g2 = profile.VariantGroup(group_name="g2", mode="optional", shapekeys=[
                              ("B", "b"), ("C", "c")])

    assert variants.count_variants_from_support([g1, g2]) == 1 * (2 ** 2)


def test_detect_export_alias_override():
    vp = profile.VariantProfile(
        profile_name="P", export_aliases={"x": "X_ALIAS"})
    override, remaining = variants.detect_export_alias_override(
        ["a", "x", "b"], vp)
    assert override == "X_ALIAS"
    assert "x" not in remaining
