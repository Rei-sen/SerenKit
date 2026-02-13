
from typing import TYPE_CHECKING
from bpy.types import Operator, Context
from bpy.props import StringProperty

from ..shared.ui_helpers import toggle_transient_state
from ..shared.blender_typing import OperatorReturn


class MODKIT_OT_toggle_transient(Operator):
    """Toggle a transient UI state identified by `state_key`."""
    bl_idname = "modkit.toggle_transient"
    bl_label = "Toggle Transient State"

    state_key: StringProperty(name="State Key")  # type: ignore

    def execute(self, context: Context) -> set[OperatorReturn]:
        state_key = self.state_key
        if not state_key:
            self.report({'ERROR'}, "State key not provided")
            return {'CANCELLED'}

        try:
            toggle_transient_state(state_key)
        except Exception:
            self.report({'ERROR'}, f"Failed to toggle state: {state_key}")
            return {'CANCELLED'}

        area = getattr(context, 'area', None)
        area.tag_redraw() if area else None
        return {'FINISHED'}

    if TYPE_CHECKING:
        state_key: str


CLASSES = [
    MODKIT_OT_toggle_transient,
]
