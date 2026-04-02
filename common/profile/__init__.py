from __future__ import annotations

from typing import Mapping, Optional, TypeAlias

from .profile_info import ProfileInfo

from ..body import Body
from ..body.shape_group import SizeGroup

MaterialMapping: TypeAlias = Mapping[str, str]


class Profile:
    name: str
    standard_materials: MaterialMapping
    controllers: list[str]
    shape_groups: set[SizeGroup]
    bodies: list[Body]
    info: Optional[ProfileInfo] = None

    def __init__(
        self,
        name: str,
        controllers: list[str],
        groups: set[SizeGroup],
        bodies: list[Body],
        standard_materials: MaterialMapping,
    ) -> None:
        self.name = name
        self.controllers = controllers
        self.shape_groups = groups
        self.bodies = bodies
        self.standard_materials = standard_materials

    @classmethod
    def from_dict(cls, data: dict) -> Profile:
        match data:
            case {
                "profile_name": str(name),
                "standard_materials": dict(standard_materials),
                "controllers": list(controller_names),
                "bodies": list(body_list),
                "groups": list(group_list),
            }:
                if not all(
                    isinstance(k, str) and isinstance(v, str)
                    for k, v in standard_materials.items()
                ):
                    raise ValueError(
                        f"Invalid standard materials data: {standard_materials}"
                    )

                if not all(isinstance(name, str) for name in controller_names):
                    raise ValueError(
                        f"Invalid controller names: {controller_names}"
                    )

                groups = {SizeGroup.from_dict(g) for g in group_list}
                group_mapping = {g.name: g for g in groups}

                bodies = [
                    Body.from_dict(group_mapping, body_data)
                    for body_data in body_list
                ]

                return cls(
                    name=name,
                    standard_materials=standard_materials,
                    controllers=controller_names,
                    groups=groups,
                    bodies=bodies,
                )
            case _:
                raise ValueError(f"Invalid profile data: {data}")
