from dataclasses  import dataclass
from numpy.typing import NDArray

from ....utils import BinaryReader


@dataclass
class Elements:
    translations: NDArray | None = None 
    rotations   : NDArray | None = None 
    scale       : NDArray | None = None 
    floats      : NDArray | None = None 

    @classmethod
    def from_bytes(cls, reader: BinaryReader, trs_count: int, rot_count: int, scl_count: int, float_count: int) -> 'Elements':
        section = cls()

        section.translations = reader.read_to_ndarray('<H', trs_count)
        section.rotations    = reader.read_to_ndarray('<H', rot_count)
        section.scale        = reader.read_to_ndarray('<H', scl_count)
        section.floats       = reader.read_to_ndarray('<H', float_count)

        return section

@dataclass
class StaticValues:
    translations: NDArray | None = None 
    rotations   : NDArray | None = None 
    scale       : NDArray | None = None 
    floats      : NDArray | None = None 

    @classmethod
    def from_bytes(cls, reader: BinaryReader, trs_count: int, rot_count: int, scl_count: int, float_count: int) -> 'StaticValues':
        section = cls()

        section.translations = reader.read_to_ndarray('<f', trs_count)
        section.rotations    = reader.read_to_ndarray('<H', rot_count * 3)
        section.scale        = reader.read_to_ndarray('<f', scl_count)
        section.floats       = reader.read_to_ndarray('<f', float_count)

        return section

@dataclass
class DynamicRanges:
    translations: NDArray | None = None 
    rotations   : NDArray | None = None 
    scale       : NDArray | None = None 
    floats      : NDArray | None = None 

    @classmethod
    def from_bytes(cls, reader: BinaryReader, trs_count: int, scl_count: int, float_count: int) -> 'DynamicRanges':
        section = cls()

        section.translations = reader.read_to_ndarray('<f', trs_count)
        section.scale        = reader.read_to_ndarray('<f', scl_count)
        section.floats       = reader.read_to_ndarray('<f', float_count)

        return section
