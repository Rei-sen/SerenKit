from typing import TYPE_CHECKING

from bpy.props import StringProperty
from bpy.types import PropertyGroup


class AttributeEntry(PropertyGroup):
    """Property group for object attributes."""

    value: StringProperty(name="Attribute name")  # type: ignore

    if TYPE_CHECKING:
        value: str  # type: ignore
