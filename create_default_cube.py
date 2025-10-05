"""
Create a default cube transformation for testing.
This places the cube at a reasonable position in the NTU Front Gate scene.
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
import pandas as pd

# Load point cloud to find a good default position
points3D_df = pd.read_pickle("data/points3D.pkl")
xyz = np.vstack(points3D_df['XYZ'])

# Find center of point cloud
center = np.mean(xyz, axis=0)
print(f"Point cloud center: {center}")

# Place cube at median camera position for best visibility across frames
# Camera trajectory: X∈[-3.45, 6.50], Y∈[-0.84, -0.03], Z∈[-0.17, 4.59]
# Median: (0.20, -0.17, 1.65)
# Place cube slightly in front and to the side
cube_position = np.array([
    0.5,      # Near median X, visible from most frames
    -0.3,     # Near median Y
    1.3       # In front of median Z (closer to viewer)
])

# No rotation (aligned with world axes)
cube_rotation_euler = np.array([0.0, 0.0, 0.0])  # degrees

# Slightly larger scale so it's more visible when closer
cube_scale = 0.6

# Create transformation matrix
r_mat = R.from_euler('xyz', cube_rotation_euler, degrees=True).as_matrix()
scale_mat = np.eye(3) * cube_scale
transform_mat = np.concatenate([scale_mat @ r_mat, cube_position.reshape(3, 1)], axis=1)

# Create cube vertices (unit cube centered at origin, then offset)
base_vertices = np.array([
    [0, 0, 0],
    [1, 0, 0],
    [1, 1, 0],
    [0, 1, 0],
    [0, 0, 1],
    [1, 0, 1],
    [1, 1, 1],
    [0, 1, 1]
], dtype=np.float64)

# Apply transformation
vertices_homogeneous = np.concatenate([base_vertices, np.ones([8, 1])], axis=1)
transformed_vertices = (transform_mat @ vertices_homogeneous.T).T

print(f"\nCube transformation matrix (3x4):")
print(transform_mat)
print(f"\nCube position: {cube_position}")
print(f"Cube rotation (euler xyz): {cube_rotation_euler} degrees")
print(f"Cube scale: {cube_scale}")

# Save the transformation
np.save('cube_transform_mat.npy', transform_mat)
np.save('cube_vertices.npy', transformed_vertices)

print(f"\n✓ Saved cube_transform_mat.npy")
print(f"✓ Saved cube_vertices.npy")
print(f"\nCube is now CLOSER to the viewer!")
print(f"Run: python3 ar_cube_video.py")
