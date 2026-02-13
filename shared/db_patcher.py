"""Database patching utilities for MDL file modifications.

Handles applying material and attribute changes to MDL database files.
"""

from sqlite3 import Cursor


def apply_mesh_materials(cur: Cursor, material_info: dict[int, str]) -> None:
    """Apply material assignments to the MDL database."""
    for mesh_id, mat_name in material_info.items():
        cur.execute("""
            INSERT OR REPLACE INTO materials (material_id, name)
            VALUES (?, ?)
        """, (mesh_id, mat_name))

        cur.execute("""
            UPDATE meshes
            SET material_id = ?
            WHERE mesh = ?
        """, (mesh_id, mesh_id))


def apply_part_attributes(
    cur: Cursor,
    part_attrs: dict[tuple[int, int], list[str]]
) -> None:
    """Write part attributes into the MDL database."""
    for (mesh, part), attrs in part_attrs.items():
        cur.execute("""
            UPDATE parts
            SET attributes = ?
            WHERE mesh = ? AND part = ?
        """, (",".join(attrs), mesh, part))
