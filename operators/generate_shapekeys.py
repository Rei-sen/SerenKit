from bpy.types import Context, Mesh, Operator
from bpy.props import StringProperty
from ..shared.profile import get_profile_data

from ..shared.blender_typing import OperatorReturn


class MODKIT_OT_generate_shapekeys(Operator):
    """Generate shapekeys for the active object based on the current profile."""

    bl_idname = "modkit.generate_shapekeys"
    bl_description = (
        "Generate EMPTY shapekeys from selected group for selected object"
    )
    bl_label = "Generate Shapekeys"
    bl_options = {"REGISTER", "UNDO"}

    profile: StringProperty(  # type: ignore
        name="Profile Name",
        description="Name of the profile to use for shapekey generation",
        options={"HIDDEN"},
    )

    group_name: StringProperty(  # type: ignore
        name="Group Name",
        description="Name of the group to use for shapekey generation",
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[OperatorReturn]:
        obj = context.active_object
        if not obj:
            self.report({"ERROR"}, "No active object")
            return {"CANCELLED"}

        profile = get_profile_data(self.profile)
        if not profile:
            self.report({"ERROR"}, f"Profile not found: {self.profile}")
            return {"CANCELLED"}

        group = next(
            (g for g in profile.groups if g.group_name == self.group_name), None
        )

        if not group:
            self.report({"ERROR"}, f"Group not found: {self.group_name}")
            return {"CANCELLED"}

        shapekeys = group.get_all_shapekey_names()

        if not shapekeys:
            self.report({"ERROR"}, "No shapekeys found in collection")
            return {"CANCELLED"}

        existing_keys: set[str] = (
            set(obj.data.shape_keys.key_blocks.keys())
            if isinstance(obj.data, Mesh) and obj.data.shape_keys
            else set()
        )

        for sk in shapekeys:
            if sk not in existing_keys:
                obj.shape_key_add(name=sk, from_mix=False)

        self.report(
            {"INFO"},
            f"Generated shapekeys for '{obj.name}': {', '.join(shapekeys)}",
        )
        return {"FINISHED"}


CLASSES = [
    MODKIT_OT_generate_shapekeys,
]
