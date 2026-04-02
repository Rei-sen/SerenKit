from typing import Iterable

from .shapekey_controller import ShapekeyController


class GlobalModifierController(ShapekeyController):

    controller_object_name: str

    modifier_name: str
    enabled_state: bool

    def __init__(
        self,
        shapekeys: Iterable[str],
        modifier_name: str,
        enabled_state: bool = True,
    ):
        super().__init__(shapekeys)
        self.modifier_name = modifier_name
        self.enabled_state = enabled_state

    def set_state(self, value: bool, mesh) -> None:
        super().set_state(value, mesh)

        if not value:
            return

        # TODO: Implement
        # controller = export_state.get_controller(self.controller_object_name)
        # if not controller:
        #     return
        # modifier = controller.modifiers.get(self.modifier_name)
        # if modifier:
        #     modifier.show_viewport = self.enabled_state
