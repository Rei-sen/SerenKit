from bpy.props import StringProperty
from bpy.types import PropertyGroup, UILayout

from ..preprocessing.actions import get_action_by_name


class ActionItem(PropertyGroup):

    action_name: StringProperty(name="Action Name", default="")  # type: ignore

    def draw_list_item(self, layout: UILayout) -> None:
        action_cls = get_action_by_name(self.action_name)
        if action_cls is None:
            layout.label(text=self.action_name, icon="ERROR")
            return
        layout.label(
            text=action_cls.action_name,
            icon=action_cls.icon,  # type: ignore
        )

    def draw(self, layout: UILayout) -> None:
        action_cls = get_action_by_name(self.action_name)
        if action_cls is None:
            layout.label(
                text=f"Unknown action: {self.action_name}", icon="ERROR"
            )
            return
        action_cls.draw(self, layout)
