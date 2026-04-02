from typing import Any, Iterable

import bpy

from .shapekey_controller import ShapekeyController


class SceneVariableController(ShapekeyController):

    scene_variable_name: str
    scene_variable_name_value: Any

    def __init__(
        self,
        shapekeys: Iterable[str],
        scene_variable_name: str,
        scene_variable_value: Any,
    ):
        super().__init__(shapekeys)
        self.scene_variable_name = scene_variable_name
        self.scene_variable_value = scene_variable_value

    def set_state(self, value: bool, mesh) -> None:
        super().set_state(value, mesh)

        if not value:
            return

        # TODO: check actual structure, vairable name might be path
        bpy.context.scene[self.scene_variable_name] = self.scene_variable_value
