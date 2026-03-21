from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


SHAPEKEY_EXPORT_PREFIXES = ("shp_", "shpx_")

from .structures import (
    MdlMesh,
    MdlModel,
    MdlShapeDelta,
    MdlShapeKey,
    MdlSubmesh,
    MdlVertex,
)


ProgressFn = Callable[[str, float], None]


@dataclass
class BlenderBuildSettings:
    triangulate: bool = True


def _default_progress(_: str, __: float) -> None:
    return


def _resolve_bone_names(obj: Any) -> list[str]:
    names: list[str] = []

    armature_obj = getattr(obj, "parent", None)
    if (
        armature_obj is not None
        and getattr(armature_obj, "type", None) == "ARMATURE"
    ):
        bones = getattr(getattr(armature_obj, "data", None), "bones", None)
        if bones is not None:
            names.extend([b.name for b in bones])

    for mod in getattr(obj, "modifiers", []):
        if getattr(mod, "type", None) != "ARMATURE":
            continue
        arm_obj = getattr(mod, "object", None)
        bones = getattr(getattr(arm_obj, "data", None), "bones", None)
        if bones is None:
            continue
        for bone in bones:
            if bone.name not in names:
                names.append(bone.name)

    return names


def _vertex_bone_data(
    obj: Any,
    source_vertex_index: int,
    bone_lookup: dict[str, int],
) -> tuple[
    tuple[int, int, int, int, int, int, int, int],
    tuple[float, float, float, float, float, float, float, float],
]:
    source_vertex = obj.data.vertices[source_vertex_index]
    groups = getattr(source_vertex, "groups", [])
    vgroups = getattr(obj, "vertex_groups", [])

    weighted: list[tuple[int, float]] = []
    for g in groups:
        group_idx = getattr(g, "group", -1)
        weight = float(getattr(g, "weight", 0.0))
        if group_idx < 0 or group_idx >= len(vgroups):
            continue
        name = vgroups[group_idx].name
        if name not in bone_lookup:
            continue
        weighted.append((bone_lookup[name], weight))

    weighted.sort(key=lambda x: x[1], reverse=True)
    weighted = weighted[:8]

    if not weighted:
        return (0, 0, 0, 0, 0, 0, 0, 0), (
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )

    total = sum(w for _, w in weighted)
    if total <= 0:
        total = 1.0

    norm = [(idx, w / total) for idx, w in weighted]
    while len(norm) < 8:
        norm.append((0, 0.0))

    return (
        norm[0][0],
        norm[1][0],
        norm[2][0],
        norm[3][0],
        norm[4][0],
        norm[5][0],
        norm[6][0],
        norm[7][0],
    ), (
        norm[0][1],
        norm[1][1],
        norm[2][1],
        norm[3][1],
        norm[4][1],
        norm[5][1],
        norm[6][1],
        norm[7][1],
    )


def _is_export_shapekey_name(name: str) -> bool:
    lowered = name.lower()
    return lowered.startswith(SHAPEKEY_EXPORT_PREFIXES)


def _co_to_tuple(co: Any) -> tuple[float, float, float]:
    return (float(co.x), float(co.y), float(co.z))


def _qf(value: float) -> float:
    # Quantize float keys so tiny numeric noise does not defeat dedup.
    return round(value, 6)


def _vertex_dedup_key(
    source_vertex_index: int,
    position: tuple[float, float, float],
    normal: tuple[float, float, float],
    uv0: tuple[float, float],
    bone_indices: tuple[int, int, int, int, int, int, int, int],
    bone_weights: tuple[float, float, float, float, float, float, float, float],
) -> tuple[Any, ...]:
    return (
        source_vertex_index,
        _qf(position[0]),
        _qf(position[1]),
        _qf(position[2]),
        _qf(normal[0]),
        _qf(normal[1]),
        _qf(normal[2]),
        _qf(uv0[0]),
        _qf(uv0[1]),
        bone_indices,
        tuple(_qf(weight) for weight in bone_weights),
    )


