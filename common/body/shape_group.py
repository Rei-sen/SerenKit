from __future__ import annotations

from enum import Enum
from typing import Iterable, Iterator, Optional

from ..shape_control.shape_controller_factory import ShapeControllerFactory

from .body_shape import BodyShape


class GroupMode(Enum, str):
    EXCLUSIVE = "exclusive"
    OPTIONAL = "optional"


class SizeGroup:
    name: str
    mode: GroupMode
    shapes: Iterable[BodyShape]

    def __init__(
        self,
        name: str,
        mode: GroupMode,
        shapes: Iterable[BodyShape],
    ):
        self.name = name
        self.mode = mode
        self.shapes = shapes

    @staticmethod
    def shapes_from_dict(shape_data: dict) -> Iterable[BodyShape]:

        if not all(isinstance(k, str) for k in shape_data.keys()):
            raise ValueError(f"Invalid shape data: {shape_data}")

        yield from [
            BodyShape(
                name=name,
                controller=ShapeControllerFactory.parse_shape_controller(data),
            )
            for name, data in shape_data.items()
        ]

    @classmethod
    def from_dict(cls, data: dict) -> SizeGroup:
        match data:
            case {
                "group_name": str(group_name),
                "mode": GroupMode(mode),
                "shapekeys": dict(keys),
            }:
                return cls(
                    name=group_name,
                    mode=mode,
                    shapes=cls.shapes_from_dict(keys),
                )
            case _:
                raise ValueError(f"Invalid SizeGroup data: {data}")

    def get_only_enabled_shapes(self) -> Iterator[BodyShape]:
        yield from filter(lambda s: s.is_enabled, self.shapes)

    def reduced_size_group(self) -> Optional[SizeGroup]:

        enabled_shapes = list(self.get_only_enabled_shapes())
        if not enabled_shapes:
            return None

        return SizeGroup(
            name=self.name,
            mode=self.mode,
            shapes=enabled_shapes,
        )
