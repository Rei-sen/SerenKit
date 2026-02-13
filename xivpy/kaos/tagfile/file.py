from io          import BytesIO
from enum        import Enum
from typing      import TYPE_CHECKING

from .node       import Node
from ...utils    import BinaryReader
from .helpers    import KaosHelper, KaosContext
from .definition import Definition

if TYPE_CHECKING:
    from ..nodes  import hkaSkeletonNode, hkaAnimationContainerNode


class TagType(Enum):
    FILE = 1
    DEF  = 2
    NODE = 4
    END  = 7
    
class Tagfile(KaosHelper):
    MAGIC = 0xD011FACECAB00D1E

    def __init__(self):
        self.version    : int              = -1
        self.ver_str    : str              = ""
        self.definitions: list[Definition] = [None]
        self.strings    : list[str]        = ["", None]
        self.nodes      : list[Node]       = []
        self.references : list[int]        = [-1]
        self.root_idx   : int              = None
        self.context    : KaosContext      = None

    @classmethod
    def from_bytes(cls, reader: BinaryReader) -> 'Tagfile':
        kaos = cls()
        if reader.read_uint64() != kaos.MAGIC:
            raise Exception("Unexpected magic in Tagfile.")
        
        kaos.create_context()
        sections = 0
        while True:
            sections += 1
            tag = kaos.read_hki32(reader)
            match TagType(tag):
                case TagType.FILE:
                    kaos.version = kaos.read_hki32(reader)
                    if kaos.version not in (3, 5):
                        raise Exception(f"Unsupported Version: {kaos.version}")
                    elif kaos.version == 5:
                        kaos.ver_str = kaos.read_string(reader, kaos.strings)
                        reader.pos += 6

                    kaos.context.version = kaos.version

                case TagType.DEF:
                    kaos.definitions.append(Definition.from_bytes(kaos.context, reader))

                case TagType.NODE:
                    Node.from_bytes(kaos.context, reader)

                case TagType.END:
                    print("End of tagfile")
                    break

                case _:
                    raise Exception(f"Unknown Tag: {tag}")
        
        if kaos.context.pending:
            raise Exception("Tagfile: Pending references remaining.")
        if any(node is None for node in kaos.nodes):
            raise Exception("Tagfile: Unresolved nodes.")
        
        kaos.root_idx = kaos.references[1]
        kaos.create_context(read=False)

        return kaos
        
    def write(self, file: BytesIO | None=None) -> bytes:
        if not file:
            file = BytesIO()

        self.create_context(read=False)

        file.write(self.MAGIC.to_bytes(8, byteorder='little'))
        self.write_hki32(file, TagType.FILE.value)
        self.write_hki32(file, 3)

        for defn in self.definitions[1:]:
            self.write_hki32(file, TagType.DEF.value)
            defn.write(self.context, file)
        
        for idx in self.references[1:]:
            self.write_hki32(file, TagType.NODE.value)
            self.nodes[idx].write(self.context, file)
        
        self.write_hki32(file, TagType.END.value)

    def unused_definitions(self) -> list[str]:
        if self.root_idx is None:
            raise Exception("Tagfile does not exist or is incomplete.")
        used_definitions = set()
        for node in self.nodes:
            used_definitions.update(node.definition.get_definitions())
        
        not_used = []
        for defn in self.definitions[1:]:
            if defn.name not in used_definitions:
                not_used.append(defn.name)
        
        return not_used
    
    def get_skeleton_node(self) -> 'hkaSkeletonNode':
        if self.root_idx is None:
            raise Exception("Tagfile does not exist or is incomplete.")

        for idx in self.nodes[self.root_idx]["namedVariants"]:
            if self.nodes[idx]["name"] != "hkaAnimationContainer":
                continue

            anim_idx = self.nodes[idx]["variant"]
            skel_idx = self.nodes[anim_idx]["skeletons"][0]
            return self.nodes[skel_idx]
        
        raise Exception("Couldn't find animation skeleton.")
    
    def get_hkbone_idx(self, name: str, skeleton: 'hkaSkeletonNode') -> int | None:
        """Returns the index from the skeleton's bone list, not the node list."""
        for bone_idx, node_idx in enumerate(skeleton.values["bones"]):
            if self.nodes[node_idx]["name"] == name:
                return bone_idx
        
        return None
    
    def get_bone_list(self, skeleton: 'hkaSkeletonNode') -> list[str]:
        bone_indices = skeleton["bones"]
        return [self.nodes[idx]["name"] for idx in bone_indices]
    
    def get_mapper_nodes(self) -> list[tuple[str, Node]]:
        if self.root_idx is None:
            raise Exception("Tagfile does not exist or is incomplete.")

        mapper_nodes = []
        for idx in self.nodes[self.root_idx]["namedVariants"]:
            if self.nodes[idx]["className"] != "hkaSkeletonMapper":
                continue

            map_name = self.nodes[idx]["name"]
            map_idx  = self.nodes[idx]["variant"]
            data_idx = self.nodes[map_idx]["mapping"]
            mapper_nodes.append((map_name, self.nodes[data_idx]))
        
        return mapper_nodes

    def get_animation_container(self) -> 'hkaAnimationContainerNode':
        for idx in self.nodes[self.root_idx]["namedVariants"]:
            if self.nodes[idx]["name"] != "hkaAnimationContainer":
                continue
            
            variant = self.nodes[idx]["variant"]
            return self.nodes[variant]
        
        raise Exception("Couldn't find animation container.")

    def create_context(self, read=True) -> KaosContext:
        self.context = KaosContext(
                            read_mode=read,
                            definitions=self.definitions,
                            strings=self.strings,
                            nodes=self.nodes,
                            references=self.references,
                        )
