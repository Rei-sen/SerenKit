"""Utilities for preparing exports and variants."""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional

from bpy.types import Collection


from .model_scanner import ModelScanner
from .variants import filter_profile_shapekeys, generate_variant_combinations
from .profile import (
    NamePair,
    Profile,
    get_profile_data,
    is_profile_loaded,
)
from .export.shapekey_utils import collect_collection_shapekeys

from ..properties.model_settings import get_modkit_collection_props
from ..properties.object_settings import get_modkit_object_props


def _collect_attributes(
    collection: Collection,
) -> Dict[Tuple[int, int], List[str]]:
    """Collect attributes for all parts in a collection."""
    attribute_map = dict()
    for mesh_id, parts in ModelScanner.scan_collection(collection).items():
        for obj, _, part_id in parts:
            props = get_modkit_object_props(obj)
            if not props:
                continue
            attrs_list = [a.value for a in props.attributes]
            if attrs_list:
                attribute_map[(mesh_id, part_id)] = attrs_list
    return attribute_map


class CollectionExportInfo:

    def __init__(self, collection: Collection):
        props = get_modkit_collection_props(collection)
        if not props:
            raise ValueError(
                f"Collection {collection.name} does not have modkit properties"
            )
        profile_name = props.model.assigned_profile
        profile = get_profile_data(profile_name)
        if not profile:
            raise ValueError(
                f"Profile '{profile_name}' not found for collection {collection.name}"
            )

        reduced_profile = filter_profile_shapekeys(
            collect_collection_shapekeys(collection), profile
        )

        materials_info = {
            mesh.id: mesh.material_name for mesh in (props.model.meshes)
        }

        part_attrs = _collect_attributes(collection)

        self._collection = collection
        self._profile_name: str = profile_name
        self._profile: Profile = profile
        self._game_path: str = props.model.game_path
        self._variants: List[List[NamePair]] = generate_variant_combinations(
            reduced_profile, profile.incompatibilities
        )
        self._materials_info: Dict[int, str] = materials_info
        self._part_attrs: Dict[Tuple[int, int], List[str]] = part_attrs

    @property
    def collection(self) -> Collection:
        return self._collection

    @property
    def profile_name(self) -> str:
        return self._profile_name

    @property
    def profile(self) -> Profile:
        return self._profile

    @property
    def game_path(self) -> str:
        return self._game_path

    @property
    def variants(self) -> List[List[NamePair]]:
        return self._variants

    @property
    def materials_info(self) -> Dict[int, str]:
        return self._materials_info

    @property
    def part_attrs(self) -> Dict[Tuple[int, int], List[str]]:
        return self._part_attrs

    @property
    def variant_count(self) -> int:
        return len(self.variants)


def is_export_ready(
    collection: Collection, require_game_path: bool = True
) -> Tuple[bool, Optional[str]]:
    """Check if a collection is ready for export, validating necessary conditions."""
    col_props = get_modkit_collection_props(collection)
    if not col_props:
        return False, "Collection does not have modkit properties"

    model = col_props.model
    if not model.export_enabled:
        return False, "Collection export is not enabled"

    if require_game_path and not model.game_path:
        return False, "No game_path set for collection"

    if not model.assigned_profile:
        return False, "No variant profile assigned"

    profile_name = model.assigned_profile
    if not is_profile_loaded(profile_name):
        return False, f"Profile '{profile_name}' not loaded"

    return True, None


def validate_export_readiness(
    collection: Collection, require_game_path: bool = True
) -> Tuple[bool, Optional[str]]:
    """Validate collection export readiness."""

    col_props = get_modkit_collection_props(collection)
    model = col_props.model if col_props else None

    if not model or not model.export_enabled:
        return False, "Collection export is not enabled"

    if require_game_path and not model.game_path:
        return False, "No game_path set for collection"

    if not model.assigned_profile:
        return False, "No variant profile assigned"

    profile_name = model.assigned_profile or ""

    if not is_profile_loaded(profile_name):
        return False, f"Profile '{profile_name}' not loaded"

    return True, None
