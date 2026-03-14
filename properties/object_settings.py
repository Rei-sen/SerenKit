from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from bpy.props import (
    BoolProperty,
    PointerProperty,
    StringProperty,
    CollectionProperty,
)
from bpy.props import IntProperty
from bpy.types import Object, PropertyGroup


from ..shared.blender_typing import BlenderCollectionProperty


class AttributeEntry(PropertyGroup):
    """Property group for object attributes."""

    value: StringProperty(name="Attribute name")  # type: ignore

    if TYPE_CHECKING:
        value: str  # type: ignore


class AttributeSettings(PropertyGroup):
    """Grouped per-object properties."""

    # Direct attribute collection for convenience and discoverability.
    attributes: CollectionProperty(  # type: ignore
        name="Attributes", type=AttributeEntry
    )

    # Active index for UI list display
    attributes_index: IntProperty(  # type: ignore
        name="Attributes Index", default=0
    )

    if TYPE_CHECKING:
        attributes: BlenderCollectionProperty[AttributeEntry]  # type: ignore
        attributes_index: int  # type: ignore


class PreprocessSettings(PropertyGroup):
    """Settings for export preprocessing steps."""

    unwrap_uvs: BoolProperty(  # type: ignore
        name="Unwrap UVs",
        description="Whether to run UV unwrapping during export preprocessing",
        default=False,
    )

    robust_weight_transfer: BoolProperty(  # type: ignore
        name="Robust Weight Transfer",
        description="Whether to run robust weight transfer during export preprocessing",
        default=False,
    )

    rwt_use_custom_mask: BoolProperty(  # type: ignore
        name="Use Custom Mask",
        description="Use a custom mask for robust weight transfer",
        default=False,
    )

    rwt_custom_mask_name: StringProperty(  # type: ignore
        name="Custom Mask Name",
        description="Name of the custom mask to use for robust weight transfer",
        default="",
    )

    if TYPE_CHECKING:
        unwrap_uvs: bool  # type: ignore
        robust_weight_transfer: bool  # type: ignore
        rwt_use_custom_mask: bool  # type: ignore
        rwt_custom_mask_name: str  # type: ignore


class ModkitObjectProps(PropertyGroup):
    """Container for Modkit object-scoped properties."""

    attribute_settings: PointerProperty(  # type: ignore
        name="Attributes", type=AttributeSettings
    )

    preprocess_settings: PointerProperty(  # type: ignore
        name="Preprocess Settings", type=PreprocessSettings
    )

    if TYPE_CHECKING:
        attribute_settings: AttributeSettings  # type: ignore
        preprocess_settings: PreprocessSettings  # type: ignore


def get_modkit_object_props(obj: Object) -> Optional[ModkitObjectProps]:
    """Get the ModkitObjectProps for a given object, if it exists."""
    return getattr(obj, "modkit", None)


CLASSES = [
    AttributeEntry,
    PreprocessSettings,
    AttributeSettings,
    ModkitObjectProps,
]
