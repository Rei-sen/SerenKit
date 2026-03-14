import bpy
from bpy.types import Object


def select_objects_for_export(objects: list[Object]) -> None:
    """Select the given objects in the viewport, making the first one active."""

    bpy.ops.object.select_all(action="DESELECT")

    if not objects:
        return

    for o in objects:
        o.select_set(True)

    view_layer = bpy.context.view_layer
    if view_layer:
        view_layer.objects.active = objects[0]
