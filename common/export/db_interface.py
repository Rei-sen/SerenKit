from pathlib import Path
from sqlite3 import Connection, Cursor
import sqlite3
from typing import Iterable, Mapping

from ..part_id import PartID


class DBInterface:

    _conn: Connection
    _cur: Cursor

    def __init__(self, db_path: Path) -> None:
        self._conn = sqlite3.connect(db_path, autocommit=True)
        self._cur = self._conn.cursor()

    def __del__(self) -> None:
        self._cur.close()
        self._conn.close()

    def apply_materials(self, material_mapping: Mapping[int, str]) -> None:
        for mesh_id, mat_name in material_mapping.items():

            self._cur.execute(
                """
                INSERT OR REPLACE INTO materials (material_id, name)
                VALUES (?, ?)
            """,
                (mesh_id, mat_name),
            )

            self._cur.execute(
                """
                UPDATE meshes
                SET material_id = ?
                WHERE mesh = ?
            """,
                (mesh_id, mesh_id),
            )

    def apply_attributes(
        self, attributes: Mapping[PartID, Iterable[str]]
    ) -> None:
        for (mesh, part), attrs in attributes.items():
            self._cur.execute(
                """
                UPDATE parts
                SET attributes = ?
                WHERE mesh = ? AND part = ?
            """,
                (",".join(attrs), mesh, part),
            )
