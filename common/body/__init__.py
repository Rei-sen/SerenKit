from __future__ import annotations

import itertools
from itertools import chain, combinations, groupby
from typing import Any, Iterable, Mapping, TypeVar


from .variant_combo import VariantCombo
from .shape_group import GroupMode, SizeGroup

from ..shape_control.shape_controller_factory import ShapeControllerFactory
from ..shape_control.shapekey_controller import ShapekeyController

T = TypeVar("T")


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def _powerset(iterable: Iterable[T]) -> Iterable[Iterable[T]]:
    "Subsequences of the iterable from shortest to longest."
    # powerset([1,2,3]) → () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


class Body:
    name: str
    size_groups: list[SizeGroup]
    controller: ShapekeyController

    def __init__(
        self,
        name: str,
        size_groups: list[SizeGroup],
        controller: ShapekeyController,
    ):
        self.name = name
        self.size_groups = size_groups
        self.controller = controller

    @classmethod
    def from_dict(
        cls,
        groups: Mapping[str, SizeGroup],
        data: dict[str, Any],
    ) -> Body:
        match data:
            case {
                "display_name": str(name),
                "groups": list(group_names),
                "controller": controller,
            } if all(isinstance(g, str) for g in group_names):
                if any(gname not in groups for gname in group_names):
                    raise ValueError(f"Invalid group names: {group_names}")

                return cls(
                    name=name,
                    size_groups=[groups[gname] for gname in group_names],
                    controller=ShapeControllerFactory.parse_shape_controller(
                        controller
                    ),
                )
            case _:
                raise ValueError(f"Invalid body data: {data}")

    def reset_mesh_state(self, mesh) -> None:
        for group in self.size_groups:
            for shape in group.shapes:
                shape.controller.set_state(False, mesh)

    def get_all_controllers(
        self, include_body: bool = True
    ) -> Iterable[ShapekeyController]:
        if include_body:
            yield self.controller
        for group in self.size_groups:
            for shape in group.shapes:
                yield shape.controller

    def generate_variant_combos(self) -> Iterable[VariantCombo]:
        reduced_groups = map(lambda g: g.reduced_size_group(), self.size_groups)
        filtered_groups = [g for g in reduced_groups if g is not None]

        ordered_groups = sorted(filtered_groups, key=lambda g: g.mode)
        groups = dict(groupby(ordered_groups, key=lambda g: g.mode))
        exclusive_groups = groups.get(GroupMode.EXCLUSIVE, iter([]))

        exclusive_permutations = map(
            VariantCombo,
            itertools.product(
                *[g.shapes for g in exclusive_groups],
            ),
        )

        optional_groups = groups.get(GroupMode.OPTIONAL, iter([]))
        optional_powerset = map(
            VariantCombo,
            _powerset(chain.from_iterable(g.shapes for g in optional_groups)),
        )
        if not exclusive_groups:
            return optional_powerset

        return map(
            lambda t: VariantCombo(chain.from_iterable(t)),
            itertools.product(exclusive_permutations, optional_powerset),
        )
