from dataclasses import dataclass
from typing import Protocol


class ProgressReporter(Protocol):
    """Interface for reporting export progress to the UI.
    """

    def set_total_collection_count(self, count: int) -> None:
        ...

    def set_total_variant_count(self, count: int) -> None:
        ...

    def start_new_collection(self, name: str, local_total: int) -> None:
        ...

    def increment_variant_index(self) -> None:
        ...

    def clear(self) -> None:
        ...


@dataclass
class ExportProgress:
    """Tracker for export progress across an entire session.
    """

    collection_name: str = ""
    collection_index: int = 0
    collection_count: int = 0

    local_idx: int = 0
    local_variant_count: int = 0

    processed_variants: int = 0
    total_variant_count: int = 0

    def set_total_collection_count(self, count: int) -> None:
        self.collection_count = count

    def set_total_variant_count(self, count: int) -> None:
        self.total_variant_count = count

    def start_new_collection(self, name: str, local_total: int) -> None:
        self.collection_name = name
        self.collection_index += 1
        self.local_idx = 0
        self.local_variant_count = local_total

    def increment_variant_index(self) -> None:
        self.local_idx += 1
        self.processed_variants += 1

    def clear(self) -> None:
        self.collection_name = ""
        self.collection_index = 0
        self.collection_count = 0
        self.local_idx = 0
        self.local_variant_count = 0
        self.processed_variants = 0
        self.total_variant_count = 0
