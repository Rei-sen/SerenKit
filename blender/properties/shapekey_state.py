from typing import Iterable, TypeAlias

from bpy.types import PropertyGroup
from bpy.props import StringProperty


class ShapekeyState(PropertyGroup):
    name: StringProperty(name="Shape Key Name", default="")  # type: ignore


# def get_modkit_disabled_shapes(collection) -> Iterable[ShapekeyState]:
#     return getattr(collection, "modkit_disabled_shapes", set())


# ObjectShapesCollection: TypeAlias = BlenderCollectionProperty[ShapekeyState]


# def is_shapekey_disabled(
#     collection: Iterable[ShapekeyState], shapekey_name: str
# ) -> bool:
#     for item in collection:
#         if item.name == shapekey_name:
#             return True
#     return False


# def disable_shapekey(
#     collection: ObjectShapesCollection, shapekey_name: str
# ) -> None:
#     if is_shapekey_disabled(collection, shapekey_name):
#         return
#     item = collection.add()
#     item.name = shapekey_name


# def enable_shapekey(
#     collection: ObjectShapesCollection, shapekey_name: str
# ) -> None:
#     for i, item in enumerate(collection):
#         if item.name == shapekey_name:
#             collection.remove(i)
#             return


# def toggle_shapekey_state(
#     collection: ObjectShapesCollection, shapekey_name: str
# ) -> None:
#     if is_shapekey_disabled(collection, shapekey_name):
#         enable_shapekey(collection, shapekey_name)
#     else:
#         disable_shapekey(collection, shapekey_name)


# CLASSES: list[type] = [
#     ShapekeyState,
# ]
