from __future__ import annotations
from contextlib import contextmanager
from typing import Generator, Iterable

import bpy
from bpy.types import Collection, Object


@contextmanager
def tmp_collection(name: str) -> Generator[Collection, None, None]:
    """Context manager to create a temporary collection for export, ensuring cleanup after use."""

    col = bpy.data.collections.new(name)

    try:
        yield col
    finally:
        _cleanup_collection(col)


def _cleanup_collection(collection: Collection) -> None:
    """Helper function to clean up a collection by unlinking and removing its objects."""
    for obj in list(collection.objects):
        collection.objects.unlink(obj)
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def duplicate_collection(
    source_col: Collection, target_col: Collection
) -> None:
    """Duplicate objects from `source_col` into `target_col`, optionally linking instead of copying."""
    for obj in source_col.objects:
        obj_copy = obj.copy()
        # if obj.data:
        #     obj_copy.data = obj.data.copy()
        target_col.objects.link(obj_copy)


def duplicate_objects_to_collection(
    objects: Iterable[Object],
    target_col: Collection,
) -> dict[Object, Object]:
    copied_objects: dict[Object, Object] = dict()

    for obj in objects:
        if obj.type != "MESH":
            continue
        obj_copy = _duplicate_mesh(obj)
        copied_objects[obj] = obj_copy
        target_col.objects.link(obj_copy)

    return copied_objects


def _duplicate_mesh(obj: Object) -> Object:
    """Duplicate a mesh object, copying its data and returning the new object."""
    obj_copy = obj.copy()
    return obj_copy
