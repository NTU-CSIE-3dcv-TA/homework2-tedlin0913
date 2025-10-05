"""
Debug script to check cube visibility in different frames.
"""

import cv2
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
import re

from ar_cube_video import (
    create_cube_voxels,
    apply_transformation,
    project_points,
    quaternion_to_rotation_matrix
)

# Load data
print("Loading data...")
transform_mat = np.load('cube_transform_mat.npy')
cube_vertices = np.load('cube_vertices.npy')
images_df = pd.read_pickle("data/images.pkl")

# Camera parameters
camera_matrix = np.array([[1868.27, 0, 540], [0, 1869.18, 960], [0, 0, 1]])
dist_coeffs = np.array([0.0847023, -0.192929, -0.000201144, -0.000725352])

# Get validation images
validation_images = images_df[images_df["NAME"].str.startswith("valid_")].copy()

def extract_id(name):
    match = re.search(r'(\d+)', name)
    return int(match.group(1)) if match else 0

validation_images['numeric_id'] = validation_images['NAME'].apply(extract_id)
validation_images = validation_images.sort_values('numeric_id')

# Create voxels
voxels, colors = create_cube_voxels(cube_vertices, density=10)
voxels_transformed = apply_transformation(voxels, transform_mat)

print(f"\nAnalyzing {len(validation_images)} frames...")
print(f"Total voxels: {len(voxels)}")

# Check first, middle, and last frames
test_indices = [0, len(validation_images)//2, len(validation_images)-3, len(validation_images)-2, len(validation_images)-1]

for test_idx in test_indices:
    row = validation_images.iloc[test_idx]

    # Get camera pose
    qx, qy, qz, qw = row["QX"], row["QY"], row["QZ"], row["QW"]
    tx, ty, tz = row["TX"], row["TY"], row["TZ"]

    R_mat = quaternion_to_rotation_matrix(qx, qy, qz, qw)
    t_vec = np.array([tx, ty, tz])

    # Project points
    points_2d, depths = project_points(voxels_transformed, R_mat, t_vec, camera_matrix, dist_coeffs)

    # Count visible points
    h, w = 1920, 1080
    in_front = np.sum(depths > 0)
    in_bounds = np.sum((points_2d[:, 0] >= 0) & (points_2d[:, 0] < w) &
                       (points_2d[:, 1] >= 0) & (points_2d[:, 1] < h) &
                       (depths > 0))

    min_depth = np.min(depths[depths > 0]) if np.any(depths > 0) else 0
    max_depth = np.max(depths[depths > 0]) if np.any(depths > 0) else 0

    print(f"\nFrame {test_idx} ({row['NAME']}):")
    print(f"  Camera pos: ({tx:.2f}, {ty:.2f}, {tz:.2f})")
    print(f"  In front of camera: {in_front}/{len(voxels)}")
    print(f"  In image bounds: {in_bounds}/{len(voxels)}")
    print(f"  Depth range: {min_depth:.2f} - {max_depth:.2f}")

    if in_bounds < len(voxels) * 0.3:  # Less than 30% visible
        print(f"  ⚠️  WARNING: Less than 30% of cube is visible!")
        print(f"  Camera might be too far or looking away from cube")
