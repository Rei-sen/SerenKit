from bpy.types import Context, Operator

from ...properties import get_object_container

from ...typing import OperatorReturn


class MODKIT_OT_delete_preprocessing_action(Operator):
    bl_idname = "modkit.delete_preprocessing_action"
    bl_label = "Delete Preprocessing Action"
    bl_description = "Delete a preprocessing action from the list"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        obj = context.object
        if obj is None:
            return False
        obj_modkit = get_object_container(obj)
        return obj_modkit is not None and len(obj_modkit.actions) > 0

    def execute(self, context: Context) -> set[OperatorReturn]:
        obj = context.object
        if not obj:
            self.report({"ERROR"}, "No active object found.")
            return {"CANCELLED"}

        obj_modkit = getattr(obj, "modkit", None)
        if not obj_modkit:
            self.report(
                {"ERROR"}, "No modkit properties found on the active object."
            )
            return {"CANCELLED"}

        obj_modkit.delete_active_action()

        return {"FINISHED"}
