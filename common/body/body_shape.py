from ..shape_control.shapekey_controller import ShapekeyController


class BodyShape:
    name: str
    is_enabled: bool = True
    controller: ShapekeyController

    def __init__(
        self,
        name: str,
        controller: ShapekeyController,
    ):
        self.name = name
        self.controller = controller

    def activate(self, mesh) -> None:
        self.controller.set_state(True, mesh)

    def deactivate(self, mesh) -> None:
        self.controller.set_state(False, mesh)
