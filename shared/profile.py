"""Load and manage variant profiles."""

from __future__ import annotations
import json
import os

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Literal, TypeAlias
from dataclasses import dataclass, field

NamePair: TypeAlias = Tuple[str, str]


@dataclass
class VariantGroup:
    group_name: str
    mode: Literal["exclusive", "optional"] = "exclusive"
    shapekeys: List[NamePair] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VariantGroup:

        # Validate structure
        cls.validate_dict(data)

        return cls(
            group_name=data["group_name"],
            mode=data.get("mode", "exclusive"),
            shapekeys=list(data["shapekeys"].items())
        )

    @staticmethod
    def validate_dict(group: dict[str, Any]) -> None:
        required_keys = ["group_name", "mode", "shapekeys"]
        name = group.get("group_name", "<unknown>")
        for key in required_keys:
            if key not in group:
                raise ValueError(f"Group {name} missing required key '{key}'")
        if not isinstance(group["shapekeys"], dict):
            raise ValueError(f"Group {name} 'shapekeys' must be a dict")
        return None

    def get_all_shapekey_names(self) -> set[str]:
        """Return all shapekey names in this VariantGroup."""
        return {sk[0] for sk in self.shapekeys}


@dataclass
class VariantProfile:
    """Typed representation of a variant profile."""
    profile_name: str
    standard_materials: List[NamePair] = field(default_factory=list)
    groups: List[VariantGroup] = field(default_factory=list)
    shpx: List[str] = field(default_factory=list)
    export_aliases: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VariantProfile":
        cls.validate_dict(data)
        groups_raw = data.get("groups", [])
        groups = [VariantGroup.from_dict(g) for g in groups_raw]
        # Accept dict or list of pairs for standard_materials
        sm_raw = data.get("standard_materials", {})
        standard_materials = list(sm_raw.items())
        shpx = data.get("shpx", [])
        export_aliases = data.get("export_aliases", {})

        return cls(
            profile_name=data["profile_name"],
            standard_materials=standard_materials,
            groups=groups,
            shpx=shpx,
            export_aliases=export_aliases,
        )

    @staticmethod
    def validate_dict(data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValueError("Profile must be a dictionary")
        if "profile_name" not in data:
            raise ValueError("Variant profile missing 'profile_name'")
        if "profile_name" and not isinstance(data["profile_name"], str):
            raise ValueError("'profile_name' must be a string")
        if "standard_materials" in data and not isinstance(data["standard_materials"], dict):
            raise ValueError("'standard_materials' must be a dictionary")
        if "groups" in data:
            if not isinstance(data["groups"], list):
                raise ValueError("'groups' must be a list")
            for group in data["groups"]:
                VariantGroup.validate_dict(group)  # Will raise if invalid
        if "shpx" in data and not isinstance(data["shpx"], list):
            raise ValueError(
                "'shpx' top-level property must be a list if present")
        if "export_aliases" in data and not isinstance(data["export_aliases"], dict):
            raise ValueError(
                "'export_aliases' top-level property must be a dict if present")
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_name": self.profile_name,
            "standard_materials": dict(self.standard_materials),
            "groups": [
                {
                    "group_name": g.group_name,
                    "mode": g.mode,
                    "shapekeys": dict(g.shapekeys)
                }
                for g in self.groups],
            "shpx": self.shpx,
            "export_aliases": self.export_aliases,
        }

    def get_all_shapekey_names(self) -> set[str]:
        """Return all shapekey names in this VariantProfile."""
        names: set[str] = set()
        for group in self.groups:
            names.update(group.get_all_shapekey_names())
        return names


_loaded_profiles: Dict[str, VariantProfile] = {}
_builtin_profiles_directory: Optional[Path] = None  # Will be set on first use


def get_builtin_profiles_dir() -> Path:
    """Return the built-in profiles directory path."""

    global _builtin_profiles_directory
    if _builtin_profiles_directory is None:
        addon_dir = Path(__file__).parent.parent
        _builtin_profiles_directory = addon_dir / "profiles"
    return _builtin_profiles_directory


def get_loaded_profiles() -> Dict[str, VariantProfile]:
    """Return loaded variant profiles."""
    return _loaded_profiles


def get_profile_data(profile_name: str) -> Optional[VariantProfile]:
    """Return a profile by name, or None if missing."""
    return _loaded_profiles.get(profile_name)


def get_profile_items() -> List[Tuple[str, str, str]]:
    """Generate enum items for UI profile dropdowns."""
    items: List[Tuple[str, str, str]] = []
    for name in _loaded_profiles.keys():
        items.append((name, name, f"Variant profile: {name}"))

    if not items:
        items.append(("NONE", "No Profiles Loaded",
                     "Load profiles in addon preferences"))

    return items


def load_variant_profile(json_path: str) -> VariantProfile:
    """Load and validate a variant profile from JSON."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Variant profile JSON not found: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {json_path}: {e}")

    # Use the VariantProfile class for validation and typed representation
    return VariantProfile.from_dict(data)


def load_variant_profiles_from_dir(folder_path: str) -> Dict[str, VariantProfile]:
    """Load all JSON variant profiles from a directory."""
    profiles: Dict[str, VariantProfile] = {}

    if not os.path.isdir(folder_path):
        return profiles

    for path in Path(folder_path).glob("*.json"):
        try:
            profile = load_variant_profile(str(path))
            profile_name = profile.profile_name
            profiles[profile_name] = profile
        except Exception as e:
            print(f"[PROFILE] Error loading {path.name}: {e}")

    return profiles


def reload_profiles() -> int:
    """Reload profiles from built-in directory.

    Returns:
        Number of profiles loaded
    """
    global _loaded_profiles
    _loaded_profiles.clear()

    builtin_dir: Path = get_builtin_profiles_dir()
    _loaded_profiles.update(load_variant_profiles_from_dir(str(builtin_dir)))

    return len(_loaded_profiles)


def auto_load_profiles() -> int:
    """Auto-load built-in profiles on addon startup.

    Returns:
        Number of profiles loaded
    """
    return reload_profiles()
