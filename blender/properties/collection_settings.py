from typing import Optional

from bpy.types import Collection, Object, PropertyGroup
from bpy.props import PointerProperty


class CollectionContainer(PropertyGroup):

    mannequin_object: PointerProperty(  # type: ignore
        name="Mannequin Object",
        description="Mannequin object used for data transfers",
        type=Object,
        poll=lambda self, obj: getattr(obj, "type", "") == "MESH",
    )

    armature_object: PointerProperty(  # type: ignore
        name="Armature Object",
        description="Armature object associated with this collection",
        type=Object,
        poll=lambda self, obj: getattr(obj, "type", "") == "ARMATURE",
    )


CLASSES = [
    CollectionContainer,
]
