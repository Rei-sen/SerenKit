import subprocess
import sqlite3
from pathlib import Path
from typing import Optional

from bpy.types import Object


from .fbx_exporter import FBXExportRunner
from .runner import ExportRunner

from ..db_patcher import apply_mesh_materials, apply_part_attributes
from ..logging import log_debug


class MDLExportRunner(ExportRunner):
    """Export runner that handles exporting a collection to FBX
    and then converting it to MDL using Textools."""

    def export(self, fbx_path: Path, objects: list[Object]) -> None:

        FBXExportRunner.export_fbx_file(fbx_path, objects)

        self._fbx_to_mdl(fbx_path=fbx_path)

    def is_ready(self) -> tuple[bool, Optional[str]]:
        if not self.textools_dir or not Path(self.textools_dir).exists():
            return (
                False,
                "Textools directory not set or does not exist; cannot export to MDL",
            )
        if not self.collection_info or not self.collection_info.game_path:
            return False, "Game path not set; cannot export to MDL"

        return True, None

    def requires_game_path(self) -> bool:
        return True

    def _fbx_to_mdl(
        self,
        fbx_path: Path,
    ) -> None:
        mdl_path: Path = fbx_path.with_suffix(".mdl")

        if not self.textools_dir:
            raise RuntimeError(
                "Textools directory not set; cannot convert FBX to MDL"
            )
        if not self.collection_info.game_path:
            raise RuntimeError("Game path not set; cannot convert FBX to MDL")

        converter_dir: Path = self.textools_dir / "converters" / "fbx"
        db_path: Path = converter_dir / "result.db"

        subprocess.check_call(
            [str(converter_dir / "converter.exe"), str(fbx_path)],
            cwd=converter_dir,
        )

        if not db_path.exists():
            raise RuntimeError("FBX converter did not produce result.db")

        conn: sqlite3.Connection = sqlite3.connect(db_path)
        with conn:
            cur: sqlite3.Cursor = conn.cursor()
            apply_mesh_materials(cur, self.collection_info.materials_info)
            apply_part_attributes(cur, self.collection_info.part_attrs)

        conn.close()

        subprocess.check_call(
            [
                str(self.textools_dir / "ConsoleTools.exe"),
                "/wrap",
                str(db_path),
                str(mdl_path),
                self.collection_info.game_path,
                "/mats",
                "/attributes",
            ],
            cwd=self.textools_dir,
            shell=True,
        )
        log_debug(f"Exported MDL to {mdl_path}")
        log_debug(f"Cleaning up converter DB at {db_path}")
