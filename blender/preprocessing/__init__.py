from ..properties.action_item import ActionItem

from . import actions


def register() -> None:
    actions.register(ActionItem)


def unregister() -> None:
    actions.unregister()
