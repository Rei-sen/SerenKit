from typing import Any

from .scene_variable_controller import SceneVariableController
from .global_modifier_controller import GlobalModifierController
from .shapekey_controller import ShapekeyController


class ShapeControllerFactory:
    @staticmethod
    def parse_shape_controller(data: Any) -> ShapekeyController:
        match data:
            case str(name):
                return ShapekeyController([name])
            case list(keys) if all(isinstance(item, str) for item in keys):
                return ShapekeyController(keys)
            case {
                "name": str(name),
                "modifier": str(modifier),
                "value": bool(value),
            }:
                return GlobalModifierController([name], modifier, value)
            case {
                # TODO: support single key, so profiles dont need to make all of them a list
                "keys": list(keys),
                "scene_variable": str(scene_variable),
                "value": value,
            } if all(isinstance(item, str) for item in keys):
                return SceneVariableController(
                    keys,
                    scene_variable,
                    value,
                )
            case _:
                raise ValueError(f"Invalid shape controller dict: {data}")
