from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .blender_builder import build_model_from_blender_objects
from .writer import model_to_bytes


ProgressFn = Callable[[str, float], None]


def export_blender_objects_to_mdl(
    objects: Iterable[Any],
    output_path: Path,
    progress: ProgressFn | None = None,
) -> Path:
    """Directly export Blender mesh objects to MDL (MVP static mesh path)."""

    model = build_model_from_blender_objects(objects, progress=progress)
    data = model_to_bytes(model, progress=progress)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)

    return output_path
