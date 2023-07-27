import numpy as np

def perspective_fov(fov, aspect_ratio, near_plane, far_plane):
    num = 1.0 / np.tan((fov / 2.0)*(3.14/180))
    numa = num / (aspect_ratio)

    return np.array([
        [numa, 0.0, 0.0, 0.0],
        [0.0, num, 0.0, 0.0],
        [0.0, 0.0, - far_plane / (far_plane - near_plane), -1.0],
        [0.0, 0.0, -(far_plane * near_plane) / (far_plane - near_plane), 0.0]
    ])

def look_at(camera_position, camera_target, up_vector):
    forward = np.subtract(camera_position, camera_target)
    forward = forward / np.linalg.norm(forward)

    right = np.cross(up_vector, forward)
    right = right / np.linalg.norm(right)

    up = np.cross(forward, right)
    up = up / np.linalg.norm(up)

    return np.array([
        [right[0], up[0], forward[0], 0.0],
        [right[1], up[1], forward[1], 0.0],
        [right[2], up[2], forward[2], 0.0],
        [-np.dot(right, camera_position), -np.dot(up, camera_position), -np.dot(forward, camera_position), 1.0]
    ])

def viewdir(camera_position, camera_target):
    vector = np.subtract(camera_position,camera_target)
    vector = vector / np.linalg.norm(vector)
    vector = np.array([vector[0],-vector[2],vector[1]])

    return vector