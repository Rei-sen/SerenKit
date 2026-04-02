import bpy

from .preprocessing import (
    MODKIT_PT_PreprocessingPanel,
    MODKIT_UL_preprocessing_action,
)


_CLASSES = [
    MODKIT_UL_preprocessing_action,
    MODKIT_PT_PreprocessingPanel,
]


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
