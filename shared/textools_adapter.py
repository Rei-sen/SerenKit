from pathlib import Path
import subprocess
import sqlite3
from typing import Mapping

from .logging import log_debug
from .db_patcher import apply_mesh_materials, apply_part_attributes


class TextoolsAdapter:
    """Encapsulates calls to Textools converters and DB-based patching.

    This isolates subprocess and sqlite usage so unit tests can mock the
    adapter instead of invoking external tools.
    """

    textools_dir: Path

    def __init__(self, textools_dir: Path) -> None:
        self.textools_dir = textools_dir

    def convert_fbx(self, fbx_path: Path) -> Path:
        """Run the FBX -> intermediate DB converter and return the DB path."""
        converter_dir: Path = self.textools_dir / "converters" / "fbx"
        db_path: Path = converter_dir / "result.db"

        subprocess.check_call(
            [str(converter_dir / "converter.exe"), str(fbx_path)],
            cwd=converter_dir,
        )

        if not db_path.exists():
            raise RuntimeError("FBX converter did not produce result.db")

        log_debug(f"FBX converter produced DB at {db_path}")
        return db_path

    def apply_patches(
        self,
        db_path: Path,
        materials_info: Mapping[int, str],
        part_attrs: Mapping[tuple[int, int], list[str]],
    ) -> None:
        """Open the converter DB and apply patchers (materials/attributes)."""
        conn = sqlite3.connect(db_path)
        try:
            with conn:
                cur = conn.cursor()
                apply_mesh_materials(cur, materials_info)
                apply_part_attributes(cur, part_attrs)
        finally:
            conn.close()

        log_debug(f"Applied mesh materials and part attributes to {db_path}")

    def build_mdl(self, db_path: Path, mdl_path: Path, game_path: str) -> None:
        """Run ConsoleTools to convert the DB to a .mdl file."""
        if not game_path:
            raise RuntimeError("Game path not set; cannot build MDL")

        subprocess.check_call(
            [
                str(self.textools_dir / "ConsoleTools.exe"),
                "/wrap",
                str(db_path),
                str(mdl_path),
                game_path,
                "/mats",
                "/attributes",
            ],
            cwd=self.textools_dir,
            shell=True,
        )

        log_debug(f"Built MDL at {mdl_path}")
