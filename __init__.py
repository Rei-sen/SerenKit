
import importlib
import pkgutil
import sys

from .shared.logging import log_error

# Folders to scan for CLASSES
_MODULE_FOLDERS: list[str] = [
    "properties",
    "operators",
    "panels",
]

_COLLECTED_CLASSES: list[type] = []


def _clear_collected_classes() -> None:
    """Clear collected classes."""
    _COLLECTED_CLASSES.clear()


def _collect_preferences_classes() -> None:
    """Collect AddonPreferences classes."""

    _COLLECTED_CLASSES.extend(
        preferences.CLASSES
    )


def _collect_classes() -> None:
    """Collect CLASSES from submodules."""
    base = __package__
    for folder in _MODULE_FOLDERS:
        pkg = f"{base}.{folder}"
        package = importlib.import_module(pkg)
        for _, modname, ispkg in pkgutil.iter_modules(package.__path__):
            if ispkg or modname.startswith("__"):
                continue

            mod_full = f"{pkg}.{modname}"
            try:
                mod = importlib.import_module(mod_full)
                _COLLECTED_CLASSES.extend(getattr(mod, "CLASSES", []))
            except Exception as e:
                log_error(
                    f"Failed to import {mod_full}: {str(e)}")


# Don't import when running outside Blender
if "bpy" in sys.modules:
    import bpy

    from . import preferences

    from .properties import register_properties, unregister_properties
    from .shared.profile import auto_load_profiles

    def register() -> None:
        """Register add-on classes and properties."""
        _clear_collected_classes()

        _collect_classes()
        _collect_preferences_classes()

        for cls in _COLLECTED_CLASSES:
            print(f"Registering class: {cls.__name__}")
            bpy.utils.register_class(cls)

        register_properties()
        auto_load_profiles()

    def unregister() -> None:
        """Unregister add-on classes and properties."""
        unregister_properties()

        for cls in reversed(_COLLECTED_CLASSES):
            bpy.utils.unregister_class(cls)

        _clear_collected_classes()
