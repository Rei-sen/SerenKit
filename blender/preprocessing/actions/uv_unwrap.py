from __future__ import annotations
from typing import Optional

from bpy.props import BoolProperty
from bpy.types import Context, PropertyGroup, UILayout

from ..action_category import ActionCategory

from ..base_action import ActionSettings, BaseAction


class UVUnwrapActionSettingsPG(ActionSettings):
    pin_boundaries: BoolProperty(  # type: ignore
        name="Pin Boundaries",
        description="Whether to pin boundary vertices during unwrapping",
        default=False,
    )


class UVUnwrapAction(BaseAction):

    action_name = "UV Unwrap"
    category = ActionCategory.UV
    description = "Unwrap the mesh's UVs to reduce stretching."
    icon = "UV"

    props_attr = "action_uv_unwrap_settings"
    settings_cls = UVUnwrapActionSettingsPG

    @classmethod
    def draw(cls, action_item: PropertyGroup, layout: UILayout) -> None:
        settings = cls.access_settings(action_item)
        layout.prop(settings, "pin_boundaries")

    @classmethod
    def execute(cls, action_item: PropertyGroup) -> None:
        raise NotImplementedError("UV unwrapping logic not implemented yet")
