from contextlib import ExitStack, contextmanager
from typing import Generator, Iterable

import bpy
from bpy.types import ID, Object, Mesh


@contextmanager
def override_object_data(obj: Object) -> Generator[None, None, None]:
    """Duplicate the data of a mesh object and return the new data block."""
    if not obj.data:
        raise ValueError(f"Object '{obj.name}' has no data to duplicate")

    old = obj.data
    obj.data = old.copy()

    try:
        yield
    finally:
        restore_object_data(obj, old)


@contextmanager
def override_objects_data(
    objects: Iterable[Object],
) -> Generator[None, None, None]:

    with ExitStack() as stack:
        for obj in objects:
            if not obj.data:
                continue
            stack.enter_context(override_object_data(obj))
        yield


def duplicate_object_data(obj: Object) -> ID:
    """Duplicate the data of a mesh object and return the new data block."""
    if not obj.data:
        raise ValueError(f"Object '{obj.name}' has no data to duplicate")
    data_copy = obj.data.copy()
    obj.data = data_copy

    return data_copy


def restore_object_data(obj: Object, original_data: ID) -> None:
    """Restore the original data of a mesh object."""

    old = obj.data
    obj.data = original_data
    if isinstance(old, Mesh):
        bpy.data.meshes.remove(old)
