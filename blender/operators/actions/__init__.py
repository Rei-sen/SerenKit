from bpy.utils import register_class, unregister_class

from .add_action import (
    MODKIT_OT_add_preprocessing_action,
)
from .del_action import MODKIT_OT_delete_preprocessing_action


def register():
    register_class(MODKIT_OT_add_preprocessing_action)

    register_class(MODKIT_OT_delete_preprocessing_action)


def unregister():
    unregister_class(MODKIT_OT_add_preprocessing_action)

    unregister_class(MODKIT_OT_delete_preprocessing_action)
