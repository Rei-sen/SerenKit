from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

from bpy.types import Object

from ..profile import Profile


@dataclass
class ExportSettings:

    profile: Profile
    export_root_dir: Path
    export_prefix: str
    game_path: Optional[str]
    live_install_target_dir: Optional[Path]
    textools_dir: Optional[Path]
    mannequin: Optional[Object]
    attributes: Mapping[tuple[int, int], list[str]]
    materials_info: Mapping[int, str]
    convert_to_mdl: bool = False
    mdl_export_mode: str = "textools"
