import numpy as np

from typing       import TYPE_CHECKING
from numpy.typing import NDArray
 
from .enums       import Space
from .vmath       import frame_matrices, ROT_MAT_90X
from .helpers     import get_child_bones
from .quantised   import QuantisedAnimation

if TYPE_CHECKING:
    from ..nodes import hkaSkeletonNode, hkaAnimationBindingNode


def create_raw_tracks(animation: QuantisedAnimation, binding: 'hkaAnimationBindingNode', bone_list: list[str]) -> dict[str, dict]:
    tracks = animation.get_tracks()
    return {bone_list[track]: tracks[track] for track in binding["transformTrackToBoneIndices"]} 

def create_matrix_tracks(
        animation: QuantisedAnimation, 
        skeleton: 'hkaSkeletonNode', 
        binding: 'hkaAnimationBindingNode',  
        bone_list: list[str], 
        space: Space = Space.NATIVE
        ) -> dict[str, NDArray]:
    
    if isinstance(space, str):
        space = Space(space)

    if "blendHint" in binding and binding["blendHint"] != 0:
        raise ValueError("Unsupported Blend Hint")
    
    frames      = animation.header.frame_count
    bone_count  = len(skeleton["bones"])
    
    binding_set = set(binding["transformTrackToBoneIndices"])
    child_bones = get_child_bones(skeleton)
    tracks = animation.get_tracks()
    
    all_tracks = {}
    ref_pose   = skeleton["referencePose"]
    for bone_idx in range(bone_count):
        if bone_idx in binding_set:
            all_tracks[bone_idx] = tracks[bone_idx]
        else:
            all_tracks[bone_idx] = np.tile(ref_pose[bone_idx][:, np.newaxis], (1, frames))

    for bone_idx in range(bone_count):
        if skeleton["parentIndices"][bone_idx] == -1:
            visit(bone_idx, skeleton, child_bones, all_tracks, space)

    return {bone_list[track]: all_tracks[track] for track in binding["transformTrackToBoneIndices"]} 

def visit(bone_idx: int, skeleton: 'hkaSkeletonNode', child_bones: dict[int, set[int]], tracks: dict[int, NDArray], space: Space):
    parent_idx = skeleton["parentIndices"][bone_idx]
    calc_arma_matrix(bone_idx, parent_idx, tracks, space)

    for idx in child_bones[bone_idx]:
        visit(idx, skeleton, child_bones, tracks, space)

def calc_arma_matrix(bone_idx: int, parent_idx: int, tracks: dict[int, NDArray], space: Space) -> None:
    trs    = tracks[bone_idx][ :3, :]
    rot    = tracks[bone_idx][4:8, :]

    local_matrices = frame_matrices(trs, rot)
    
    if parent_idx == -1:
        if space == "BLENDER":
            tracks[bone_idx] = np.einsum('ij,jkn->ikn', ROT_MAT_90X, local_matrices)
        else:
            tracks[bone_idx] = local_matrices

    else:
        parent_arm = tracks[parent_idx]
        tracks[bone_idx] = np.einsum('ijn,jkn->ikn', parent_arm, local_matrices)
