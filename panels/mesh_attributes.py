from typing import Any, Optional

from bpy.types import Panel, Context, Mesh, UIList, UILayout

from ..properties.object_settings import get_modkit_object_props

from ..operators.attributes import (
    MODKIT_OT_add_attribute,
    MODKIT_OT_remove_attribute,
)


class MODKIT_PT_mesh_attributes(Panel):
    bl_idname = "MODKIT_PT_mesh_attributes"
    bl_label = "FFXIV Part Attributes"
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
        obj = context.object

        if layout is None:
            return

        if not obj or not isinstance(obj.data, Mesh):
            layout.label(text="No mesh object selected.")
            return

        # Object-scoped attributes are stored on `obj.modkit.attributes`.
        modkit = get_modkit_object_props(obj)
        if not modkit:
            layout.label(text="No modkit properties found for this object.")
            return

        # Display attributes in a UIList with add/remove buttons
        row = layout.row()
        row.template_list(
            MODKIT_UL_attributes.bl_idname,
            "",
            modkit.attribute_settings,
            "attributes",
            modkit.attribute_settings,
            "attributes_index",
            rows=2,
        )

        col = row.column(align=True)
        add = col.operator(
            MODKIT_OT_add_attribute.bl_idname, icon="ADD", text=""
        )
        add.target = obj.name

        # Determine active attribute value for removal
        active_idx = modkit.attribute_settings.attributes_index
        remove = col.operator(
            MODKIT_OT_remove_attribute.bl_idname, icon="REMOVE", text=""
        )
        remove.target = obj.name
        remove.attribute_index = active_idx


class MODKIT_UL_attributes(UIList):
    bl_idname = "MODKIT_UL_attributes"

    def draw_item(
        self,
        context: Context,
        layout: UILayout,
        data: Any,
        item: Any,
        icon: Optional[int],
        active_data: Any,
        active_property: Optional[str],
        index: Optional[int],
        flt_flag: Optional[int],
    ):
        if item is None:
            return

        layout.prop(item, "value", text="", emboss=False)


CLASSES = [
    MODKIT_PT_mesh_attributes,
    MODKIT_UL_attributes,
]
