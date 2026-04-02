from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty,
)


class MaterialItem(PropertyGroup):
    name: StringProperty(name="Material Name", default="")  # type: ignore
    path: StringProperty(name="Material Path", default="")  # type: ignore


CLASSES = [
    MaterialItem,
]
