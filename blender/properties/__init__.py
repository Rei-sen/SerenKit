from typing import Optional

import bpy
from bpy.props import PointerProperty
from bpy.types import Object, Collection

from .action_item import ActionItem
from .shapekey_state import ShapekeyState
from .attribute import AttributeEntry
from .object_container import ObjectContainer
from .collection_container import CollectionContainer
from .material import MaterialItem


def register_properties() -> None:
    """Register properties on Blender types."""

    Object.modkit = PointerProperty(  # type: ignore
        name="Modkit Object Properties",
        type=ObjectContainer,
    )

    Collection.modkit = PointerProperty(  # type: ignore
        name="Modkit Collection Properties",
        type=CollectionContainer,
    )


def unregister_properties() -> None:
    """Unregister properties from Blender types."""

    # Using this so type checkers shut up
    del Object.modkit  # type: ignore
    del Collection.modkit  # type: ignore


_PROPERTIES = [
    ActionItem,
    ShapekeyState,
    AttributeEntry,
    MaterialItem,
    CollectionContainer,
    ObjectContainer,
]


def register() -> None:

    for prop in _PROPERTIES:
        bpy.utils.register_class(prop)

    register_properties()


def unregister() -> None:

    unregister_properties()

    for prop in reversed(_PROPERTIES):
        bpy.utils.unregister_class(prop)


def get_object_container(obj: Object) -> Optional[ObjectContainer]:
    return getattr(obj, "modkit", None)


def get_collection_settings(
    collection: Collection,
) -> Optional[CollectionContainer]:
    return getattr(collection, "modkit", None)
