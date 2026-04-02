import importlib
from itertools import groupby
from operator import attrgetter
import pkgutil
from typing import Iterable, Optional

from bpy.props import PointerProperty
from bpy.types import PropertyGroup

from ..action_category import ActionCategory
from ..base_action import BaseAction


class ActionRegistry:
    _actions: set[type[BaseAction]] = set()
    _action_enum_list: list[tuple[str, str, str, str, int]] = list()
    _action_name_mapping: dict[str, type[BaseAction]] = dict()

    @staticmethod
    def import_all_submodules() -> None:
        for _, module_name, is_pkg in pkgutil.iter_modules(__path__):
            if is_pkg or module_name.startswith("__"):
                continue
            importlib.import_module(f"{__name__}.{module_name}")

    @staticmethod
    def discover_all_actions() -> Iterable[type[BaseAction]]:
        return BaseAction.__subclasses__()

    def register_action_properties(self) -> None:
        for action_cls in self._actions:
            action_cls.register()

    def unregister_action_properties(self) -> None:
        for action_cls in self._actions:
            action_cls.unregister()

    def wipe_cache(self) -> None:
        self._actions.clear()
        self._action_enum_list.clear()
        self._action_name_mapping.clear()

    def build_mapping_cache(self, actions: Iterable[type[BaseAction]]) -> None:
        for action_cls in actions:
            self._action_name_mapping[action_cls.action_name] = action_cls

    def build_enum_list(
        self,
        grouped_actions: Iterable[
            tuple[ActionCategory, Iterable[type[BaseAction]]]
        ],
    ) -> None:
        for category, actions in grouped_actions:
            self._action_enum_list.append(("", category.value, "", "", 0))
            for action in actions:
                self._action_enum_list.append(
                    (
                        action.action_name,
                        action.action_name,
                        action.description,
                        action.icon,
                        len(self._action_enum_list),
                    )
                )

    def generate_caches(self) -> None:
        self.wipe_cache()

        self._actions = set(self.discover_all_actions())

        self.build_mapping_cache(self._actions)

        self.build_enum_list(
            groupby(
                sorted(
                    self._actions,
                    key=attrgetter("category", "action_name"),
                ),
                key=attrgetter("category"),
            )
        )

    def get_action_by_name(self, name: str) -> Optional[type[BaseAction]]:
        return self._action_name_mapping.get(name)

    def get_action_enum_items(self) -> list[tuple[str, str, str, str, int]]:
        return self._action_enum_list

    def inject_action_settings_to_property_group(
        self,
        target: type[PropertyGroup],
    ) -> None:
        ann = dict(getattr(target, "__annotations__", {}))
        for action_cls in self._actions:
            attr = action_cls.props_attr
            if attr in ann:
                continue
            ann[attr] = PointerProperty(type=action_cls.settings_cls)  # type: ignore

        target.__annotations__ = ann


_REGISTRY = ActionRegistry()


def get_action_by_name(name: str) -> Optional[type[BaseAction]]:
    return _REGISTRY.get_action_by_name(name)


def get_action_enum_items() -> list[tuple[str, str, str, str, int]]:
    return _REGISTRY.get_action_enum_items()


def register(action_item_class: type[PropertyGroup]) -> None:
    _REGISTRY.import_all_submodules()
    _REGISTRY.generate_caches()
    _REGISTRY.register_action_properties()
    _REGISTRY.inject_action_settings_to_property_group(action_item_class)


def unregister() -> None:
    _REGISTRY.unregister_action_properties()
