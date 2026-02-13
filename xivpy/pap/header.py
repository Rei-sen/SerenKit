from io          import BytesIO
from struct      import pack
from dataclasses import dataclass, field

from .enums      import SkeletonType
from ..utils     import BinaryReader, write_null_string


@dataclass
class FileHeader:
    anim_count     : int          = 0 #ushort
    char_id        : int          = 0 #ushort
    char_type      : SkeletonType = None
    variant        : int          = 0 #ubyte

    anim_offset    : int          = 0 
    hk_offset      : int          = 0
    timeline_offset: int          = 0

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> 'FileHeader':
        header = cls()

        header.anim_count      = reader.read_uint16()
        header.char_id         = reader.read_uint16()
        header.char_type       = SkeletonType(reader.read_byte())
        header.variant         = reader.read_byte()

        header.anim_offset     = reader.read_uint32()
        header.hk_offset       = reader.read_uint32()
        header.timeline_offset = reader.read_uint32()

        return header

    def write(self, file: BytesIO) -> None:
        file.write(pack('<H', self.anim_count))
        file.write(pack('<H', self.char_id))
        file.write(pack('<B', self.char_type.value))
        file.write(pack('<B', self.variant))

        file.write(pack('<I', self.anim_offset))
        file.write(pack('<I', self.hk_offset))
        file.write(pack('<I', self.timeline_offset))

@dataclass
class AnimInfo:
    name  : str = ""
    type  : int = 0 #ushort
    hk_idx: int = 0 #ushort
    face  : int = 0 

    anim_offset    : int          = 0 
    hk_offset      : int          = 0
    timeline_offset: int          = 0

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> 'AnimInfo':
        info = cls()

        info.name   = reader.read_string(32)
        info.type   = reader.read_uint16()
        info.hk_idx = reader.read_uint16()
        info.face   = reader.read_uint32()

        return info

    def write(self, file: BytesIO) -> None:
        write_null_string(file, self.name, 32)
        file.write(pack('<H', self.type))
        file.write(pack('<H', self.hk_idx))
        file.write(pack('<I', self.face))
