from dataclasses import dataclass

from ....utils import BinaryReader


@dataclass
class AnimHeader:
    # All ints in this format are ushorts
    tracks     : int = 0
    bone_count : int = 0
    float_count: int = 0
    frame_count: int = 0
    duration   : float = 0.0

    static_trs   : int = 0
    static_rot   : int = 0
    static_scl   : int = 0
    static_floats: int = 0

    dynamic_trs   : int = 0
    dynamic_rot   : int = 0
    dynamic_scl   : int = 0
    dynamic_floats: int = 0

    frame_size: int = 0
    static_element_offset : int = 0
    dynamic_element_offset: int = 0
    static_values_offset  : int = 0

    dynamic_range_min_offset : int = 0
    dynamic_range_span_offset: int = 0

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> 'AnimHeader':
        header = cls()

        header.bone_count  = reader.read_uint16()
        header.float_count = reader.read_uint16()
        header.frame_count = reader.read_uint16()
        header.duration    = reader.read_float()

        header.static_trs    = reader.read_uint16()
        header.static_rot    = reader.read_uint16()
        header.static_scl    = reader.read_uint16()
        header.static_floats = reader.read_uint16()

        header.dynamic_trs    = reader.read_uint16()
        header.dynamic_rot    = reader.read_uint16()
        header.dynamic_scl    = reader.read_uint16()
        header.dynamic_floats = reader.read_uint16()

        header.frame_size = reader.read_uint16()
        header.static_element_offset  = reader.read_uint16()
        header.dynamic_element_offset = reader.read_uint16()
        header.static_values_offset   = reader.read_uint16()

        header.dynamic_range_min_offset  = reader.read_uint16()
        header.dynamic_range_span_offset = reader.read_uint16()

        return header