from bpy.props import StringProperty
from bpy.types import PropertyGroup, UILayout

from ..action_category import ActionCategory
from ..base_action import ActionSettings, BaseAction


class FixLRWeightsActionSettings(ActionSettings):
    left_mask: StringProperty(  # type: ignore
        name="Left Mask",
        description="Vertex group name for left side weights",
        default="",
    )
    right_mask: StringProperty(  # type: ignore
        name="Right Mask",
        description="Vertex group name for right side weights",
        default="",
    )


class FixLRWeightsAction(BaseAction):

    action_name = "Fix LR Weights"
    category = ActionCategory.WEIGHTS
    icon = "AREA_SWAP"
    props_attr = "action_fix_lr_weights_settings"
    settings_cls = FixLRWeightsActionSettings

    @classmethod
    def draw(cls, action_item: PropertyGroup, layout: UILayout) -> None:
        settings = cls.access_settings(action_item)
        layout.prop(settings, "left_mask")
        layout.prop(settings, "right_mask")

    @classmethod
    def execute(cls, action_item: PropertyGroup) -> None:
        raise NotImplementedError("LR weight fixing logic not implemented yet")
