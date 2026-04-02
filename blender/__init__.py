from . import (
    operators,
    panels,
    preprocessing,
    properties,
)

_modules = [
    preprocessing,
    properties,
    operators,
    panels,
]


def register():
    for module in _modules:
        module.register()


def unregister():
    for module in reversed(_modules):
        module.unregister()
