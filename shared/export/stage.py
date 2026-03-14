from enum import Enum


class ExportStage(str, Enum):
    DUPLICATE = "duplicate"
    APPLY_SHAPEKEYS = "apply_shapekeys"
    PREPROCESS = "preprocess"
    EXPORT = "export"
    VARIANT = "variant"
