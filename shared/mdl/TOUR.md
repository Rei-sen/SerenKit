# MDL Code Tour

This folder contains SerenKit's standalone MDL implementation.

## Main Flow

1. Blender extraction:
- `build_model_from_blender_objects` in `blender_builder.py`
- Reads mesh geometry, UVs, material slots, armature weights, and shape key deltas.
- Produces a high-level `MdlModel`.

2. Binary writing:
- `to_binary_model` and `model_to_bytes` in `writer.py`
- Converts `MdlModel` into `MdlBinaryModel` and writes MDL bytes.
- Handles:
  - vertex/index buffers
  - bone tables
  - shape replacement-vertex payloads
  - string tables and metadata blocks

3. Binary parsing:
- `from_bytes` in `parser.py`
- Reads `MdlBinaryModel` from bytes and converts back to `MdlModel`.
- Reconstructs shape key deltas by comparing base and replacement vertices.

## Key Modules

- `structures.py`
: High-level export model used by SerenKit logic (`MdlModel`, `MdlMesh`, `MdlVertex`, shape structs).

- `binary_model.py`
: Low-level MDL container (`MdlBinaryModel`) with top-level read/write orchestration.

- `binary_structs.py`
: Binary structs for headers, mesh/submesh, LOD, vertex declarations, bone tables, shape blocks.

- `binary_io.py`
: Minimal binary reader and padding helpers.

- `vertex_codec.py`
: Shared vertex packing/unpacking format.
  - `VERTEX_STRIDE`
  - `encode_vertex`
  - `decode_vertex`

- `checks.py`
: Invariant validation.
  - `validate_model`: checks high-level data before writing.
  - `validate_binary_model`: checks low-level bounds and references before parsing/writing.

## Most Important Functions

- `build_model_from_blender_objects` (`blender_builder.py`)
: Entry for Blender -> `MdlModel`.

- `to_binary_model` (`writer.py`)
: Core build step for `MdlModel` -> `MdlBinaryModel`.

- `model_to_bytes` (`writer.py`)
: Final writer entrypoint.

- `from_bytes` (`parser.py`)
: Parser entrypoint for MDL bytes -> `MdlModel`.

- `MdlBinaryModel.to_bytes` / `MdlBinaryModel.from_bytes` (`binary_model.py`)
: Low-level serializer/parser backbone.

## Safety Checks

- Writer path calls:
  - `validate_model` before packing.
  - `validate_binary_model` before returning binary model.

- Parser path calls:
  - `validate_binary_model` immediately after reading low-level model.

These checks catch common invalid states early (bad indices, bad bone references, buffer overflows, invalid table references).
