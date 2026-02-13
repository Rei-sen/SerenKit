"""Utilities for PMP (modpack) handling.

Handles temporary working directories and common modpack operations.
"""


from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Dict, Generator, List, Tuple
from pathlib import Path


from ..logging import log_debug, log_error, log_info, log_warning

from ...properties.model_settings import ModelSettings

from ...xivpy.pmp import GroupOption, ModGroup, Modpack


def find_or_create_group(
    modpack: Modpack,
    group_name: str,
    description: str = ""
) -> ModGroup:
    """Get or create a modpack group by name."""
    existing = next((g for g in modpack.groups if g.Name == group_name), None)

    if existing is not None:
        log_debug(f"Found existing group: {group_name}")
        return existing

    log_debug(f"Creating new group: {group_name}")
    new_group = ModGroup()
    new_group.Name = group_name
    new_group.Description = description or "Auto-generated from exports"
    new_group.Version = 0
    new_group.Type = "Single"
    new_group.Page = 0
    new_group.Priority = 0
    new_group.Options = []

    modpack.groups.append(new_group)
    return new_group


def find_or_create_option(
    group: ModGroup,
    option_name: str,
    description: str = ""
) -> GroupOption:
    """Get or create an option within a group."""
    options = group.Options or []
    existing = next((o for o in options if o.Name == option_name), None)

    if existing is not None:
        log_debug(f"Found existing option: {option_name}")
        return existing

    log_debug(f"Creating new option: {option_name}")
    new_option = GroupOption()
    new_option.Name = option_name
    new_option.Description = description
    new_option.Priority = 0
    new_option.Files = {}

    if group.Options is None:
        group.Options = []
    group.Options.append(new_option)

    return new_option


def add_file_to_option(
    option: GroupOption,
    game_path: str,
    mdl_path: Path,
    rel_path: Path
) -> tuple[Path, str]:
    """Add a file to a GroupOption and return (mdl_path, rel_path)."""
    if option.Files is None:
        option.Files = {}

    option.Files[game_path] = rel_path.as_posix()
    return (mdl_path, rel_path.as_posix())


def collect_mdl_files_by_collection(export_path: Path) -> Dict[str, List[Path]]:
    """Scan an export folder and collect MDL files by collection."""
    groups_to_create: dict[str, list[Path]] = {}

    for collection_dir in export_path.iterdir():
        if not collection_dir.is_dir():
            continue

        mdl_files = list(collection_dir.glob("*.mdl"))
        if mdl_files:
            groups_to_create[collection_dir.name] = mdl_files
            log_debug(
                f"Found {len(mdl_files)} MDL files in {collection_dir.name}")

    if not groups_to_create:
        raise ValueError("No .mdl files found in export directory")

    log_info(f"Found {len(groups_to_create)} collections with MDL files")
    return groups_to_create


def update_live_modpack(
    modpack_root: Path,
    export_root: Path,
    collections: dict[str, ModelSettings]
) -> dict[str, set[Path]]:
    """Update a modpack from MDL files in an export directory."""
    summary: dict[str, set[Path]] = {"orphans": set(), "duplicates": set()}

    if not modpack_root.exists() or not modpack_root.is_dir():
        raise ValueError(
            f"Modpack root does not exist or is not a directory: {modpack_root}")

    if not export_root.exists() or not export_root.is_dir():
        raise ValueError(
            f"Export root does not exist or is not a directory: {export_root}")

    try:
        mp = Modpack.from_folder(modpack_root)
    except Exception as e:
        raise RuntimeError(f"Target folder is not a valid modpack: {e}")

    groups_to_create = collect_mdl_files_by_collection(export_root)

    new_files = _prepare_files_to_copy(
        groups_to_create, collections, export_root, mp)

    try:
        orphans, duplicates = mp.to_folder(modpack_root, new_files=new_files)
        summary['orphans'] = orphans
        summary['duplicates'] = duplicates
        log_info(
            "Live install update completed. Orphans: "
            f"{len(orphans)}, Duplicates: {len(duplicates)}")
    except Exception as e:
        raise RuntimeError(f"Modpack live install update failed: {e}")

    return summary


def _prepare_files_to_copy(
    groups_to_create: dict[str, list[Path]],
    collections: dict[str, ModelSettings],
    export_root: Path,
    mp: Modpack
) -> dict[Path, str]:
    """Map local MDL files to their modpack archive paths."""
    files_to_copy: list[tuple[Path, str]] = []

    for collection_name, mdl_files in groups_to_create.items():
        model_props = collections.get(collection_name, None)

        if model_props is None:
            log_warning(
                f"Skipping live install for unknown collection: {collection_name}")
            continue

        if model_props.use_custom_export_name and not model_props.export_name:
            log_warning(
                f"Skipping live install for collection with custom export name enabled but no name set: {collection_name}")
            continue

        game_path = model_props.game_path
        if not game_path:
            log_warning(
                f"Skipping live install for collection with no game path: {collection_name}")
            continue

        group_name = model_props.export_name if model_props.use_custom_export_name else collection_name
        group = find_or_create_group(mp, group_name)

        for mdl_file in mdl_files:
            option_name = mdl_file.stem
            option = find_or_create_option(group, option_name)

            internal_path = Path(group_name) / mdl_file.name
            mdl_path = mdl_file.resolve()

            entry = add_file_to_option(
                option, game_path, mdl_path, internal_path)
            files_to_copy.append(entry)

            log_info(
                f"Prepared live install for {mdl_path} to {internal_path} in modpack.")

    return dict(files_to_copy)


@contextmanager
def pmp_work_context(
    pmp_path: Path
) -> Generator[Tuple[Modpack, Path], None, None]:
    """Temporary working context for PMP operations (extracts and cleans up)."""
    if not pmp_path.exists():
        raise FileNotFoundError(f"PMP file not found: {pmp_path}")

    try:
        modpack = Modpack.from_archive(pmp_path)
        log_debug(f"Loaded modpack from {pmp_path.name}")
    except Exception as e:
        log_error(f"Failed to load modpack: {e}")
        raise

    with TemporaryDirectory() as temp_dir:
        temp_work = Path(temp_dir)
        try:
            Modpack.extract_archive(pmp_path, temp_work)
            log_debug(f"Extracted modpack to {temp_work}")
            yield modpack, temp_work
        except Exception as e:
            log_error(f"Failed to extract modpack: {e}")
            raise


def get_versioned_pmp_path(pmp_path: Path) -> Path:
    """Generate a versioned PMP filename to avoid overwriting."""
    stem = pmp_path.stem
    suffix = pmp_path.suffix
    parent = pmp_path.parent

    version = 1
    while True:
        versioned = parent / f"{stem}_v{version}{suffix}"
        if not versioned.exists():
            return versioned
        version += 1


def save_modpack_versioned(
    modpack: Modpack,
    pmp_path: Path,
    temp_work: Path,
    new_files: dict[Path, str] = dict()
) -> Path:
    """Save a modpack, adding a version suffix when needed."""
    new_pmp_path = get_versioned_pmp_path(pmp_path)

    log_debug(f"Saving modpack to {new_pmp_path}")
    modpack.to_folder(temp_work, new_files)
    modpack.to_archive(temp_work, new_pmp_path.parent, new_pmp_path.stem)

    log_info(f"Saved modpack to {new_pmp_path.name}")
    return new_pmp_path
