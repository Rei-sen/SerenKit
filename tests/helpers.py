from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class KeyBlock:
    name: str
    mute: bool = field(default=False)


@dataclass
class ShapeKeys:
    key_blocks: List[KeyBlock]


@dataclass
class Data:
    shape_keys: Optional[ShapeKeys] = None


@dataclass
class Collection:
    all_objects: List[Any] = field(default_factory=list)
    objects: List[Any] = field(default_factory=list)


class Context:
    pass


class Scene:
    pass


class Operator:
    pass


class PropertyGroup:
    pass


@dataclass
class Mesh:
    id: int
    material_name: str


@dataclass
class Model:
    export_enabled: bool = field(default=False)
    game_path: str = field(default="")
    assigned_profile: str = field(default="")
    meshes: List[Mesh] = field(default_factory=list)


@dataclass
class Object:
    type: Any = None
    key_names: List[str] = field(default_factory=list)
    ffxiv_values: List[Any] = field(default_factory=list)
    data: Optional[Data] = None
    ffxiv_attributes: List[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.key_names is None:
            self.data = None
        else:
            self.data = Data(ShapeKeys([KeyBlock(n) for n in self.key_names]))

        if self.ffxiv_values is None:
            self.ffxiv_attributes = []
        else:
            class A:
                def __init__(self, v: Any) -> None:
                    self.value = v

            self.ffxiv_attributes = [A(v) for v in self.ffxiv_values]
