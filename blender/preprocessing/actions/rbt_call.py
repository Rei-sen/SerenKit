from bpy.types import PropertyGroup, UILayout

from ..action_category import ActionCategory

from ..base_action import ActionSettings, BaseAction


class RWTCallActionSettingsPG(ActionSettings):
    pass


class RWTCallAction(BaseAction):

    action_name = "RWT Call"
    category = ActionCategory.WEIGHTS
    icon = "WPAINT_HLT"

    props_attr = "action_rwt_call_settings"
    settings_cls = RWTCallActionSettingsPG

    @classmethod
    def draw(cls, action_item: PropertyGroup, layout: UILayout) -> None:
        raise NotImplementedError("No options to draw for this action")

    @classmethod
    def execute(cls, action_item: PropertyGroup) -> None:
        raise NotImplementedError("RWT call logic not implemented yet")
