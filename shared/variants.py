"""Utilities for generating and naming exportable variants."""

from itertools import combinations, chain, product

from typing import List, Tuple, Iterable, Any, Optional, Iterator

from .profile import (
    Group,
    GroupMode,
    IncompatibilityMap,
    NamePair,
    Profile,
)


def _powerset(iterable: Iterable[Any]) -> Iterator[Tuple[Any, ...]]:
    """Return an iterator over all subsets (the powerset) of `iterable`."""
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def filter_profile_shapekeys(
    shapekeys: set[str], profile: Profile
) -> List[Group]:
    """Build a reduced group list for a collection from a VariantProfile."""

    reduced_groups: List[Group] = []

    for group in profile.groups:
        detected = [
            (bname, ename)
            for bname, ename in group.shapekeys
            if bname in shapekeys
        ]
        reduced_groups.append(
            Group(
                group_name=group.group_name, mode=group.mode, shapekeys=detected
            )
        )

    return reduced_groups


def _is_valid_variant_combo(
    variant_combo: Iterable[NamePair], incompatibilities: IncompatibilityMap
) -> bool:
    """Check if a variant combo is valid according to the profile rules."""

    combo_shapes = {shape for shape, _ in variant_combo}

    for shape in combo_shapes:
        if shape in incompatibilities and any(
            inc in combo_shapes for inc in incompatibilities[shape]
        ):
            return False
    return True


def _filter_compatible_shapekeys(
    variants: Iterable[Iterable[NamePair]],
    incompatibilities: IncompatibilityMap,
) -> List[List[NamePair]]:
    """Remove shapekeys from the set that are incompatible with the profile."""
    valid_combos = []
    for combo in variants:
        if _is_valid_variant_combo(combo, incompatibilities):
            valid_combos.append(list(combo))
    return valid_combos


def generate_variant_combinations(
    support_list: List[Group], incompatibilities: IncompatibilityMap
) -> List[List[NamePair]]:
    """Generate bakeable variant combinations from support groups."""

    exclusive_groups: List[List[NamePair]] = []
    optional_keys: List[NamePair] = []

    for g in support_list:
        sk_list = g.shapekeys
        mode = g.mode

        if not sk_list:
            continue

        if mode == GroupMode.EXCLUSIVE:
            exclusive_groups.append(sk_list)
        else:
            optional_keys.extend(sk_list)

    optional_subsets = list(_powerset(optional_keys)) if optional_keys else [()]

    variants: List[List[NamePair]] = []

    if exclusive_groups:
        for excl_choice in product(*exclusive_groups):
            base = list(excl_choice)
            for opt_subset in optional_subsets:
                variants.append(base + list(opt_subset))
    else:
        for opt_subset in optional_subsets:
            variants.append(list(opt_subset))

    if variants == []:
        variants.append([])

    return _filter_compatible_shapekeys(variants, incompatibilities)


def name_variant(variant_combo: List[str], separator: str = " - ") -> str:
    """Return a label for a variant combo by joining export names."""
    return separator.join(variant_combo)


def detect_export_alias(
    variant_combo: List[str], profile: Profile
) -> Tuple[Optional[str], List[str]]:
    """Detect and return a single export alias override and remaining items."""
    alias_map = profile.export_aliases

    if alias_map:
        for idx, name in enumerate(variant_combo):
            if name in alias_map:
                override = alias_map[name]
                remaining = variant_combo[:idx] + variant_combo[idx + 1 :]
                return override, remaining

    return None, variant_combo
