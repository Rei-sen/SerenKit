

from typing import Iterator, Literal, Protocol, SupportsIndex, TypeVar


T = TypeVar("T")


class BlenderCollectionProperty(Protocol[T]):

    def add(self) -> T: ...

    def remove(self, index: int) -> None: ...

    def __len__(self) -> int: ...

    def __iter__(self) -> Iterator[T]: ...

    def __getitem__(self, index: SupportsIndex) -> T: ...

    def __setitem__(self, index: SupportsIndex, value: T) -> None: ...


OperatorReturn = Literal[
    'RUNNING_MODAL',
    'CANCELLED',
    'FINISHED',
    'PASS_THROUGH',
    'INTERFACE'
]
