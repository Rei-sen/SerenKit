from bpy.types import Mesh

from typing import Iterable


class ShapekeyController:

    shapekeys: Iterable[str]

    def __init__(self, shapekeys: Iterable[str]):
        self.shapekeys = shapekeys

    def set_state(self, value: bool, mesh: Mesh) -> None:
        if not mesh.shape_keys:
            return

        for shapekey in self.shapekeys:
            if shapekey in mesh.shape_keys.key_blocks:
                mesh.shape_keys.key_blocks[shapekey].value = (
                    1.0 if value else 0.0
                )
                mesh.shape_keys.key_blocks[shapekey].mute = not value
