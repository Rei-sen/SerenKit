
import types
import sys
from types import ModuleType

from .helpers import Context, Collection, Object, Operator, PropertyGroup, Mesh, Scene, Model


def _ensure_bpy_shim():
    """Provide a minimal `bpy` shim for tests."""

    _bpy = ModuleType("bpy")
    sys.modules.setdefault("bpy", _bpy)

    _bpy.types = ModuleType("bpy.types")
    sys.modules.setdefault("bpy.types", _bpy.types)

    _bpy.types.Context = Context
    _bpy.types.Collection = Collection
    _bpy.types.Object = Object
    _bpy.types.Operator = Operator
    _bpy.types.PropertyGroup = PropertyGroup
    _bpy.types.Scene = Scene
    _bpy.types.Mesh = Mesh
    _bpy.types.Armature = Object
    _bpy.types.UILayout = type("UILayout", (), {})

    _bpy.props = ModuleType("bpy.props")
    sys.modules.setdefault("bpy.props", _bpy.props)

    # Provide no-op factories for property definitions
    def _noop(*args, **kwargs):
        return None

    for name in ("PointerProperty", "CollectionProperty", "StringProperty",
                 "EnumProperty", "IntProperty", "BoolProperty"):
        setattr(_bpy.props, name, _noop)


_ensure_bpy_shim()
