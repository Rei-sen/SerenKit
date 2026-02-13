import numpy as np

from numpy        import float32, int32
from typing       import TYPE_CHECKING
from collections  import defaultdict
from numpy.typing import NDArray 

from .vmath       import normalise_quats

if TYPE_CHECKING:
    from ..nodes import hkaSkeletonNode


def dequantise_quaternions(quat_data: NDArray, bone_count: int, rot_indices: NDArray, bindings: NDArray) -> NDArray:
    quaternions = np.zeros((bone_count, quat_data.shape[1], 4))
    quaternions[:, :, 3] = 1.0

    x_indices = rot_indices      
    y_indices = rot_indices + 1  
    z_indices = rot_indices + 2  

    x_val = quat_data[x_indices, :]
    y_val = quat_data[y_indices, :]
    z_val = quat_data[z_indices, :]
    
    comp_idx = ((y_val >> 14) & 2) | ((x_val >> 15) & 1)
    sign_bit = (z_val >> 15) != 0
    
    MASK_15BIT = 0x7FFF  
    x_quant = x_val & MASK_15BIT
    y_quant = y_val & MASK_15BIT
    z_quant = z_val & MASK_15BIT

    MIDPOINT = 16383 
    x_signed = x_quant.astype(int32) - MIDPOINT
    y_signed = y_quant.astype(int32) - MIDPOINT
    z_signed = z_quant.astype(int32) - MIDPOINT

    FRACTAL = float32(0.000043161)
    a = x_signed * FRACTAL
    b = y_signed * FRACTAL
    c = z_signed * FRACTAL

    d_squared = 1.0 - a*a - b*b - c*c
    d_squared = np.maximum(d_squared, 0.0)

    d = np.sqrt(d_squared)
    d = np.where(sign_bit, -d, d)
    
    temp_quats = np.zeros((len(bindings), quat_data.shape[1], 4), dtype=np.float32)
    for idx_value in range(4):
        mask = (comp_idx == idx_value)
        if not np.any(mask):
            continue  
        
        if idx_value == 0:    # X was omitted
            temp_quats[:, :, 0][mask] = d[mask]
            temp_quats[:, :, 1][mask] = a[mask]
            temp_quats[:, :, 2][mask] = b[mask]
            temp_quats[:, :, 3][mask] = c[mask]
        elif idx_value == 1:  # Y was omitted
            temp_quats[:, :, 0][mask] = a[mask]
            temp_quats[:, :, 1][mask] = d[mask]
            temp_quats[:, :, 2][mask] = b[mask]
            temp_quats[:, :, 3][mask] = c[mask]
        elif idx_value == 2:  # Z was omitted
            temp_quats[:, :, 0][mask] = a[mask]
            temp_quats[:, :, 1][mask] = b[mask]
            temp_quats[:, :, 2][mask] = d[mask]
            temp_quats[:, :, 3][mask] = c[mask]
        else:                 # W was omitted
            temp_quats[:, :, 0][mask] = a[mask]
            temp_quats[:, :, 1][mask] = b[mask]
            temp_quats[:, :, 2][mask] = c[mask]
            temp_quats[:, :, 3][mask] = d[mask]
    
    quaternions[bindings, :, :] = temp_quats
    w_negative  = quaternions[:, :, 3] < 0
    quaternions = np.where(w_negative[:, :, np.newaxis], -quaternions, quaternions)
    
    return normalise_quats(quaternions)

def dequantise_scalars(scalars: NDArray, min: NDArray, span: NDArray) -> NDArray:
    normalised = scalars / float32(65535)
    return min[:, None] + normalised * span[:, None]

def get_child_bones(skeleton: 'hkaSkeletonNode') -> dict[int, set[int]]:
    child_bones = defaultdict(set)
    for bone_idx in range(len(skeleton["bones"])):
        parent_idx = skeleton["parentIndices"][bone_idx]

        if parent_idx > -1:
            child_bones[parent_idx].add(bone_idx)

    return child_bones