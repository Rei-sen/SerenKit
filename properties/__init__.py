import bpy
from bpy.props import PointerProperty
from bpy.types import Collection, Object, Scene

from .model_settings import ModkitCollectionProps
from .object_settings import ModkitObjectProps
from .export_properties import ModkitSceneProps


def register_properties():
    """Register properties on Blender types."""

    bpy.types.Scene.modkit = PointerProperty(
        name="Modkit",
        type=ModkitSceneProps
    )
    bpy.types.Collection.modkit = PointerProperty(
        name="Modkit",
        type=ModkitCollectionProps
    )

    bpy.types.Object.modkit = PointerProperty(
        name="Modkit Object Properties",
        type=ModkitObjectProps
    )


def unregister_properties():
    """Unregister properties from Blender types."""

    del Object.modkit
    del Collection.modkit
    del Scene.modkit
