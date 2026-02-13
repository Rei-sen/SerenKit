import numpy as np

from typing       import TYPE_CHECKING
from numpy        import uint16, float32
from numpy.typing import NDArray

from .header      import AnimHeader
from ..helpers    import dequantise_quaternions, dequantise_scalars
from .sections    import Elements, StaticValues, DynamicRanges
from ....utils    import BinaryReader

if TYPE_CHECKING:
    from ...nodes import hkaQuantizedAnimationNode


# All ints in this format are ushorts
class QuantisedAnimation:

    def __init__(self) -> None:
        self.header = AnimHeader()

        self.static_elements  = Elements()
        self.dynamic_elements = Elements()

        self.static_values = Elements()
        self.range_min     = Elements()
        self.range_span    = Elements()

        self.translations: NDArray = None
        self.rotations   : NDArray = None
        self.scale       : NDArray = None
        self.floats      : NDArray = None
        self.raw_frames  : bytes   = b''

        self.tracks: dict[int, NDArray] = {}
    
    @classmethod
    def from_bytes(cls, node: 'hkaQuantizedAnimationNode', tracks_to_idx: list[int]) -> 'QuantisedAnimation':
        anim   = cls()
        reader = BinaryReader(node["data"])

        tracks_to_idx  = np.array(tracks_to_idx)
        pre_frame_size = reader.read_uint16()
        anim.header    = AnimHeader.from_bytes(reader)
        header         = anim.header

        reader.pos = header.static_element_offset
        anim.static_elements = Elements.from_bytes(reader, header.static_trs, header.static_rot, header.static_scl, header.static_floats)

        reader.pos = header.dynamic_element_offset
        anim.dynamic_elements = Elements.from_bytes(reader, header.dynamic_trs, header.dynamic_rot, header.dynamic_scl, header.dynamic_floats)

        reader.pos = header.static_values_offset
        anim.static_values = StaticValues.from_bytes(reader, header.static_trs, header.static_rot, header.static_scl, header.static_floats)

        reader.pos = header.dynamic_range_min_offset
        anim.range_min = DynamicRanges.from_bytes(reader, header.dynamic_trs, header.dynamic_scl, header.dynamic_floats)

        reader.pos = header.dynamic_range_span_offset
        anim.range_span = DynamicRanges.from_bytes(reader, header.dynamic_trs, header.dynamic_scl, header.dynamic_floats)
        
        #Inputting the static values into the pose arrays
        trs, rot, scl, floats = anim._create_frame_arrays(anim.header.frame_count)
        buffer_size     = anim.header.frame_count * anim.header.frame_size
        frame_data      = reader.data[pre_frame_size: pre_frame_size + buffer_size]
        anim.raw_frames = frame_data[:]

        all_frames  = np.frombuffer(frame_data, uint16)
        all_frames  = all_frames.reshape(anim.header.frame_count, anim.header.frame_size // 2)

        trs_start   = 0
        rot_start   = trs_start + anim.header.dynamic_trs
        scl_start   = rot_start + anim.header.dynamic_rot
        float_start = scl_start + anim.header.dynamic_scl

        if anim.header.dynamic_trs:
            trs_end = trs_start + anim.header.dynamic_trs 
            anim._scalars(trs, all_frames[:, trs_start: trs_end].T, "translations")
            anim.translations = trs

        if anim.header.dynamic_rot:
            rot_end = rot_start + anim.header.dynamic_rot * 3
            dynamic_indices = anim.dynamic_elements.rotations[:, None] + np.arange(3)
            rot[dynamic_indices.ravel(), :] = all_frames[:, rot_start: rot_end].T

            rot_indices    = np.concatenate([anim.static_elements.rotations, anim.dynamic_elements.rotations])
            anim.rotations = dequantise_quaternions(rot, anim.header.bone_count, np.sort(rot_indices), tracks_to_idx)
            
        if anim.header.dynamic_scl:
            scl_end = scl_start + anim.header.dynamic_scl
            anim._scalars(scl, all_frames[:, scl_start: scl_end].T, "scale")
            anim.scale = scl

        if anim.header.dynamic_floats:
            float_end = float_start + anim.header.dynamic_floats
            anim._scalars(floats, all_frames[:, float_start: float_end].T, "floats")
            anim.floats = floats

        anim._create_tracks(tracks_to_idx)

        return anim
    
    def _create_frame_arrays(self, frame_count: int) -> tuple[NDArray, ...]:

        def get_max_index(static_arr: NDArray, dynamic_arr: NDArray) -> int:
            indices = []
            if len(static_arr) > 0:
                indices.append(static_arr.max())
            if len(dynamic_arr) > 0:
                indices.append(dynamic_arr.max())
            return max(indices) if indices else -1

        trs_len   = self.header.bone_count * 12
        rot_len   = get_max_index(self.static_elements.rotations, self.dynamic_elements.rotations) + 1
        scl_len   = get_max_index(self.static_elements.scale, self.dynamic_elements.scale) + 1
        float_len = get_max_index(self.static_elements.floats, self.dynamic_elements.floats) + 1

        translations = np.zeros((trs_len, frame_count), float32)
        rotations    = np.zeros((rot_len + 2 if rot_len else 0, frame_count), uint16)
        scale        = np.zeros((scl_len, frame_count), float32)
        floats       = np.zeros((float_len, frame_count), float32)

        translations[self.static_elements.translations, :] = self.static_values.translations[:, None]

        rot_indices = self.static_elements.rotations[:, None] + np.arange(3)
        rotations[rot_indices.ravel()] = self.static_values.rotations[:, None]

        scale[self.static_elements.scale, :]   = self.static_values.scale[:, None]
        floats[self.static_elements.floats, :] = self.static_values.floats[:, None]

        return translations, rotations, scale, floats

    def _scalars(self, array: NDArray, scalars: NDArray, container: str) -> None:
        array[getattr(self.dynamic_elements, container), :] = dequantise_scalars(
                                                                            scalars,
                                                                            getattr(self.range_min, container),
                                                                            getattr(self.range_span, container),
                                                                        )
    
    def _create_tracks(self, track_to_idx: NDArray) -> None:
        for bone_idx in track_to_idx:
            trs_start = bone_idx * 12
            self.tracks[bone_idx] = self.translations.copy()[trs_start: trs_start + 12, :]
            
            anim_rot = self.rotations[bone_idx, :, :].copy()
            self.tracks[bone_idx][4:8, :] = anim_rot.T.copy()

    def get_tracks(self) -> dict[int, NDArray]:
        return {track: array.copy() for track, array in self.tracks.items()}
    