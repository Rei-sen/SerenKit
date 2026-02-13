"""Utilities for preparing exports and variants."""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional

from bpy.types import Collection, Object

from .model_scanner import ModelScanner
from .variants import (
    summarize_variant_support_from_profile,
    generate_variant_combinations
)
from .profile import NamePair, VariantGroup, VariantProfile, get_profile_data
from .logging import log_debug, log_info
from .export.shapekey_utils import collect_collection_shapekeys

from ..properties.model_settings import get_modkit_collection_props


class CollectionExportContext:
    """Export context for a single collection."""

    def __init__(
            self,
            collection: Collection,
            profile_name: str,
            game_path: Optional[str] = None
    ) -> None:
        """Initialize the collection export context."""
        self.collection = collection
        self.profile_name: str = profile_name
        self.game_path: Optional[str] = game_path
        self._profile_data: Optional[VariantProfile] = None
        self._support_map: Optional[List[VariantGroup]] = None
        self._variants: Optional[List[List[NamePair]]] = None
        self._scanned_meshes: Optional[Dict[int,
                                            List[Tuple[Object, str, int]]]] = None
        self._material_info: Optional[Dict[int, str]] = None
        self._part_attrs: Optional[Dict[Tuple[int, int], List[str]]] = None

    @property
    def profile_data(self) -> Optional[VariantProfile]:
        """Load profile data lazily."""
        if self._profile_data is None:
            self._profile_data = get_profile_data(self.profile_name)
            if self._profile_data:
                log_debug(f"Loaded profile: {self.profile_name}")
        return self._profile_data

    @property
    def support_map(self) -> Optional[List[VariantGroup]]:
        """Generate the support map lazily."""
        if self._support_map is None and self.profile_data:

            shapekeys = collect_collection_shapekeys(self.collection)
            self._support_map = summarize_variant_support_from_profile(
                shapekeys,
                self.profile_data
            )
            log_debug(
                f"Generated support map with {len(self._support_map)} groups")
        return self._support_map

    @property
    def variants(self) -> List[List[NamePair]]:
        """Generate variant combinations lazily."""
        if self._variants is None and self.support_map:
            self._variants = generate_variant_combinations(self.support_map)
            log_info(f"Generated {len(self._variants)} variant combinations")
        return self._variants or []

    @property
    def scanned_meshes(self) -> Dict[int, List[Tuple[Object, str, int]]]:
        """Scan meshes on first access."""
        if self._scanned_meshes is None:
            self._scanned_meshes = ModelScanner.scan_collection(
                self.collection)
        return self._scanned_meshes

    @property
    def material_info(self) -> Dict[int, str]:
        """Material info keyed by mesh ID."""
        if self._material_info is None:
            col_props = get_modkit_collection_props(self.collection)
            model = col_props.model if col_props else None
            self._material_info = {
                mesh.id: mesh.material_name
                for mesh in (model.meshes if model else [])
            }
            if self._material_info:
                log_debug(
                    f"Prepared material info for {len(self._material_info)} meshes")
        return self._material_info

    @property
    def part_attrs(self) -> Dict[Tuple[int, int], List[str]]:
        """Part attributes keyed by (mesh_id, part_id)."""
        if self._part_attrs is None:
            self._part_attrs = {}

            for mesh_id, parts in self.scanned_meshes.items():
                for obj, _, part_id in parts:
                    container = getattr(obj, "modkit", None)
                    attrs_list = getattr(
                        container, "attributes", []) if container is not None else []
                    attrs = [a.value for a in attrs_list]
                    if attrs:
                        self._part_attrs[(mesh_id, part_id)] = attrs
                        log_debug(
                            f"Found attributes for mesh {mesh_id} part {part_id}: {attrs}")

        return self._part_attrs

    @property
    def total_variants(self) -> int:
        """Return the number of variant combinations."""
        return len(self.variants)

    def count_variants(self) -> int:
        """Alias for `total_variants`."""
        return int(self.total_variants)

    def clear(self) -> None:
        """Clear cached context data."""
        self._profile_data = None
        self._support_map = None
        self._variants = None
        self._scanned_meshes = None
        self._material_info = None
        self._part_attrs = None

    def __repr__(self) -> str:
        try:
            name = self.collection.name
        except Exception:
            name = None
        return f"<CollectionExportContext collection={name!r} profile={self.profile_name!r}>"

    @staticmethod
    def from_collection(collection: Collection) -> CollectionExportContext:
        col_props = get_modkit_collection_props(collection)
        if not col_props:
            raise ValueError(
                f"Collection {collection.name} does not have modkit properties")

        game_path = col_props.model.game_path
        profile_name = col_props.model.assigned_profile
        return CollectionExportContext(collection, profile_name, game_path)


def validate_export_readiness(
    collection: Collection,
    require_game_path: bool = True
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

    profile_name = model.assigned_profile or ''

    profile_data = get_profile_data(profile_name)
    if not profile_data:
        return False, f"Profile '{profile_name}' not loaded"

    return True, None
