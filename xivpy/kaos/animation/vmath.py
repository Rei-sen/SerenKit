import numpy as np

from numpy.typing import NDArray


ROT_MAT_90X = np.array([
                    [1.0,  0.0,  0.0,  0.0],
                    [0.0,  0.0, -1.0,  0.0],
                    [0.0,  1.0,  0.0,  0.0],
                    [0.0,  0.0,  0.0,  1.0]
                ])

def normalise_quats(quaternions: NDArray) -> NDArray:
    magnitudes      = np.sqrt(np.sum(quaternions ** 2, axis=-1))
    magnitudes_safe = np.maximum(magnitudes, 1e-8)
    normalised = quaternions / magnitudes_safe[..., np.newaxis]
    
    return normalised

def quaternion_multiply(q1: NDArray, q2: NDArray, xyzw = True) -> NDArray:
    if xyzw:
        x1, y1, z1, w1 = q1[..., 0], q1[..., 1], q1[..., 2], q1[..., 3]
        x2, y2, z2, w2 = q2[..., 0], q2[..., 1], q2[..., 2], q2[..., 3]
    else:
        w1, x1, y1, z1 = q1[..., 0], q1[..., 1], q1[..., 2], q1[..., 3]
        w2, x2, y2, z2 = q2[..., 0], q2[..., 1], q2[..., 2], q2[..., 3]
    
    result_x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    result_y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    result_z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    result_w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2

    quats = np.stack([result_x, result_y, result_z, result_w], axis=-1)
    
    return normalise_quats(quats)

def quaternion_divide(q1: NDArray, q2: NDArray, xyzw = True) -> NDArray:
    if xyzw:
        x1, y1, z1, w1 = q1[..., 0], q1[..., 1], q1[..., 2], q1[..., 3]
        x2, y2, z2, w2 = q2[..., 0], q2[..., 1], q2[..., 2], q2[..., 3]
    else:
        w1, x1, y1, z1 = q1[..., 0], q1[..., 1], q1[..., 2], q1[..., 3]
        w2, x2, y2, z2 = q2[..., 0], q2[..., 1], q2[..., 2], q2[..., 3]
    
    result_x = w1 * (-x2) + x1 * w2 + y1 * (-z2) - z1 * (-y2)
    result_y = w1 * (-y2) - x1 * (-z2) + y1 * w2 + z1 * (-x2)
    result_z = w1 * (-z2) + x1 * (-y2) - y1 * (-x2) + z1 * w2
    result_w = w1 * w2 - x1 * (-x2) - y1 * (-y2) - z1 * (-z2)
    
    quats = np.stack([result_x, result_y, result_z, result_w], axis=-1)
    return normalise_quats(quats)

def quaternion_divide_reversed(q1: NDArray, q2: NDArray) -> NDArray:
    """Calculate inverse(q2) * q1. Expects xyzw."""
    q1 = normalise_quats(q1)
    q2 = normalise_quats(q2)
  
    # Inverse
    x2, y2, z2, w2 = q2[..., 0], q2[..., 1], q2[..., 2], q2[..., 3]
    inv_q2 = np.stack([-x2, -y2, -z2, w2], axis=-1)
    
    return quaternion_multiply(inv_q2, q1)

def create_matrix(translation: NDArray, rotation: NDArray, scale: NDArray = None, xyzw = True) -> NDArray:
    if scale is None:
        scale = np.array([1.0, 1.0, 1.0])
    
    if xyzw:
        x, y, z, w = rotation
    else:
        w, x, y, z = rotation

    rot = np.array([
        [1 - 2*(y*y + z*z),     2*(x*y - z*w),     2*(x*z + y*w)],
        [    2*(x*y + z*w), 1 - 2*(x*x + z*z),     2*(y*z - x*w)],
        [    2*(x*z - y*w),     2*(y*z + x*w), 1 - 2*(x*x + y*y)]
    ])

    rot = rot @ np.diag(scale)
    
    mat = np.eye(4)
    mat[:3, :3] = rot
    mat[:3, 3] = translation
    
    return mat

def frame_matrices(translation: NDArray, rotation: NDArray, scale: NDArray = None, xyzw = True) -> NDArray:
    frame_count = translation.shape[1]

    if scale is None:
        scale = np.ones((3, frame_count))
    
    if xyzw:
        x = rotation[0, :]
        y = rotation[1, :]
        z = rotation[2, :]
        w = rotation[3, :]
    else:
        w = rotation[0, :]
        x = rotation[1, :]
        y = rotation[2, :]
        z = rotation[3, :]
    
    xx = x * x
    yy = y * y
    zz = z * z
    xy = x * y
    xz = x * z
    yz = y * z
    wx = w * x
    wy = w * y
    wz = w * z
    
    matrices = np.zeros((4, 4, frame_count))

    # Rotations
    matrices[0, 0, :] = 1 - 2 * (yy + zz)
    matrices[0, 1, :] = 2 * (xy - wz)
    matrices[0, 2, :] = 2 * (xz + wy)
    matrices[1, 0, :] = 2 * (xy + wz)
    matrices[1, 1, :] = 1 - 2 * (xx + zz)
    matrices[1, 2, :] = 2 * (yz - wx)
    matrices[2, 0, :] = 2 * (xz - wy)
    matrices[2, 1, :] = 2 * (yz + wx)
    matrices[2, 2, :] = 1 - 2 * (xx + yy)
    
    # Multiply Scale
    matrices[0, 0, :] *= scale[0, :]
    matrices[1, 0, :] *= scale[0, :]
    matrices[2, 0, :] *= scale[0, :]
    matrices[0, 1, :] *= scale[1, :]
    matrices[1, 1, :] *= scale[1, :]
    matrices[2, 1, :] *= scale[1, :]
    matrices[0, 2, :] *= scale[2, :]
    matrices[1, 2, :] *= scale[2, :]
    matrices[2, 2, :] *= scale[2, :]
    
    # Translations
    matrices[0, 3, :] = translation[0, :]
    matrices[1, 3, :] = translation[1, :]
    matrices[2, 3, :] = translation[2, :]
    
    matrices[3, 3, :] = 1.0
    
    return matrices
