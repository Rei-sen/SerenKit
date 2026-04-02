from typing import Any, Optional

from bpy.types import AnyType, Context, Mesh, Panel, UILayout, UIList

from ..properties.action_item import ActionItem

from ..operators.actions.add_action import (
    MODKIT_OT_add_preprocessing_action,
)
from ..operators.actions.del_action import (
    MODKIT_OT_delete_preprocessing_action,
)

from ..properties.attribute import AttributeEntry

from ..properties import get_object_container


class MODKIT_PT_PreprocessingPanel(Panel):
    bl_label = "FFXIV Preprocessing"
    bl_idname = "MODKIT_PT_preprocessing_panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        obj = context.object
        return obj is not None and isinstance(obj.data, Mesh)

    def draw(self, context: Context) -> None:
        layout = self.layout
        if layout is None:
            return

        if not context.object:
            return

        obj_modkit = get_object_container(context.object)
        if obj_modkit is None:
            layout.label(text="No modkit properties found for this object.")
            return

        row = layout.row()
        row.template_list(
            MODKIT_UL_preprocessing_action.bl_idname,
            "",
            obj_modkit,
            "actions",
            obj_modkit,
            "active_action_index",
            rows=2,
        )

        op_col = row.column(align=True)
        op_col.operator_menu_enum(
            MODKIT_OT_add_preprocessing_action.bl_idname,
            "action_name",
            text="",
            icon="ADD",
        )
        op_col.operator(
            MODKIT_OT_delete_preprocessing_action.bl_idname,
            text="",
            translate=False,
            icon="REMOVE",
        )

        action = obj_modkit.get_active_action()
        if action is not None:
            action.draw(layout)


class MODKIT_UL_preprocessing_action(UIList):
    bl_idname = "MODKIT_UL_preprocessing_action"

    def draw_item(
        self,
        context: Context,
        layout: UILayout,
        data: Optional[Any],
        item: Optional[Any],
        icon: Optional[int],
        active_data: Optional[Any],
        active_property: Optional[str],
        index: Optional[int],
        flt_flag: Optional[int],
    ) -> None:
        if layout is None:
            return
        if not isinstance(item, ActionItem):
            layout.label(text="Invalid item type")
            return

        item.draw_list_item(layout)
