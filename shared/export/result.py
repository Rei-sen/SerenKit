from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExportResult:
    fbx_files: list[Path] = field(default_factory=list)
    mdl_files: list[Path] = field(default_factory=list)
