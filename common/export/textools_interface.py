from pathlib import Path
from typing import Mapping

from ..part_id import PartID


class TextoolsInterface:
    _base_dir: Path

    _consoletools_executable: Path
    _db_converter_path: Path
    _db_converter_executable: Path

    def __init__(self, dir: Path):
        self._base_dir = dir
        if not self._base_dir.is_dir():
            raise ValueError(f"Directory {dir} does not exist")

        self._consoletools_executable = self._base_dir / "ConsoleTools.exe"
        self._db_converter_path = self._base_dir / "converters" / "fbx"
        self._db_converter_executable = (
            self._db_converter_path / "converter.exe"
        )

        if not self._consoletools_executable.is_file():
            raise ValueError(
                f"ConsoleTools executable not found at {self._consoletools_executable}"
            )
        if not self._db_converter_executable.is_file():
            raise ValueError(
                f"DB Converter executable not found at {self._db_converter_executable}"
            )

    