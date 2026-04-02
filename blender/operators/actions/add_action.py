from bpy.props import StringProperty, EnumProperty
from bpy.types import Context, Event, Operator, UIList, Object, Collection

from ...preprocessing.actions import get_action_enum_items

from ...properties import get_object_container

from ...typing import OperatorReturn


class MODKIT_OT_add_preprocessing_action(Operator):

    bl_idname = "modkit.add_preprocessing_action"
    bl_label = "Add Preprocessing Action"
    bl_description = "Add a new preprocessing action to this object"
    bl_options = {"REGISTER", "UNDO"}

    action_name: EnumProperty(  # type: ignore
        name="Action Name",
        items=get_action_enum_items(),
    )

    def execute(self, context: Context) -> set[OperatorReturn]:
        obj = context.object
        if obj is None:
            self.report({"ERROR"}, "No active object")
            return {"CANCELLED"}

        obj_modkit = get_object_container(obj)
        if obj_modkit is None:
            self.report({"ERROR"}, "Object does not have modkit properties")
            return {"CANCELLED"}

        obj_modkit.add_action(self.action_name)

        return {"FINISHED"}
