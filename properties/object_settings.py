
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from bpy.props import (
    BoolProperty,
    PointerProperty,
    StringProperty,
    CollectionProperty,
)
from bpy.types import Object, PropertyGroup


from ..shared.blender_typing import BlenderCollectionProperty


class AttributeEntry(PropertyGroup):
    """Property group for object attributes."""
    value: StringProperty(name="Attribute name")  # type: ignore

    if TYPE_CHECKING:
        value: str


class ObjectSettings(PropertyGroup):
    """Grouped per-object properties."""

    ffxiv_attributes: CollectionProperty(  # type: ignore
        name="Attributes",
        type=AttributeEntry
    )

    postproc_unwrap_uvs: BoolProperty(  # type: ignore
        name="Unwrap on export",
        description="Run UV unwrap on this object during export postprocessing",
        default=False
    )

    post_proc_robust_weight_transfer: BoolProperty(  # type: ignore
        name="Robust Weight Transfer on export",
        description="Run robust weight transfer on this object during export postprocessing",
        default=False
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

    is_expanded: BoolProperty(  # type: ignore
        name="Expanded",
        description="Whether the part UI is expanded in the model panel",
        default=True
    )

    def copy_from(self, source: ObjectSettings) -> None:
        if not hasattr(source, "__annotations__"):
            return
        for prop_name in source.__annotations__.keys():
            try:
                setattr(self, prop_name, getattr(source, prop_name))
            except (AttributeError, TypeError):
                pass

    if TYPE_CHECKING:
        ffxiv_attributes: BlenderCollectionProperty[AttributeEntry]
        postproc_unwrap_uvs: bool
        post_proc_robust_weight_transfer: bool
        rwt_use_custom_mask: bool
        rwt_custom_mask_name: str
        is_expanded: bool


class ModkitObjectProps(PropertyGroup):
    """Container for Modkit object-scoped properties."""
    # Direct attribute collection for convenience and discoverability.
    attributes: CollectionProperty(  # type: ignore
        name="Attributes",
        type=AttributeEntry
    )

    props: PointerProperty(  # type: ignore
        name="Object Properties",
        type=ObjectSettings
    )

    if TYPE_CHECKING:
        attributes: BlenderCollectionProperty[AttributeEntry]
        props: ObjectSettings


def get_modkit_object_props(obj: Object) -> Optional[ModkitObjectProps]:
    """Get the Modkit object properties from a Blender object."""
    return getattr(obj, "modkit", None)


CLASSES: list[type] = [
    AttributeEntry,
    ObjectSettings,
    ModkitObjectProps,
]
