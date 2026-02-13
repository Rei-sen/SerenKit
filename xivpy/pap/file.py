from io          import BytesIO
from struct      import pack

from .header     import FileHeader, AnimInfo
from ..kaos      import Tagfile
from ..utils     import BinaryReader, write_alignment


class XIVAnim:
    MAGIC = 0x20706170

    def __init__(self):
        self.version: int        = 0
        self.header : FileHeader = FileHeader()

        self.anim_info: list[AnimInfo] = []

        self.kaos     : Tagfile = Tagfile()
        self.remaining: bytes   = b''

    @classmethod
    def from_file(cls, file_path: str) -> 'XIVAnim':
        with open(file_path, 'rb') as pap:
            return cls.from_bytes(pap.read())

    @classmethod
    def from_bytes(cls, data: bytes) -> 'XIVAnim':
        pap   = cls()
        reader = BinaryReader(data)
        if reader.read_uint32() != pap.MAGIC:
            raise Exception("Not an XIV Animation")
        
        pap.version = reader.read_uint32()
        pap.header  = FileHeader.from_bytes(reader)

        reader.pos    = pap.header.anim_offset
        pap.anim_info = [AnimInfo.from_bytes(reader) for _ in range(pap.header.anim_count)]
        
        reader.pos = pap.header.hk_offset
        pap.kaos   = Tagfile.from_bytes(reader)

        pap.remaining = reader.data[pap.header.timeline_offset:]

        return pap
    
    def to_file(self, file_path: str) -> None:
        with open(file_path, 'wb') as pap:
            pap.write(self.to_bytes())
    
    def to_bytes(self) -> bytes:
        file = BytesIO()

        return file.getvalue()
