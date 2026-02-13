from enum import Enum


class ProgressStage(str, Enum):
    DUPLICATE = "duplicate"
    APPLY_SHAPEKEYS = "apply_shapekeys"
    PREPROCESS = "preprocess"
    EXPORT = "export"
    VARIANT = "variant"
