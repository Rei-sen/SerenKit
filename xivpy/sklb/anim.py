from io          import BytesIO
from struct      import pack
from dataclasses import dataclass, field

from .enums      import AnimConst
from ..utils     import BinaryReader


@dataclass
class AnimLayer:
    id          : int       = 0
    bone_count  : int       = 0                           #ushort
    bone_indices: list[int] = field(default_factory=list) #ushort

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> 'AnimLayer':
        layer = cls()

        layer.id   = reader.read_uint32()
        bone_count = reader.read_uint16()
        for _ in range(bone_count):
            layer.bone_indices.append(reader.read_uint16())
 
        return layer
    
    def write(self, file: BytesIO) -> None:
        file.write(pack('<I', self.id))
        file.write(pack('<H', len(self.bone_indices)))
        for idx in self.bone_indices:
            file.write(pack('<H', idx))

@dataclass
class AnimData:
    layer_count: int             = 0 #ushort
    offsets    : list[int]       = field(default_factory=list)     
    layers     : list[AnimLayer] = field(default_factory=list)     

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> 'AnimData':
        data     = cls()
        anim_pos = reader.pos

        if reader.read_uint32() != AnimConst.SIG.value:
            raise Exception("Unrecognised animation layer.")
        
        offsets: list[int] = []
        layer_count = reader.read_uint16()
        for _ in range(layer_count):
            offsets.append(reader.read_uint16())
        
        for offset in offsets:
            reader.pos = anim_pos + offset
            data.layers.append(AnimLayer.from_bytes(reader))
            
        return data
    
    def write(self, file: BytesIO, anim_pos: int) -> None:
        layer_count = len(self.layers)
        file.write(pack('<I', AnimConst.SIG.value))
        file.write(pack('<H', layer_count))

        offset_pos         = file.tell()
        offsets: list[int] = []
        for _ in range(layer_count):
            file.write(pack('<H', 0))
        
        for layer in self.layers:
            offsets.append(file.tell() - anim_pos)
            layer.write(file)
        
        end_pos = file.tell()
        file.seek(offset_pos)
        for offset in offsets:
            file.write(pack('<H', offset))
        
        file.seek(end_pos)
