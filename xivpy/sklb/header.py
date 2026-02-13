from io          import BytesIO
from struct      import pack
from dataclasses import dataclass, field

from .enums      import AnimConst
from ..utils     import BinaryReader, write_padding


@dataclass
class FileHeader:
    anim_offset     : int       = 0
    hk_offset       : int       = 0
    connect_bone_idx: int       = 0 #ushort
    PADDING                     = 2
    race_id         : int       = 0
    mapper_id       : list[int] = field(default_factory=list)

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> 'FileHeader':
        header = cls()

        header.anim_offset      = reader.read_uint32()
        header.hk_offset        = reader.read_uint32()
        header.connect_bone_idx = reader.read_int16()

        reader.pos += header.PADDING

        header.race_id = reader.read_uint32()
 
        while True:
            id = reader.read_uint32()
            if id in (0xFFFFFFFF, 0x0, AnimConst.SIG.value):
                break
            header.mapper_id.append(id)
    
        return header
    
    def write(self, file: BytesIO) -> None:
        file.write(pack('<I', 0))
        file.write(pack('<I', 0))
        file.write(pack('<h', self.connect_bone_idx))

        file.write(write_padding(self.PADDING))

        file.write(pack('<I', self.race_id))

        for id in self.mapper_id:
            file.write(pack('<I', id))
        
        remaining = max(4 - len(self.mapper_id), 0)
        for _ in range(remaining):
            file.write(pack('<I', 0xFFFFFFFF))

    def get_race_id_str(self, mapper_idx: int | None=None) -> str:
        if mapper_idx is None:
            id = self.race_id
        else:
            id = self.mapper_id[mapper_idx]

        return f"{id:04d}"
  
@dataclass
class OldFileHeader:
    anim_offset  : int       = 0 #ushort
    hk_offset    : int       = 0 #ushort
    race_id      : int       = 0
    mapper_id    : list[int] = field(default_factory=list)
    lod_bone_nums: list[int] = field(default_factory=list) #ushort
    connect_bones: list[int] = field(default_factory=list) #ushort
    

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> 'OldFileHeader':
        header = cls()
 
        header.anim_offset   = reader.read_uint16()
        header.hk_offset     = reader.read_uint16()
        header.race_id       = reader.read_uint32()
        header.mapper_id     = [reader.read_uint32() for _ in range(4)]
        header.lod_bone_nums = [reader.read_uint16() for _ in range(3)]
        header.connect_bones = [reader.read_uint16() for _ in range(4)]

        return header
