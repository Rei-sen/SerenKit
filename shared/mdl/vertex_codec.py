from __future__ import annotations

from struct import pack, unpack_from
from typing import Literal

from .structures import MdlVertex


SkinningWeightCount = Literal[4, 8]

BASE_VERTEX_FORMAT = "<ffffffff"
BASE_VERTEX_STRIDE = 32
VERTEX_FORMAT_4 = "<ffffffffBBBBBBBB"
VERTEX_FORMAT_8 = "<ffffffffBBBBBBBBBBBBBBBB"
VERTEX_STRIDE_4 = 40
VERTEX_STRIDE_8 = 48

# Backward-compatible alias for callers that assume the original fixed layout.
VERTEX_STRIDE = VERTEX_STRIDE_4


def vertex_stride(skinning_weights: SkinningWeightCount) -> int:
    return VERTEX_STRIDE_8 if skinning_weights == 8 else VERTEX_STRIDE_4


def skinning_weight_count(vertex: MdlVertex) -> SkinningWeightCount:
    weights = list(vertex.bone_weights)
    while len(weights) < 8:
        weights.append(0.0)
    if any(weight > 0.0 for weight in weights[4:8]):
        return 8
    return 4


def _quantize_weights(
    weights: tuple[float, ...], count: SkinningWeightCount
) -> tuple[int, ...]:
    return tuple(
        max(0, min(255, int(round(weights[i] * 255.0)))) for i in range(count)
    )


def _normalize_skinning(vertex: MdlVertex) -> tuple[list[int], list[float]]:
    indices = list(vertex.bone_indices)
    weights = list(vertex.bone_weights)
    while len(indices) < 8:
        indices.append(0)
    while len(weights) < 8:
        weights.append(0.0)
    return indices[:8], weights[:8]


def encode_vertex(
    vertex: MdlVertex, skinning_weights: SkinningWeightCount = 4
) -> bytes:
    indices, normalized_weights = _normalize_skinning(vertex)

    if skinning_weights == 8:
        weights = _quantize_weights(tuple(normalized_weights), 8)
        return pack(
            VERTEX_FORMAT_8,
            vertex.position[0],
            vertex.position[1],
            vertex.position[2],
            vertex.normal[0],
            vertex.normal[1],
            vertex.normal[2],
            vertex.uv0[0],
            vertex.uv0[1],
            indices[0],
            indices[1],
            indices[2],
            indices[3],
            indices[4],
            indices[5],
            indices[6],
            indices[7],
            weights[0],
            weights[1],
            weights[2],
            weights[3],
            weights[4],
            weights[5],
            weights[6],
            weights[7],
        )

    weights = _quantize_weights(tuple(normalized_weights), 4)
    return pack(
        VERTEX_FORMAT_4,
        vertex.position[0],
        vertex.position[1],
        vertex.position[2],
        vertex.normal[0],
        vertex.normal[1],
        vertex.normal[2],
        vertex.uv0[0],
        vertex.uv0[1],
        indices[0],
        indices[1],
        indices[2],
        indices[3],
        weights[0],
        weights[1],
        weights[2],
        weights[3],
    )


def decode_vertex(
    buffer: bytes,
    offset: int,
    bone_table: list[int],
    skinning_weights: SkinningWeightCount = 4,
) -> MdlVertex:
    fmt = VERTEX_FORMAT_8 if skinning_weights == 8 else VERTEX_FORMAT_4
    values = unpack_from(fmt, buffer, offset)

    index_count = 8 if skinning_weights == 8 else 4
    local_indices = tuple(values[8 + i] for i in range(index_count))

    global_indices = []
    for local_idx in local_indices:
        if 0 <= local_idx < len(bone_table):
            global_indices.append(bone_table[local_idx])
        else:
            global_indices.append(0)

    while len(global_indices) < 8:
        global_indices.append(0)

    raw_weights = [
        values[8 + index_count + i] / 255.0 for i in range(index_count)
    ]
    while len(raw_weights) < 8:
        raw_weights.append(0.0)

    return MdlVertex(
        position=(values[0], values[1], values[2]),
        normal=(values[3], values[4], values[5]),
        uv0=(values[6], values[7]),
        bone_indices=(
            global_indices[0],
            global_indices[1],
            global_indices[2],
            global_indices[3],
            global_indices[4],
            global_indices[5],
            global_indices[6],
            global_indices[7],
        ),
        bone_weights=(
            raw_weights[0],
            raw_weights[1],
            raw_weights[2],
            raw_weights[3],
            raw_weights[4],
            raw_weights[5],
            raw_weights[6],
            raw_weights[7],
        ),
    )


def decode_u16(buffer: bytes, offset: int) -> int:
    return unpack_from("<H", buffer, offset)[0]
