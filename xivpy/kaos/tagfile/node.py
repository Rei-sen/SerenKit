import numpy as np

from io           import BytesIO
from struct       import pack
from typing       import Optional, Any
from dataclasses  import dataclass, field
from numpy.typing import NDArray

from ...utils    import BinaryReader
from .helpers    import KaosHelper, KaosContext
from .definition import Definition, Field, FieldKind, Kind


@dataclass
class Node(KaosHelper):
    definition: Definition = None
    field_mask: list[bool] = field(default_factory=list)
    values    : dict[str, Any | list[Any] | bytes | NDArray] = field(default_factory=dict)

    @classmethod
    def from_bytes(cls, context: KaosContext, reader: BinaryReader, definition : Optional[Definition]=None, store_ref=True) -> int:
        node = cls()

        node_idx = len(context.nodes)

        if store_ref:
            ref_idx     = len(context.references)
            pending_ref = context.pending.pop(ref_idx, False)
            if pending_ref:
                node_idx = pending_ref
            
            context.references.append(node_idx)
        
        # Reserve slot in node list
        if node_idx == len(context.nodes):
            context.nodes.append(None)
        
        if not definition:
            def_idx    = node.read_hki32(reader)
            definition = context.definitions[def_idx]

        fields = definition.get_fields()
        node.definition = definition
        node.field_mask = node.read_bitfield(reader, len(fields))
        node.values     = node._read_fields(context, reader, fields, node.field_mask)

        context.nodes[node_idx] = node
        return node_idx
    
    @classmethod
    def from_definition(cls, definition: Definition, fields: set[str]) -> 'Node':

        def is_list(field: Field) -> bool:
            is_list = False
            if field.kind.base_type in (FieldKind.FLOAT_4, FieldKind.FLOAT_8, FieldKind.FLOAT_12, FieldKind.FLOAT_16):
                is_list = True
            elif field.kind.arr_type and field.kind.arr_type in (FieldKind.IS_ARRAY, FieldKind.IS_TUPLE):
                is_list = True
            
            return is_list
        
        node = cls()
        node.definition = definition
        for field in definition.get_fields():
            is_set = field.name in fields
            node.field_mask.append(is_set)
            if not is_set:
                continue
            
            if is_list(field):
                node.values[field.name] = []
            
        return node

    def _read_fields(self, context: KaosContext, reader: BinaryReader, fields: list[Field], field_mask: list[bool]) -> dict:
        field_values = {}
        for is_set, field in zip(field_mask, fields):
            if not is_set:
                continue
            
            if field.kind.arr_type:
                field_values[field.name] = self._read_array(context, reader, field.kind)
            else:
                field_values[field.name] = self._read_value(context, reader, field.kind)
        
        return field_values

    def _read_array(self, context: KaosContext, reader: BinaryReader, kind: Kind) -> list:
        match kind.arr_type:
            case FieldKind.IS_ARRAY:
                count = self.read_hki32(reader)
                return self._read_value_arr(context, reader, kind, count)
            
            case FieldKind.IS_TUPLE:
                  return [self._read_value(context, reader, kind)
                          for _ in range(kind.tuple_size)]  

    def _read_value(self, context: KaosContext, reader: BinaryReader, kind: Kind) -> Any:
        match kind.base_type:
            case FieldKind.BYTE:
                return reader.read_byte()
             
            case FieldKind.INTEGER:
                return self.read_hki32(reader)
            
            case FieldKind.FLOAT:
                return reader.read_float()
            
            case FieldKind.STRING:
                return self.read_string(reader, context.strings)
            
            case FieldKind.STRUCT:
                definition = context.get_definition(kind.type_name)
                return Node.from_bytes(context, reader, definition=definition, store_ref=False)
            
            case FieldKind.REFERENCE:
                return self._read_node_ref(context, reader)
            
            case FieldKind.FLOAT_4 | FieldKind.FLOAT_8 | FieldKind.FLOAT_12 | FieldKind.FLOAT_16:
                count = int(kind.base_type.name.split('_')[1])
                return [reader.read_float() for _ in range(count)]
            
            case _:
                raise ValueError(f"Node: Unknown value type: {kind.base_type}")
               
    def _read_value_arr(self, context: KaosContext, reader: BinaryReader, kind: Kind, count: int) -> list[Any] | bytes | NDArray:

        def read_struct() -> list:
            definition = context.get_definition(kind.type_name)
            fields     = definition.get_fields()
            field_mask = self.read_bitfield(reader, len(fields))
            field_cols = {}
            for is_set, field in zip(field_mask, fields):
                if not is_set:
                    continue
                field_cols[field.name] = self._read_value_arr(context, reader, field.kind, count)

            nodes: list[int] = []
            for idx in range(count):
                values = {field_name: column[idx] for field_name, column in field_cols.items()}

                nodes.append(len(context.nodes))
                context.nodes.append(
                            Node(
                                    definition=definition,
                                    field_mask=field_mask,
                                    values=values
                                )
                            )
            return nodes
        
        match kind.base_type:
            case FieldKind.BYTE:
                data = reader.data[reader.pos: reader.pos + count]
                reader.pos += count
                return data
            
            case FieldKind.INTEGER:
                unknown = self.read_hki32(reader)
                if unknown != 4:
                    raise ValueError("Unknown integer array marker.")
                
                return [self.read_hki32(reader) for _ in range(count)]
            
            case FieldKind.FLOAT:
                return [reader.read_float() for _ in range(count)]
            
            case FieldKind.STRING:
                return [self.read_string(reader, context.strings) for _ in range(count)]
            
            case FieldKind.STRUCT:
                return read_struct()
            
            case FieldKind.REFERENCE:
                return [self._read_node_ref(context, reader) for _ in range(count)]
            
            case FieldKind.FLOAT_4 | FieldKind.FLOAT_8 | FieldKind.FLOAT_12 | FieldKind.FLOAT_16:
                array_size = int(kind.base_type.name.split('_')[1])  
                if array_size == 4:
                    array_size = self.read_hki32(reader)
                    if array_size not in (3, 4):
                        raise ValueError(f"Unexpected array length: {array_size}")
                
                result = reader.read_to_ndarray('<f', array_size * count)
                return result.reshape(count, array_size)
            
            case _:
                raise ValueError(f"Node: Unknown value array type: : {kind.base_type}")

    def _read_node_ref(self, context: KaosContext, reader: BinaryReader) -> int:
        ref_idx = self.read_hki32(reader)

        if ref_idx < len(context.references):
            node_idx = context.references[ref_idx]
            return node_idx
        else:
            reserved_idx = context.pending.get(ref_idx, False)
            if not reserved_idx:
                reserved_idx = len(context.nodes)
                context.nodes.append(None)
                context.pending[ref_idx] = reserved_idx

            return reserved_idx
    
    def write(self, context: KaosContext, file: BytesIO, write_def=True) -> None:
        if write_def:
            self.write_hki32(file, context.get_definition_idx(self.definition.name))
        
        self.write_bitfield(file, self.field_mask)
        for is_set, field in zip(self.field_mask, self.definition.get_fields()):
            if not is_set:
                continue
            
            if field.kind.arr_type:
                self._write_array(context, file, field.kind, self.values[field.name])
            else:
                self._write_value(context, file, field.kind, self.values[field.name])
            
    
    def _write_array(self, context: KaosContext, file: BytesIO, kind: Kind, values: dict) -> None:
        match kind.arr_type:
            case FieldKind.IS_ARRAY:
                self.write_hki32(file, len(values))
                self._write_value_arr(context, file, kind, values)
            
            case FieldKind.IS_TUPLE:
                  for value in values:
                    self._write_value(context, file, kind, value)

    def _write_value(self, context: KaosContext, file: BytesIO, kind: Kind, value: int | float | str | list) -> None:
        match kind.base_type:
            case FieldKind.BYTE:
                file.write(pack('<B', value))
             
            case FieldKind.INTEGER:
                self.write_hki32(file, value)
            
            case FieldKind.FLOAT:
                file.write(pack('<f', value))
            
            case FieldKind.STRING:
                self.write_string(file, value, context.written)
            
            case FieldKind.STRUCT:
                context.nodes[value].write(context, file, write_def=False)
            
            case FieldKind.REFERENCE:
                ref_idx = context.node_to_ref[value]
                self.write_hki32(file, ref_idx)
            
            case FieldKind.FLOAT_4 | FieldKind.FLOAT_8 | FieldKind.FLOAT_12 | FieldKind.FLOAT_16:
                count = int(kind.base_type.name.split('_')[1])
                if len(value) != count:
                    raise Exception("Node: Array mismatch.")
                
                for v in value:
                    file.write(pack('<f', v)) 
            
            case _:
                raise ValueError(f"Node: Unknown value type: {kind.base_type}")
            
    def _write_value_arr(self, context: KaosContext, file: BytesIO, kind: Kind, values: list[Any] | NDArray | bytes) -> None:
        match kind.base_type:
            case FieldKind.BYTE:
                file.write(values)
            
            case FieldKind.INTEGER:
                self.write_hki32(file, 4)
                for value in values:
                    self.write_hki32(file, value)
            
            case FieldKind.FLOAT:
                for value in values:
                    file.write(pack('<f', value))
            
            case FieldKind.STRING:
                for value in values:
                    self.write_string(file, value, context.written)
            
            case FieldKind.STRUCT:
                def_idx    = context.def_indices[kind.type_name]
                fields     = context.definitions[def_idx].get_fields()
                field_mask = context.nodes[values[0]].field_mask
                self.write_bitfield(file, field_mask)

                field_cols  = {field.name: [] for is_set, field in zip(field_mask, fields) if is_set}
                for node_idx in values:
                    node_values = context.nodes[node_idx].values
                    for field_name in field_cols.keys():
                        field_cols[field_name].append(node_values[field_name])

                for is_set, field in zip(field_mask, fields):
                    if not is_set:
                        continue

                    self._write_value_arr(context, file, field.kind, field_cols[field.name])
                    
            case FieldKind.REFERENCE:
                for value in values:
                    ref_idx = context.node_to_ref[value]
                    self.write_hki32(file, ref_idx)
            
            case FieldKind.FLOAT_4 | FieldKind.FLOAT_8 | FieldKind.FLOAT_12 | FieldKind.FLOAT_16:
                if not isinstance(values, np.ndarray):
                    values = np.array(values, dtype=np.float32)

                arr_size = int(kind.base_type.name.split('_')[1])  
                if arr_size == 4:
                    arr_size = values.shape[1]
                    self.write_hki32(file, arr_size)
                
                file.write(values.tobytes())
            
            case _:
                raise ValueError(f"Node: Unknown value type: {kind.base_type}")
    
    @property
    def name(self) -> str:
        if self.definition:
            return self.definition.name
        else:
            return "None"
    
    def __getitem__(self, key: str) -> list | Any:
        return self.values[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        self.values[key] = value

    def __delitem__(self, key: str) -> None:
        del self.values[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self.values
    
    def __len__(self) -> int:
        return len(self.values)
    
    def __str__(self) -> str:
        if not self.definition:
            return "Node (no definition)"
        
        lines = []
        lines.append(f"Node using Definition '{self.definition.name}'")
        lines.append(f"  Version: {self.definition.version}")
        lines.append(f"  Parent: {self.definition.parent}")
        
        if self.field_mask:
            active_count = sum(1 for active in self.field_mask if active)
            lines.append(f"  Active fields: {active_count}/{len(self.field_mask)}")
        
        lines.append("  Field Details:")
        if self.definition.get_fields() and self.field_mask:
            value_idx = 0
            for field, is_set in zip(self.definition.get_fields(), self.field_mask):
                field_info = f"{field.name}: {field.kind}"
                
                if is_set:
                    if field.name in self.values:
                        if field.kind.arr_type == FieldKind.IS_ARRAY:
                            if field.kind.base_type == FieldKind.BYTE:
                                field_values = "<byte data>"
                            elif len(self.values[field.name]) > 500:
                                field_values = "<large array>"
                            else:
                                field_values = self.values[field.name]
                        else:
                            field_values = self.values[field.name]

                        field_info += f" = {field_values}"
                        value_idx  += 1
                    else:
                        field_info += " = <missing value>"
                    field_info = "    (1) " + field_info
                else:
                    field_info = "    (0) " + field_info
                
                lines.append(field_info)
        
        return "\n".join(lines)
     