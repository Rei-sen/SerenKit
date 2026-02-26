"""Load and manage variant profiles."""

from __future__ import annotations
from enum import Enum, auto

from pathlib import Path
import tomllib
from typing import Dict, Any, Optional, List, Tuple, TypeAlias
from dataclasses import dataclass, field

NamePair: TypeAlias = Tuple[str, str]


@dataclass
class Material:
    name: str
    path: str

    @classmethod
    def from_tuple(cls, pair: Tuple[str, str]) -> Material:
        return cls(name=pair[0], path=pair[1])


class GroupMode(Enum):
    EXCLUSIVE = auto()
    OPTIONAL = auto()


@dataclass
class Group:
    group_name: str
    mode: GroupMode = GroupMode.EXCLUSIVE
    shapekeys: List[NamePair] = field(default_factory=list)

    @staticmethod
    def _is_valid_group_mode(mode: str) -> bool:
        return mode.upper() in GroupMode.__members__

    @staticmethod
    def _is_valid_shapekeys(shapekeys: Any) -> bool:
        return isinstance(shapekeys, dict) and all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in shapekeys.items()
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Group:
        match data:
            case {
                "group_name": str(group_name),
                "mode": str(mode),
                "shapekeys": dict(shapekeys),
            } if cls._is_valid_group_mode(mode) and cls._is_valid_shapekeys(
                shapekeys
            ):
                return cls(
                    group_name=group_name,
                    mode=GroupMode[mode.upper()],
                    shapekeys=list(shapekeys.items()),
                )
            case _:
                raise ValueError(f"Invalid group structure: {data}")

    def get_all_shapekey_names(self) -> set[str]:
        """Return a set of all shapekey names in this group."""
        return {sk[0] for sk in self.shapekeys}


IncompatibilityMap: TypeAlias = Dict[str, List[str]]


@dataclass
class Profile:
    profile_name: str
    standard_materials: List[Material] = field(default_factory=list)
    groups: List[Group] = field(default_factory=list)
    export_aliases: Dict[str, str] = field(default_factory=dict)
    incompatibilities: IncompatibilityMap = field(default_factory=dict)

    @staticmethod
    def _is_valid_materials(materials: Any) -> bool:
        return all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in materials.items()
        )

    @staticmethod
    def _is_valid_groups(groups: Any) -> bool:
        return all(isinstance(g, dict) for g in groups)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Profile:
        match data:
            case {
                "profile_name": str(name),
                "standard_materials": dict(materials),
                "groups": list(groups),
                **rest,
            } if cls._is_valid_materials(materials) and cls._is_valid_groups(
                groups
            ):
                materials_list = [
                    Material.from_tuple(pair) for pair in materials.items()
                ]

                return Profile(
                    profile_name=name,
                    standard_materials=materials_list,
                    groups=list(map(Group.from_dict, groups)),
                    export_aliases=rest.get("export_aliases", {}),
                    incompatibilities=rest.get("incompatibilities", {}),
                )

            case _:
                raise ValueError("Invalid profile structure")

    def get_shapekey_names(self) -> set[str]:
        """Return a set of all shapekey names in this profile."""
        names: set[str] = set()
        for group in self.groups:
            names.update(group.get_all_shapekey_names())
        return names


def _load_profile(path: Path) -> Profile:
    """Load a profile from a TOML file."""
    if not path.exists():
        raise FileNotFoundError(f"Profile file not found: {path}")
    with open(path, "rb") as f:
        try:
            data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Invalid TOML in {path}: {e}")

    return Profile.from_dict(data)


def _load_profiles_from_directory(directory: Path) -> Dict[str, Profile]:
    """Load all profiles from a directory."""
    profiles: Dict[str, Profile] = {}
    if not directory.is_dir():
        return profiles

    for path in directory.glob("*.toml"):
        try:
            profile = _load_profile(path)
            profiles[profile.profile_name] = profile
        except Exception:
            # Skip invalid or unreadable profile files and continue loading others
            continue

    return profiles


def _initialize_profiles_dir() -> Path:
    """Initialize the built-in profiles directory path."""
    addon_dir = Path(__file__).parent.parent
    return addon_dir / "profiles"


_PROFILES_DIRECTORY: Path = _initialize_profiles_dir()
_profiles: Dict[str, Profile] = {}


def get_profiles_dir() -> Path:
    """Return the profiles directory path."""
    return _PROFILES_DIRECTORY


def load_profiles() -> None:
    """Load profiles from the built-in directory."""
    global _profiles
    _profiles.clear()

    _profiles = _load_profiles_from_directory(get_profiles_dir())


def get_loaded_profiles() -> Dict[str, Profile]:
    """Return loaded variant profiles."""
    return _profiles


def is_profile_loaded(profile_name: str) -> bool:
    """Check if a profile is loaded."""
    return profile_name in _profiles


def get_profile_data(profile_name: str) -> Optional[Profile]:
    """Return a profile by name, or None if missing."""
    return _profiles.get(profile_name)


def get_profile_items() -> List[Tuple[str, str, str]]:
    """Generate enum items for UI profile dropdowns."""
    items: List[Tuple[str, str, str]] = []
    for name in _profiles.keys():
        items.append((name, name, f"Variant profile: {name}"))

    if not items:
        items.append(
            ("NONE", "No Profiles Loaded", "Load profiles in addon preferences")
        )

    return items