def _build_baked_base_positions(
    mesh_data: Any,
) -> list[tuple[float, float, float]] | None:
    sk = getattr(mesh_data, "shape_keys", None)
    if sk is None or not getattr(sk, "key_blocks", None):
        return None

    key_blocks = sk.key_blocks
    if len(key_blocks) < 2:
        return None

    basis = key_blocks[0]
    basis_positions = [_co_to_tuple(point.co) for point in basis.data]
    baked_positions = basis_positions.copy()

    for kb in key_blocks[1:]:
        if _is_export_shapekey_name(getattr(kb, "name", "")):
            continue
        if bool(getattr(kb, "mute", False)):
            continue

        value = float(getattr(kb, "value", 0.0))
        if abs(value) <= 1e-8:
            continue

        for i in range(min(len(basis_positions), len(kb.data))):
            base = basis_positions[i]
            key = _co_to_tuple(kb.data[i].co)
            baked_positions[i] = (
                baked_positions[i][0] + (key[0] - base[0]) * value,
                baked_positions[i][1] + (key[1] - base[1]) * value,
                baked_positions[i][2] + (key[2] - base[2]) * value,
            )

    return baked_positions


def _mesh_vertices_from_object(
    obj: Any,
    bone_lookup: dict[str, int],
) -> dict[int, tuple[list[MdlVertex], list[int]]]:
    mesh = obj.data
    if mesh is None:
        return {}

    mesh.calc_loop_triangles()

    baked_positions = _build_baked_base_positions(mesh)

    uv_layer = None
    if mesh.uv_layers and mesh.uv_layers.active:
        uv_layer = mesh.uv_layers.active.data

    per_material: dict[int, tuple[list[MdlVertex], list[int]]] = {}
    per_material_lookup: dict[int, dict[tuple[Any, ...], int]] = {}

    # Build per-material vertices, deduplicating identical corner payloads.
    # UV seams and hard edges are preserved because UV/normal are part of the key.
    for tri in mesh.loop_triangles:
        mat_idx = int(getattr(tri, "material_index", 0))
        if mat_idx not in per_material:
            per_material[mat_idx] = ([], [])
            per_material_lookup[mat_idx] = {}

        vertices, indices = per_material[mat_idx]
        lookup = per_material_lookup[mat_idx]
        for loop_idx in tri.loops:
            loop = mesh.loops[loop_idx]
            vertex = mesh.vertices[loop.vertex_index]
            src_idx = int(loop.vertex_index)

            uv = (0.0, 0.0)
            if uv_layer is not None:
                raw_uv = uv_layer[loop_idx].uv
                uv = (float(raw_uv.x), float(1.0 - raw_uv.y))

            bone_indices, bone_weights = _vertex_bone_data(
                obj, src_idx, bone_lookup
            )

            position = (
                float(vertex.co.x),
                float(vertex.co.y),
                float(vertex.co.z),
            )
            if baked_positions is not None and 0 <= src_idx < len(
                baked_positions
            ):
                position = baked_positions[src_idx]

            normal = (
                float(loop.normal.x),
                float(loop.normal.y),
                float(loop.normal.z),
            )

            key = _vertex_dedup_key(
                source_vertex_index=src_idx,
                position=position,
                normal=normal,
                uv0=uv,
                bone_indices=bone_indices,
                bone_weights=bone_weights,
            )
            existing_index = lookup.get(key)
            if existing_index is not None:
                indices.append(existing_index)
                continue

            new_index = len(vertices)
            vertices.append(
                MdlVertex(
                    position=position,
                    normal=normal,
                    uv0=uv,
                    bone_indices=bone_indices,
                    bone_weights=bone_weights,
                    source_vertex_index=src_idx,
                )
            )
            lookup[key] = new_index
            indices.append(new_index)

    return per_material


