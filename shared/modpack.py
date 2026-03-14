"""Utilities for PMP (modpack) handling.

Handles temporary working directories and common modpack operations.
"""

from __future__ import annotations

from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Dict, Generator, Iterable, List, Tuple
from pathlib import Path


from .logging import log_debug, log_error, log_info, log_warning

from ..xivpy.pmp import GroupOption, ModGroup, Modpack


def find_or_create_group(
    modpack: Modpack, group_name: str, description: str = ""
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
    group: ModGroup, option_name: str, description: str = ""
) -> GroupOption:
    """Get or create an option within a group."""
    options: List[GroupOption] = group.Options or []
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
    option: GroupOption, game_path: str, rel_path: Path
) -> str:
    """Add a file to a GroupOption and return (mdl_path, rel_path)."""
    if option.Files is None:
        option.Files = {}

    option.Files[game_path] = rel_path.as_posix()
    return rel_path.as_posix()


def update_live_modpack(
    modpack_root: Path,
    mdl_files: Iterable[Path],
    target_group_name: str,
    game_path: str,
) -> None:

    if not modpack_root.exists() or not modpack_root.is_dir():
        raise ValueError(
            f"Modpack root does not exist or is not a directory: {modpack_root}"
        )

    try:
        mp = Modpack.from_folder(modpack_root)
    except Exception as e:
        raise RuntimeError(f"Target folder is not a valid modpack: {e}")

    new_files: Dict[Path, str] = _prepare_files_to_copy_single(
        mdl_files, target_group_name, game_path, mp
    )

    try:
        mp.to_folder(modpack_root, new_files=new_files)

        log_info(
            f"Live install update completed for group {target_group_name}."
        )
    except Exception as e:
        raise RuntimeError(f"Modpack live install update failed: {e}")


def update_packed_modpack(
    pmp_path: Path,
    mdl_files: Iterable[Path],
    target_group_name: str,
    game_path: str,
) -> None:
    if not pmp_path.exists() or not pmp_path.is_file():
        raise ValueError(f"PMP file does not exist: {pmp_path}")

    with pmp_work_context(pmp_path) as (modpack, temp_work):
        new_files: Dict[Path, str] = _prepare_files_to_copy_single(
            mdl_files, target_group_name, game_path, modpack
        )

        save_modpack_versioned(modpack, pmp_path, temp_work, new_files)


def _prepare_files_to_copy_single(
    mdl_files: Iterable[Path], group_name: str, game_path: str, mp: Modpack
) -> dict[Path, str]:
    """Prepare mapping of local MDL files to modpack paths for a single group."""
    if not game_path:
        raise ValueError(
            "`game_path` is required when calling update_live_modpack with a single group"
        )

    files_to_copy: dict[Path, str] = {}

    group = find_or_create_group(mp, group_name)

    for mdl_file in mdl_files:
        option_name = mdl_file.stem
        option = find_or_create_option(group, option_name)

        internal_path = Path(group_name) / mdl_file.name
        mdl_path = mdl_file.resolve()

        rel_path = add_file_to_option(option, game_path, internal_path)
        files_to_copy[mdl_path] = rel_path

        log_info(
            f"Prepared live install for {mdl_path} to {internal_path} in modpack."
        )

    return files_to_copy


@contextmanager
def pmp_work_context(
    pmp_path: Path,
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
    stem: str = pmp_path.stem
    suffix: str = pmp_path.suffix
    parent: Path = pmp_path.parent

    version = 1
    while True:
        versioned: Path = parent / f"{stem}_v{version}{suffix}"
        if not versioned.exists():
            return versioned
        version += 1


def save_modpack_versioned(
    modpack: Modpack,
    pmp_path: Path,
    temp_work: Path,
    new_files: dict[Path, str] = dict(),
) -> Path:
    """Save a modpack, adding a version suffix when needed."""
    new_pmp_path: Path = get_versioned_pmp_path(pmp_path)

    log_debug(f"Saving modpack to {new_pmp_path}")
    modpack.to_folder(temp_work, new_files)
    modpack.to_archive(temp_work, new_pmp_path.parent, new_pmp_path.stem)

    log_info(f"Saved modpack to {new_pmp_path.name}")
    return new_pmp_path
