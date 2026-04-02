from abc import abstractmethod
from bpy.types import (
    PropertyGroup,
    UILayout,
)
from bpy.utils import register_class, unregister_class

from .action_category import ActionCategory


class ActionSettings(PropertyGroup):
    pass


class BaseAction:

    # Metadata
    action_name: str
    category: ActionCategory
    description: str = ""
    icon: str

    props_attr: str
    settings_cls: type[ActionSettings]

    @classmethod
    @abstractmethod
    def draw(cls, action_item: PropertyGroup, layout: UILayout) -> None: ...

    @classmethod
    @abstractmethod
    def execute(cls, action_item: PropertyGroup) -> None: ...

    # TODO: Tighten the type hints
    @classmethod
    def access_settings(cls, action_item: PropertyGroup) -> ActionSettings:

        setting = getattr(action_item, cls.props_attr)
        if not isinstance(setting, cls.settings_cls):
            raise TypeError(
                f"Expected settings of type {cls.settings_cls}, got {type(setting)}"
            )

        return setting

    @classmethod
    def register(cls) -> None:
        register_class(cls.settings_cls)

    @classmethod
    def unregister(cls) -> None:
        unregister_class(cls.settings_cls)
