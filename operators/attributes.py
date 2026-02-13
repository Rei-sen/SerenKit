"""Operators for adding/removing FFXIV attributes on objects."""

from typing import TYPE_CHECKING, Any

import bpy

from bpy.types import Operator, Context
from bpy.props import StringProperty, EnumProperty, BoolProperty

from ..shared.blender_typing import OperatorReturn


# Standard FFXIV attributes
_STANDARD_ATTRIBUTES: list[tuple[str, str, str] | None] = [
    ("atr_hij", "Wrist", ""),
    ("atr_nek", "Neck", ""),
    ("atr_ude", "Elbow", ""),
    None,
    ("atr_hiz", "Knee", ""),
    ("atr_sne", "Shin", ""),
    None,
    ("atr_arm", "Glove", ""),
    None,
    ("atr_leg", "Boot", ""),
    ("atr_spd", "Knee Pad", ""),
    None,
    ("atr_tls", "Tail", "")
    # att ear attributes
]


class MODKIT_OT_handle_attribute(Operator):
    """Add or remove attributes from objects."""
    bl_idname: str = "modkit.handle_attribute"
    bl_label: str = "Handle Attribute"
    bl_options: Any = {'REGISTER', 'UNDO'}

    obj: StringProperty(  # type: ignore
        name="Object",
        description="Object name to add attribute to"
    )

    is_new: BoolProperty(  # type: ignore
        name="Is New",
        description="Add new attribute vs remove existing",
        default=False
    )

    attribute_name: StringProperty(  # type: ignore
        name="Attribute Name",
        description="Name of the attribute to remove",
        default=""
    )

    selection: EnumProperty(  # type: ignore
        name="Attribute",
        description="Most common attributes",
        items=_STANDARD_ATTRIBUTES
    )

    custom_input: StringProperty(  # type: ignore
        name="Custom Attribute",
        description="Custom attribute value",
        default="atr_"
    )

    is_custom: BoolProperty(  # type: ignore
        name="Use Custom",
        description="Use custom attribute instead of standard",
        default=False
    )

    @classmethod
    def description(cls, context: Context, properties: Any) -> str:
        """Operator description based on mode."""
        return "Add new attribute" if properties.is_new else "Remove this attribute"

    def invoke(self, context: Context, event: Any) -> set[OperatorReturn]:
        """Show dialog for add mode; execute for removal."""
        if self.is_new:
            wm = context.window_manager
            if wm is None:
                self.report({'ERROR'}, "Window manager not available")
                return {'CANCELLED'}
            return wm.invoke_props_dialog(self)

        return self.execute(context)

    def draw(self, context: Context) -> None:
        """Draw UI."""
        layout = self.layout

        assert layout is not None

        if self.is_custom:
            layout.prop(self, "custom_input")
        else:
            layout.prop(self, "selection")

        layout.prop(self, "is_custom")

    def execute(self, context: Context) -> set[OperatorReturn]:
        """Perform attribute add or remove."""
        obj = bpy.data.objects.get(self.obj)
        if not obj:
            self.report({'ERROR'}, f"Object '{self.obj}' not found")
            return {'CANCELLED'}

        container = getattr(obj, 'modkit', None)
        if not container:
            self.report({'ERROR'}, "Object missing 'modkit' property group")
            return {'CANCELLED'}

        if self.is_new:
            # Add new attribute
            attribute_value = self.custom_input if self.is_custom else self.selection

            atr = container.attributes.add()
            atr.value = attribute_value
            self.report({'INFO'}, f"Added attribute: {attribute_value}")
        else:
            # Remove existing attribute
            for i, attr in enumerate(container.attributes):
                if self.attribute_name == attr.value:
                    container.attributes.remove(i)
                    self.report(
                        {'INFO'}, f"Removed attribute: {self.attribute_name}")
                    break

        return {'FINISHED'}

    if TYPE_CHECKING:
        obj: str
        is_new: bool
        attribute_name: str
        selection: str
        custom_input: str
        is_custom: bool


CLASSES = [
    MODKIT_OT_handle_attribute,
]
