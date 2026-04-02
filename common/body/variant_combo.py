from __future__ import annotations

from typing import Iterable
from bpy.types import Mesh

from .body_shape import BodyShape


class VariantCombo(list[BodyShape]):

    def is_active(self, mesh: Mesh) -> bool:
        if not mesh.shape_keys:
            return False

        active_shapekeys = {sk.name for sk in mesh.shape_keys.key_blocks}
        return all(sk.name in active_shapekeys for sk in self)

    def apply_combo(
        self,
        relevant_keys: Iterable[BodyShape],
        mesh: Mesh,
    ) -> None:
        for key in relevant_keys:
            if key in self:
                key.activate(mesh)
            else:
                key.deactivate(mesh)

    def variant_name_list(self) -> Iterable[str]:
        yield from (shape.name for shape in self)
