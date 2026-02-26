from typing import TYPE_CHECKING, Dict, Iterable, Optional

import bpy
from bpy.props import (
    IntProperty,
    StringProperty,
    EnumProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty,
)
from bpy.types import Collection, Object, PropertyGroup, Context

from ..shared.blender_typing import BlenderCollectionProperty
from ..shared.profile import get_profile_data, get_profile_items


class MeshSettings(PropertyGroup):
    """Property group for individual mesh configuration."""

    def get_standard_materials(self) -> Dict[str, str]:
        profile_obj = get_profile_data(self.profile)

        if not profile_obj:
            return {}
        mats = {mat.name: mat.path for mat in profile_obj.standard_materials}
        return mats

    def _search(self, context: Context, edit_text: str) -> list[str]:
        return list(self.get_standard_materials().keys())

    def _get_material(self) -> str:
        return self.get("material_name")

    def _set_material(self, name: str) -> None:
        standard_mats = self.get_standard_materials()
        if name in standard_mats.keys():
            self["material_name"] = standard_mats[name]
        else:
            self["material_name"] = name.lower()

    is_expanded: BoolProperty(name="Expanded", default=True)  # type: ignore

    material_name: StringProperty(  # type: ignore
        name="Material Path",
        description="Material Path for selected mesh",
        default="",
        get=_get_material,
        set=_set_material,
        search=_search,
        search_options={"SUGGESTION"},
    )

    id: IntProperty()  # type: ignore
    profile: StringProperty(default="")  # type: ignore

    if TYPE_CHECKING:
        is_expanded: bool
        material_name: str
        id: int
        profile: str


class ModelSettings(PropertyGroup):
    """Property group for model and collection configuration."""

    is_enabled: BoolProperty(  # type: ignore
        name="Enabled", description="Enable handling of this collection"
    )

    export_enabled: BoolProperty(  # type: ignore
        name="Exported",
        description="Enable exporting of this collection",
        default=False,
    )

    meshes: CollectionProperty(type=MeshSettings)  # type: ignore

    def _get_profile_items(
        self, context: Optional[Context] = None
    ) -> Iterable[tuple[str, str, str]]:
        return get_profile_items()

    def _update_mesh_current_profile(
        self, context: Optional[Context] = None
    ) -> None:
        for mesh in self.meshes:
            mesh.profile = self.assigned_profile

    assigned_profile: EnumProperty(  # type: ignore
        name="Variant Profile",
        description="Profile attached to this collection",
        items=_get_profile_items,
        update=_update_mesh_current_profile,
    )

    game_path: StringProperty(  # type: ignore
        name="Game Path",
        description="In-game path for this model (Penumbra)",
        default="",
    )
    export_armature: PointerProperty(  # type: ignore
        name="Armature",
        type=Object,
        poll=lambda self, obj: getattr(obj, "type", "") == "ARMATURE",
        description="Armature to link duplicated objects to for export",
    )

    mannequin_object: PointerProperty(  # type: ignore
        name="Mannequin",
        type=Object,
        poll=lambda self, obj: getattr(obj, "type", "") == "MESH",
        description="Mannequin object used for data transfers",
    )

    export_name: StringProperty(  # type: ignore
        name="Export Name",
        description="Custom name to use when exporting this model",
        default="",
    )

    use_custom_export_name: BoolProperty(  # type: ignore
        name="Use Custom Export Name",
        description="Use the custom export name instead of the collection name",
        default=False,
    )

    def copy_from(self, source: "ModelSettings") -> None:
        if not hasattr(source, "__annotations__"):
            return
        for prop_name in source.__annotations__.keys():
            try:
                setattr(self, prop_name, getattr(source, prop_name))
            except (AttributeError, TypeError):
                pass

    if TYPE_CHECKING:
        is_enabled: bool
        export_enabled: bool
        meshes: BlenderCollectionProperty[MeshSettings]
        assigned_profile: str
        game_path: str
        export_armature: Optional[Object]
        mannequin_object: Optional[Object]
        export_name: str
        use_custom_export_name: bool


class ModkitCollectionProps(PropertyGroup):
    """Container for Modkit collection-scoped properties."""

    model: PointerProperty(name="Model", type=ModelSettings)  # type: ignore

    if TYPE_CHECKING:
        model: ModelSettings


def get_modkit_collection_props(
    col: Collection,
) -> Optional[ModkitCollectionProps]:
    """Get the Modkit collection properties from a Blender collection."""
    return getattr(col, "modkit", None)


def get_model_props(collection: Collection) -> Optional[ModelSettings]:
    """Get the model properties from a collection.

    NOTE: This returns `collection.modkit.model` only (breaking change).
    """
    modkit = get_modkit_collection_props(collection)

    return modkit.model if modkit else None


def get_game_path(collection_name: str) -> str:
    """Get the game path from a collection's model properties."""
    col = bpy.data.collections[collection_name]
    model = get_model_props(col)
    return model.game_path if model else ""


CLASSES: list[type] = [
    MeshSettings,
    ModelSettings,
    ModkitCollectionProps,
]
