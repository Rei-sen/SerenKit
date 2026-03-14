from ..shared import variants
from ..shared.profile import Profile, Group, GroupMode


def test_generate_variant_combinations_exclusive_and_optional():
    g1 = Group(
        group_name="G1",
        mode=GroupMode.EXCLUSIVE,
        shapekeys=[("A", "A"), ("B", "B")],
    )
    g2 = Group(group_name="G2", mode=GroupMode.OPTIONAL, shapekeys=[("C", "C")])

    variants_list = variants.generate_variant_combinations(
        [g1, g2], incompatibilities={}
    )

    # exclusive choices (A or B) combined with optional C (present or not)
    assert len(variants_list) == 4
    # ensure at least one combo contains A and one contains B
    assert any(("A", "A") in combo for combo in variants_list)
    assert any(("B", "B") in combo for combo in variants_list)


def test_name_alias_and_disabled_helpers():
    prof = Profile(profile_name="P", groups=[], export_aliases={"Alt": "Alias"})

    name = variants.name_variant(["one", "two"])
    assert name == "one - two"

    alias, remaining = variants.detect_export_alias(["Alt", "X"], prof)
    assert alias == "Alias"
    assert remaining == ["X"]

    sks = [("A", "A"), ("B", "B")]
    filtered = variants.remove_disabled_shapekeys(sks, {"B"})
    assert filtered == [("A", "A")]


def test_generate_variant_combos_for_export_end_to_end():
    prof = Profile(
        profile_name="P",
        groups=[
            Group(
                group_name="G",
                mode=GroupMode.EXCLUSIVE,
                shapekeys=[("A", "A"), ("B", "B")],
            )
        ],
        incompatibilities={},
    )

    combos = variants.generate_variant_combos_for_export(
        prof, {"A", "B"}, disabled_shapes=set()
    )
    # Expect two exclusive choices
    assert len(combos) == 2


def test_incompatibility_filters_out_invalid_combos():
    g1 = Group(
        group_name="G1", mode=GroupMode.EXCLUSIVE, shapekeys=[("A", "A")]
    )
    g2 = Group(group_name="G2", mode=GroupMode.OPTIONAL, shapekeys=[("C", "C")])

    # declare A incompatible with C
    incompat = {"A": ["C"]}

    combos = variants.generate_variant_combinations(
        [g1, g2], incompatibilities=incompat
    )

    # ensure no combo contains both A and C
    for combo in combos:
        names = {pair[0] for pair in combo}
        assert not ("A" in names and "C" in names)
