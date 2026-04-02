from typing import Optional

from bpy.types import PropertyGroup, Object
from bpy.props import CollectionProperty, IntProperty

from .action_item import ActionItem

from .attribute import AttributeEntry

from .shapekey_state import ShapekeyState


class ObjectContainer(PropertyGroup):

    # Shapekeys

    disabled_shapekeys: CollectionProperty(  # type: ignore
        name="Disabled Shape Keys",
        description="List of shape keys that should be disabled during export",
        type=ShapekeyState,
    )

    def is_shapekey_disabled(self, shapekey_name: str) -> bool:
        return any(
            item.name == shapekey_name for item in self.disabled_shapekeys
        )

    def disable_shapekey(self, shapekey_name: str) -> None:
        if self.is_shapekey_disabled(shapekey_name):
            return
        item = self.disabled_shapekeys.add()
        item.name = shapekey_name

    def enable_shapekey(self, shapekey_name: str) -> None:
        self.disabled_shapekeys.find()
        for i, item in enumerate(self.disabled_shapekeys):
            if item.name == shapekey_name:
                self.disabled_shapekeys.remove(i)
                return

    def toggle_shapekey_state(self, shapekey_name: str) -> None:
        if self.is_shapekey_disabled(shapekey_name):
            self.enable_shapekey(shapekey_name)
        else:
            self.disable_shapekey(shapekey_name)

    # Attributes

    attributes: CollectionProperty(  # type: ignore
        name="Attributes",
        description="List of custom attributes to include during export",
        type=AttributeEntry,
    )

    active_attribute_index: IntProperty(  # type: ignore
        name="Active Attribute Index",
        description="Index of the active attribute in the attributes collection",
        default=0,
    )

    def delete_active_attribute(self) -> None:
        if (
            self.active_attribute_index >= len(self.attributes)
            or self.active_attribute_index < 0
        ):
            return

        self.attributes.remove(self.active_attribute_index)

        if self.active_attribute_index >= len(self.attributes):
            self.active_attribute_index = max(0, len(self.attributes) - 1)

    def add_attribute(self, attribute_name: str) -> None:
        if any(attr.name == attribute_name for attr in self.attributes):
            return
        item = self.attributes.add()
        item.name = attribute_name

    # Preprocessing

    actions: CollectionProperty(  # type: ignore
        name="Preprocessing Actions",
        description="List of preprocessing actions to run during export",
        type=ActionItem,
    )

    active_action_index: IntProperty(  # type: ignore
        name="Active Action Index",
        description="Index of the active preprocessing action in the actions collection",
        default=0,
    )

    def delete_active_action(self) -> None:
        if (
            self.active_action_index >= len(self.actions)
            or self.active_action_index < 0
        ):
            return

        self.actions.remove(self.active_action_index)

        if self.active_action_index >= len(self.actions):
            self.active_action_index = max(0, len(self.actions) - 1)

    def add_action(self, action_name: str) -> None:
        item = self.actions.add()
        item.action_name = action_name

    def get_active_action(self) -> Optional[ActionItem]:
        if (
            self.active_action_index >= len(self.actions)
            or self.active_action_index < 0
        ):
            return None
        return self.actions[self.active_action_index]
