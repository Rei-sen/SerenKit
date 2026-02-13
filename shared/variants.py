"""Utilities for generating and naming exportable variants."""

from bpy.types import Collection

from itertools import combinations, chain, product

from typing import List, Tuple, Iterable, Any, Optional, Iterator

from .export.shapekey_utils import collect_collection_shapekeys
from .profile import NamePair, VariantProfile, VariantGroup, get_profile_data

from ..properties.model_settings import get_modkit_collection_props


def summarize_variant_support_from_profile(
    shapekeys: set[str],
    profile: VariantProfile
) -> List[VariantGroup]:
    """Build a reduced group list for a collection from a VariantProfile."""

    reduced_groups: List[VariantGroup] = []

    for group in profile.groups:
        detected = [(bname, ename)
                    for bname, ename in group.shapekeys if bname in shapekeys]
        reduced_groups.append(VariantGroup(
            group_name=group.group_name,
            mode=group.mode,
            shapekeys=detected
        ))

    return reduced_groups


def powerset(iterable: Iterable[Any]) -> Iterator[Tuple[Any, ...]]:
    """Return an iterator over all subsets (the powerset) of `iterable`."""
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def generate_variant_combinations(
    support_list: List[VariantGroup]
) -> List[List[NamePair]]:
    """Generate bakeable variant combinations from support groups."""

    exclusive_groups: List[List[NamePair]] = []
    optional_keys: List[NamePair] = []

    for g in support_list:
        sk_list = list(g.shapekeys)
        mode = g.mode

        if not sk_list:
            continue

        if mode == "exclusive":
            exclusive_groups.append(sk_list)
        else:
            optional_keys.extend(sk_list)

    optional_subsets = list(powerset(optional_keys)) if optional_keys else [()]

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
    return variants


def name_variant(variant_combo: List[str], separator: str = " - ") -> str:
    """Return a label for a variant combo by joining export names."""
    return separator.join(variant_combo)


def detect_export_alias_override(
    variant_combo: List[str],
    profile: Optional[VariantProfile] = None
) -> Tuple[Optional[str], List[str]]:
    """Detect and return a single export alias override and remaining items."""
    # Use only per-profile aliases. If none provided, no override.
    if profile and profile.export_aliases:
        alias_map = profile.export_aliases
        for idx, name in enumerate(variant_combo):
            if name in alias_map:
                override = alias_map[name]
                remaining = variant_combo[:idx] + variant_combo[idx+1:]
                return override, remaining

    return None, variant_combo


def count_variants_from_support(support_list: List[VariantGroup]) -> int:
    """Count variant combinations from a support map without generating them."""

    exclusive_product = 1
    optional_count = 0

    for g in support_list:
        sk_list = list(g.shapekeys)
        if not sk_list:
            continue

        mode = g.mode
        if mode == "exclusive":
            exclusive_product *= max(1, len(sk_list))
        else:
            optional_count += len(sk_list)

    return exclusive_product * (2 ** optional_count)


def count_variants_for_collection(collection: Collection) -> int:
    """Count variant combinations for a collection."""

    col_props = get_modkit_collection_props(collection)
    model = col_props.model if col_props else None
    profile_name = model.assigned_profile if model else ""
    profile = get_profile_data(profile_name)

    if not profile:
        return 0

    shapekeys = collect_collection_shapekeys(collection)

    support = summarize_variant_support_from_profile(shapekeys, profile)
    return count_variants_from_support(support)
