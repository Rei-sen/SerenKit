"""Operators for adding/removing FFXIV attributes on objects."""

from typing import TYPE_CHECKING, Any

import bpy

from bpy.types import Operator, Context
from bpy.props import StringProperty, EnumProperty, BoolProperty, IntProperty

from ..properties.object_settings import get_modkit_object_props

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
    ("atr_cn_neck", "Neck Connector", ""),
    ("atr_cn_wrist", "Wrist Connector", ""),
    ("atr_cn_waist", "Waist Connector", ""),
    ("atr_cn_ankle", "Ankle Connector", ""),
    None,
    ("atr_tls", "Tail Races", ""),
    ("atr_tlh", "Tailless Races", ""),
    ("atr_top", "Miqo'te Ears", ""),
    ("atr_lod", "Excess Detail", ""),
]


class MODKIT_OT_add_attribute(Operator):
    """Add an attribute to the active object."""

    bl_idname = "modkit.add_attribute"
    bl_label = "Add Attribute"
    bl_options = {"REGISTER", "UNDO"}

    target: StringProperty(  # type: ignore
        name="Target Object",
        description="Object name to add attribute to",
        options={"HIDDEN"},
    )

    selection: EnumProperty(  # type: ignore
        name="Attribute",
        description="Most common attributes",
        items=_STANDARD_ATTRIBUTES,
    )

    custom_input: StringProperty(  # type: ignore
        name="Custom Attribute",
        description="Custom attribute value",
        default="atr_",
    )

    is_custom: BoolProperty(  # type: ignore
        name="Use Custom",
        description="Use custom attribute instead of standard",
        default=False,
    )

    def invoke(self, context: Context, event: Any) -> set[OperatorReturn]:
        wm = context.window_manager
        if wm is None:
            self.report({"ERROR"}, "Window manager not available")
            return {"CANCELLED"}
        return wm.invoke_props_dialog(self)

    def draw(self, context: Context) -> None:
        layout = self.layout

        if not layout:
            return

        if self.is_custom:
            layout.prop(self, "custom_input")
        else:
            layout.prop(self, "selection")

        layout.prop(self, "is_custom")

    def execute(self, context: Context) -> set[OperatorReturn]:
        obj = context.active_object
        if not obj:
            self.report({"ERROR"}, "No active object")
            return {"CANCELLED"}

        # Object-scoped attributes are stored on `obj.modkit.attributes`.
        modkit = get_modkit_object_props(obj)
        if not modkit:
            self.report({"ERROR"}, "No attributes found for this mesh.")
            return {"CANCELLED"}

        if self.is_custom:
            attribute_value = self.custom_input
        else:
            attribute_value = self.selection

        atr = modkit.attribute_settings.attributes.add()
        atr.value = attribute_value

        self.report({"INFO"}, f"Added new attribute: {attribute_value}")
        return {"FINISHED"}


class MODKIT_OT_remove_attribute(Operator):
    bl_idname = "modkit.remove_attribute"
    bl_label = "Remove Attribute"
    bl_options = {"REGISTER", "UNDO"}

    target: StringProperty(  # type: ignore
        name="Target Object",
        description="Object name to remove attribute from",
        options={"HIDDEN"},
    )

    attribute_index: IntProperty(  # type: ignore
        name="Attribute Index",
        description="Index of the attribute to remove",
        options={"HIDDEN"},
        default=0,
    )

    def execute(self, context: Context) -> set[OperatorReturn]:
        """Perform attribute removal."""
        obj = bpy.data.objects.get(self.target)
        if not obj:
            self.report({"ERROR"}, f"Object '{self.target}' not found")
            return {"CANCELLED"}

        props = get_modkit_object_props(obj)
        if not props:
            self.report({"ERROR"}, "Object missing 'modkit' property group")
            return {"CANCELLED"}

        idx = self.attribute_index
        props.attribute_settings.attributes.remove(idx)
        return {"FINISHED"}

    def draw(self, context: Context) -> None:
        pass

    if TYPE_CHECKING:
        target: str  # type: ignore
        attribute_index: int  # type: ignore


CLASSES = [
    MODKIT_OT_add_attribute,
    MODKIT_OT_remove_attribute,
]
