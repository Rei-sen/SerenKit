from io          import BytesIO
from typing      import TYPE_CHECKING
from dataclasses import dataclass, field

from ...utils    import BinaryReader

if TYPE_CHECKING:
    from .node       import Node
    from .definition import Definition


@dataclass
class KaosContext:
    read_mode  : bool               = True
    version    : int                = -1
    definitions: list['Definition'] = None
    strings    : list[str]          = None
    nodes      : list['Node']       = None
    references : list[int]          = None
    pending    : dict[int, int]     = field(default_factory=dict)

    written    : dict[str, int]     = field(default_factory=dict)
    def_indices: dict[str, int]     = field(default_factory=dict)
    node_to_ref: dict[int, int]     = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.read_mode:
            self.pending = {}
        else:
            self.written = {"": 0, None: 1}
            self.node_to_ref = {node_idx: ref_idx for ref_idx, node_idx in enumerate(self.references)}

    def get_definition(self, name: str) -> 'Definition':
        if not self.def_indices:
            self._create_def_dict()
            
        idx = self.def_indices.get(name, False)
        return self.definitions[idx]
    
    def get_definition_idx(self, name: str) -> int | None:
        if not self.def_indices:
            self._create_def_dict()
            
        return self.def_indices.get(name, None)
    
    def _create_def_dict(self) -> None:
        for idx, defn in enumerate(self.definitions):
            name = defn.name if defn else None
            self.def_indices[name] = idx

class KaosHelper:
    
    def read_hki32(self, reader: BinaryReader) -> int:
        '''Variable length integer. Consumes one byte at a time. 
        First bit is the negative sign, next 6 bits are the values, the last one is the continuation bit.'''
        byte     = reader.read_byte()
        negative = byte & 1 == 1
        value    = (byte >> 1) & 0x3F

        shift = 6
        while (byte & 0x80) != 0:
            byte   = reader.read_byte()
            value |= (byte & 0x7F) << shift
            shift += 7
        
        return -value if negative else value

    def read_string(self, reader: BinaryReader, strings: list[str]) -> str:
        length = self.read_hki32(reader)
        if length <= 0:
            return strings[-length]
        
        string = reader.read_string(length)
        strings.append(string)
        return string
    
    def read_bitfield(self, reader: BinaryReader, count: int) -> list[bool]:
        bytes  = (count + 7) // 8
        buffer = reader.read_bytes(bytes)

        bitfield: list[bool] = []
        for byte in buffer:
            for bit_idx in range(8):
                mask   = 1 << bit_idx
                is_set = (byte & mask) != 0
                bitfield.append(is_set)
        
        if any(bitfield[count:]):
            raise ValueError("Found unexpected bit set after count in bitfield.")
        
        return bitfield[:count]
    
    def write_hki32(self, file: BytesIO, value: int) -> None:
        negative = value < 0
        value    = abs(value)

        byte    = ((value & 0x3F) << 1) | negative
        value >>= 6

        to_write: list[int] = []
        while value:
            to_write.append(byte | 0x80)
            byte  = value & 0x7F
            value = value >> 7
        
        to_write.append(byte)

        file.write(bytes(to_write))
    
    def write_string(self, file: BytesIO, string: str, written: dict[str, int]) -> None:
        idx = written.get(string, False)
        if idx:
            self.write_hki32(file, -idx)
        else:
            length = len(string)
            self.write_hki32(file, length)
            file.write(string.encode())
            written[string] = len(written)
    
    def write_bitfield(self, file: BytesIO, field_mask: list[bool]) -> None:
        count    = (len(field_mask) + 7) // 8
        bitfield = sum(1 << bit_idx for bit_idx, is_set in enumerate(field_mask) if is_set)
        file.write(bitfield.to_bytes(count, byteorder='little'))
