from bpy.props import PointerProperty, CollectionProperty, RemoveProperty
from bpy.types import Object, Collection

from .material import MaterialItem
from .collection_settings import CollectionSettings
from .shapekey_state import ShapekeyState
from .object_settings import ModkitObjectProps


def register_properties() -> None:
    """Register properties on Blender types."""

    Object.modkit = PointerProperty(  # type: ignore
        name="Modkit Object Properties", type=ModkitObjectProps
    )

    Collection.modkit_disabled_shapes = CollectionProperty(  # type: ignore
        name="Disabled Shape Keys",
        description="List of shape keys that should be disabled during export",
        type=ShapekeyState,
    )

    Collection.modkit_materials = CollectionProperty(  # type: ignore
        name="Materials",
        description="Materials to export with the model",
        type=MaterialItem,
    )

    Collection.modkit_settings = PointerProperty(  # type: ignore
        name="Collection Settings",
        description="Settings for Modkit collection properties",
        type=CollectionSettings,
    )


def unregister_properties() -> None:
    """Unregister properties from Blender types."""

    # Using this so type checkers shut up
    del Object.modkit  # type: ignore
    del Collection.modkit_disabled_shapes  # type: ignore
    del Collection.modkit_materials  # type: ignore
    del Collection.modkit_settings  # type: ignore