def _collect_object_shapekeys(
    obj: Any, mesh_indices: list[int], model: MdlModel
) -> None:
    mesh_data = obj.data
    sk = getattr(mesh_data, "shape_keys", None)
    if sk is None or not getattr(sk, "key_blocks", None):
        return

    key_blocks = sk.key_blocks
    if len(key_blocks) < 2:
        return

    basis = key_blocks[0]
    epsilon = 1e-6

    for kb in key_blocks[1:]:
        if not _is_export_shapekey_name(kb.name):
            continue

        entry = next((s for s in model.shapekeys if s.name == kb.name), None)
        if entry is None:
            entry = MdlShapeKey(name=kb.name)
            model.shapekeys.append(entry)

        for mesh_idx in mesh_indices:
            mesh = model.lod_meshes[0][mesh_idx]
            deltas: list[MdlShapeDelta] = []
            for i, vert in enumerate(mesh.vertices):
                src_idx = vert.source_vertex_index
                if src_idx < 0:
                    continue

                basis_co = basis.data[src_idx].co
                key_co = kb.data[src_idx].co
                dx = float(key_co.x - basis_co.x)
                dy = float(key_co.y - basis_co.y)
                dz = float(key_co.z - basis_co.z)

                if (
                    abs(dx) <= epsilon
                    and abs(dy) <= epsilon
                    and abs(dz) <= epsilon
                ):
                    continue

                deltas.append(MdlShapeDelta(vertex_index=i, delta=(dx, dy, dz)))

            if deltas:
                entry.mesh_deltas[mesh_idx] = deltas


def build_model_from_blender_objects(
    objects: Iterable[Any],
    settings: BlenderBuildSettings | None = None,
    progress: ProgressFn | None = None,
) -> MdlModel:
    """Convert Blender mesh objects into SerenKit's high-level MDL model.

    The conversion currently targets static meshes and one LOD (LOD0).
    """

    if settings is None:
        settings = BlenderBuildSettings()

    if progress is None:
        progress = _default_progress

    mesh_objects = [
        obj for obj in objects if getattr(obj, "type", None) == "MESH"
    ]
    total = len(mesh_objects)

    model = MdlModel(lod_meshes=[[]])

    # Build a global bone lookup up-front so vertex blend indices are stable.
    bone_names: list[str] = []
    for obj in mesh_objects:
        for bone_name in _resolve_bone_names(obj):
            if bone_name not in bone_names:
                bone_names.append(bone_name)

    model.bones = bone_names
    bone_lookup = {name: idx for idx, name in enumerate(model.bones)}

    progress("collecting_meshes", 0.0)
    for idx, obj in enumerate(mesh_objects):
        per_material = _mesh_vertices_from_object(obj, bone_lookup)
        if not per_material:
            continue

        created_mesh_indices: list[int] = []
        for mat_idx, (vertices, indices) in sorted(
            per_material.items(), key=lambda x: x[0]
        ):
            if not vertices or not indices:
                continue

            material_name = ""
            material_path = ""
            slots = getattr(obj, "material_slots", None)
            if slots and 0 <= mat_idx < len(slots):
                mat = slots[mat_idx].material
                if mat is not None:
                    material_name = mat.name
                    material_path = mat.name

            mesh_name = obj.name
            if len(per_material) > 1:
                mesh_name = f"{obj.name}__mat{mat_idx}"

            mdl_mesh = MdlMesh(
                name=mesh_name,
                material_name=material_name,
                material_path=material_path,
                vertices=vertices,
                indices=indices,
                submeshes=[
                    MdlSubmesh(
                        start_index=0,
                        index_count=len(indices),
                        attribute_mask=0,
                    )
                ],
            )

            model.lod_meshes[0].append(mdl_mesh)
            mesh_index = len(model.lod_meshes[0]) - 1
            created_mesh_indices.append(mesh_index)

            if material_path and material_path not in model.materials:
                model.materials.append(material_path)

        _collect_object_shapekeys(obj, created_mesh_indices, model)

        if total:
            progress("collecting_meshes", float(idx + 1) / float(total))

    progress("collecting_meshes", 1.0)
    return model
