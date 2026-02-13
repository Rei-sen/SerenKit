from typing import TYPE_CHECKING, Literal, overload

if TYPE_CHECKING:
    from ..tagfile.node import Node


    class hkBaseObjectNode(Node):
        pass

    class hkReferencedObjectNode(hkBaseObjectNode):
        # This is a parent of several nodes, but its fields are not relevant for file io.
        # Python's type hints will not inherit these overloaded functions.

        @overload
        def __getitem__(self, key: Literal["memSizeAndFlags"]) -> None: ...
        @overload
        def __getitem__(self, key: Literal["referenceCount"]) -> None: ...

        @overload
        def __setitem__(self, key: Literal["memSizeAndFlags"], value: None) -> None: ...
        @overload
        def __setitem__(self, key: Literal["referenceCount"], value: None) -> None: ... 

    class hkRootLevelContainerNode(Node):

        @overload
        def __getitem__(self, key: Literal["namedVariants"]) -> list[int]: ...  # hkRootLevelContainerNamedVariant

        @overload
        def __setitem__(self, key: Literal["namedVariants"], value: list[int]) -> None: ...  # hkRootLevelContainerNamedVariant

    class hkRootLevelContainerNamedVariantNode(Node):

        @overload
        def __getitem__(self, key: Literal["name"]) -> str: ...
        @overload
        def __getitem__(self, key: Literal["className"]) -> str: ...
        @overload
        def __getitem__(self, key: Literal["variant"]) -> int: ...  # hkReferencedObject

        @overload
        def __setitem__(self, key: Literal["name"], value: str) -> None: ...
        @overload
        def __setitem__(self, key: Literal["className"], value: str) -> None: ...
        @overload
        def __setitem__(self, key: Literal["variant"], value: int) -> None: ...  # hkReferencedObject
