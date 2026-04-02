from typing import Optional

import bpy

from bpy.types import Context, Operator, OperatorProperties
from bpy.props import StringProperty

from ..properties.shapekey_state import toggle_shapekey_state

from .._shared.blender_typing import OperatorReturn


class MODKIT_OT_shape_toggle(Operator):
    bl_idname = "modkit.shape_toggle"
    bl_label = "Shape Stage Toggle"
    bl_description = "Enable/disable this shape stage for export."
    bl_options = {"REGISTER", "UNDO"}

    key: StringProperty(name="Shape Key Name", options={"HIDDEN"})  # type: ignore
    name: StringProperty(name="Export Name", options={"HIDDEN"})  # type: ignore

    collection: StringProperty(name="Collection Name", options={"HIDDEN"})  # type: ignore

    @classmethod
    def description(
        cls, context: Optional[Context], properties: OperatorProperties
    ) -> str:
        return (
            f"Toggle export state for shape key '{properties.key}' "
            f"(export name: '{properties.name}')"
        )

    def execute(self, context: Context) -> set[OperatorReturn]:

        collection = bpy.data.collections.get(self.collection)
        if not collection:
            self.report({"ERROR"}, f"Collection not found: {self.collection}")
            return {"CANCELLED"}

        disabled_shapes = getattr(collection, "modkit_disabled_shapes", None)
        if disabled_shapes is None:
            self.report(
                {"ERROR"},
                f"Collection missing 'modkit_disabled_shapes' property: {self.collection}",
            )
            return {"CANCELLED"}

        toggle_shapekey_state(disabled_shapes, self.key)

        return {"FINISHED"}


CLASSES = [
    MODKIT_OT_shape_toggle,
]
