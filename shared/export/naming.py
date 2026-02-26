from ..export_context import CollectionExportInfo

from ..logging import log_error
from ..variants import detect_export_alias, name_variant

from ...properties.model_settings import get_modkit_collection_props
from ...properties.export_properties import ExportSettings


def build_export_name(
    export_settings: ExportSettings,
    info: CollectionExportInfo,
    variant: list[str],
) -> str:
    """Construct an export filename based on the export settings,
    collection, and variant information.
    """

    parts: list[str] = []

    remaining = list(variant)
    mode = export_settings.export_prefix_mode

    col_props = get_modkit_collection_props(info.collection)
    model = col_props.model if col_props else None
    profile_name = model.assigned_profile if model else None

    if mode == "PROFILE":
        if not profile_name:
            col_name = info.collection.name
            log_error(
                f"Collection {col_name} has no assigned variant profile "
                f"but export prefix mode is PROFILE"
            )
            raise RuntimeError(
                "Export prefix mode PROFILE requires an "
                "assigned variant profile on the collection"
            )

        override, remaining = detect_export_alias(remaining, info.profile)

        parts.append(override or profile_name)
    elif mode == "CUSTOM" and export_settings.export_custom_prefix:
        parts.append(export_settings.export_custom_prefix)

    label = name_variant(remaining) if remaining else ""
    if label:
        parts.append(label)

    filename = (" ".join(parts) if parts else (label or "export")) + ".fbx"
    return filename
