from io      import BytesIO
from struct  import pack

from .anim   import AnimData
from .enums  import SklbConst
from ..kaos  import Tagfile
from .header import FileHeader, OldFileHeader
from ..utils import BinaryReader, write_alignment


class XIVSkeleton:
    def __init__(self):
        self.version: SklbConst  = SklbConst.V1300
        self.header : FileHeader = FileHeader()

        self.anim_data: AnimData = AnimData()

        self.kaos: Tagfile = Tagfile()

    @classmethod
    def from_file(cls, file_path: str) -> 'XIVSkeleton':
        with open(file_path, 'rb') as skl:
            return cls.from_bytes(skl.read())

    @classmethod
    def from_bytes(cls, data: bytes) -> 'XIVSkeleton':
        sklb   = cls()
        reader = BinaryReader(data)
        if reader.read_uint32() != SklbConst.MAGIC.value:
            raise Exception("Not an XIV Skeleton.")
        
        sklb.version = SklbConst(reader.read_uint32())
        if sklb.version == SklbConst.V1300:
            sklb.header = FileHeader.from_bytes(reader)
        elif sklb.version == SklbConst.V1200:
            sklb.header = OldFileHeader.from_bytes(reader)
        else:
            raise Exception(f"Unsupported skeleton version: {SklbConst(sklb.version)}")

        reader.pos    = sklb.header.anim_offset
        sklb.anim_data = AnimData.from_bytes(reader)
        
        reader.pos = sklb.header.hk_offset
        sklb.kaos  = Tagfile.from_bytes(reader)

        return sklb
    
    def to_file(self, file_path: str) -> None:
        with open(file_path, 'wb') as skl:
            skl.write(self.to_bytes())
    
    def to_bytes(self) -> bytes:
        file = BytesIO()
        file.write(pack('<I', SklbConst.MAGIC.value))
        
        if not (self.version == SklbConst.V1300 and isinstance(self.header, FileHeader)):
            raise Exception(f"Unsopported skeleton version: {SklbConst(self.version)}")
        
        file.write(pack('<I', self.version.value))
        header_pos = file.tell()
        self.header.write(file)
        
        write_alignment(file, alignment=16)

        anim_pos = file.tell()
        self.anim_data.write(file, anim_pos)

        write_alignment(file, alignment=16)

        kaos_pos = file.tell()
        self.kaos.write(file)

        file.seek(header_pos)
        file.write(pack('<I', anim_pos))
        file.write(pack('<I', kaos_pos))

        return file.getvalue()
