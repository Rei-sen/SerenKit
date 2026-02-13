import json

from io          import BytesIO
from enum        import IntFlag
from typing      import Self
from dataclasses import dataclass, field, fields, asdict

from ...utils    import BinaryReader
from .helpers    import KaosHelper, KaosContext


class FieldKind(IntFlag):
    VOID    = 0x0
    BYTE    = 0x1
    INTEGER = 0x2
    FLOAT   = 0x3

    FLOAT_4  = 0x4   
    FLOAT_8  = 0x5   
    FLOAT_12 = 0x6  
    FLOAT_16 = 0x7  

    REFERENCE = 0x8
    STRUCT    = 0x9
    STRING    = 0xA
    
    IS_ARRAY  = 0x10    
    IS_TUPLE  = 0x20    
    BASE_MASK = 0xF

class DefinitionHelper(KaosHelper):

    @classmethod
    def from_dict(cls, input: dict) -> Self:
        field_names = {field.name for field in fields(cls)}
        
        filtered_input = {}
        for key, value in input.items():
            if key in field_names:
                filtered_input[key] = value
            else:
                print(f"Unknown field: {key} in {cls.__name__}")
        
        return cls(**filtered_input)
    
@dataclass
class Kind(DefinitionHelper):
    base_type : FieldKind        = FieldKind(0)
    type_name : str              = ""
    arr_type  : FieldKind | None = None
    tuple_size: int              = 0

    def __post_init__(self) -> None:
        if isinstance(self.base_type, int):
            self.base_type = FieldKind(self.base_type)

        if isinstance(self.arr_type, int):
            self.arr_type = FieldKind(self.arr_type)

    def __str__(self) -> str:
        result = self.base_type.name
        
        if self.type_name:
            result += f"({self.type_name})"
        
        if self.arr_type == FieldKind.IS_ARRAY:
            result = f"Array[{result}]"
        elif self.arr_type == FieldKind.IS_TUPLE:
            result = f"Tuple[{result}, {self.tuple_size}]"
            
        return result

@dataclass
class Field(DefinitionHelper):
    name: str  = ""
    kind: Kind = None

    def __post_init__(self) -> None:
        if isinstance(self.kind, dict):
            self.kind = Kind.from_dict(self.kind)

    @classmethod
    def from_bytes(cls, context: KaosContext, reader: BinaryReader) -> 'Field':
        field = cls()

        field.name = field.read_string(reader, context.strings)
        kind_data  = field.read_hki32(reader)

        field_kind = FieldKind(kind_data & FieldKind.BASE_MASK)
        is_array   = (kind_data & FieldKind.IS_ARRAY) != 0
        is_tuple   = (kind_data & FieldKind.IS_TUPLE) != 0

        tuple_size = field.read_hki32(reader) if is_tuple else 0

        if is_tuple:
            arr_type = FieldKind.IS_TUPLE
        elif is_array:
            arr_type = FieldKind.IS_ARRAY
        else:
            arr_type = None

        if field_kind in (FieldKind.REFERENCE, FieldKind.STRUCT):
            kind_name = field.read_string(reader, context.strings)
        else:
            kind_name = ""
        
        field.kind = Kind(
                        base_type  = field_kind,
                        type_name  = kind_name,
                        arr_type   = arr_type,
                        tuple_size = tuple_size
                    )
        
        return field
    
    def write(self, context: KaosContext, file: BytesIO) -> None:
        self.write_string(file, self.name, context.written)

        kind_data = self.kind.base_type.value
        if self.kind.arr_type:
            kind_data |= self.kind.arr_type
        
        self.write_hki32(file, kind_data)

        if self.kind.arr_type == FieldKind.IS_TUPLE:
            self.write_hki32(file, self.kind.tuple_size)

        if self.kind.base_type in (FieldKind.REFERENCE, FieldKind.STRUCT):
            self.write_string(file, self.kind.type_name, context.written)

    def __str__(self) -> str:
        return f"{self.name}: {self.kind}"
    
@dataclass
class Definition(DefinitionHelper):
    name   : str          = ""
    version: int          = -1
    parent : 'Definition' = None
    fields : list[Field]  = field(default_factory=list)

    def __post_init__(self) -> None:
        if isinstance(self.parent, dict):
            self.parent = Definition.from_dict(self.parent)

        if all(isinstance(field, dict) for field in self.fields):
            self.fields = [Field.from_dict(field) for field in self.fields]

    @classmethod
    def from_bytes(cls, context: KaosContext, reader: BinaryReader) -> 'Definition':
        defn = cls()

        defn.name    = defn.read_string(reader, context.strings)
        
        defn.version = defn.read_hki32(reader)
        defn.parent  = context.definitions[defn.read_hki32(reader)]
        field_count  = defn.read_hki32(reader)
        for _ in range(field_count):
            defn.fields.append(Field.from_bytes(context, reader))

        return defn
    
    def write(self, context: KaosContext, file: BytesIO) -> None:
        self.write_string(file, self.name, context.written)
        self.write_hki32(file, self.version)

        if self.parent:
            self.write_hki32(file, context.get_definition_idx(self.parent.name))
        else:
            self.write_hki32(file, 0)

        self.write_hki32(file, len(self.fields))
        for field in self.fields:
            field.write(context, file)

    def get_fields(self) -> list[Field]:
        if not self.parent:
            return self.fields
        else:
            return self.parent.get_fields() + self.fields
        
    def get_definitions(self) -> set[str]:
        defn = {self.name}
        if self.parent:
            defn.update(self.parent.get_definitions())

        return defn

    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=4)

    def __str__(self) -> str:
        header = f"Definition '{self.name}' (v{self.version}, parent={self.parent})"
        
        if self.fields:
            field_summary = f"  {len(self.fields)} fields:"
            field_lines = [f"    {field}" for field in self.fields]
            return header + "\n" + field_summary + "\n" + "\n".join(field_lines)
        else:
            return header + " (no fields)"
    