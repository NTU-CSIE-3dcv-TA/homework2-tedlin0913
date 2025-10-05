"""
AR Cube Video Generator for Q2-2
Creates an Augmented Reality video by rendering a virtual cube on validation images.
Uses the painter's algorithm to determine drawing order.

Usage:
    1. First run transform_cube.py to manually position the cube
    2. Then run this script to generate the AR video

Author: 3DCV HW2
"""

import cv2
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
from tqdm import tqdm
import os
import re


def load_cube_transform():
    """Load the cube transformation matrix and vertices from saved files."""
    if not os.path.exists('cube_transform_mat.npy'):
        raise FileNotFoundError(
            "cube_transform_mat.npy not found. Please run transform_cube.py first "
            "to manually position the cube and save the transformation."
        )

    transform_mat = np.load('cube_transform_mat.npy')
    cube_vertices = np.load('cube_vertices.npy')

    return transform_mat, cube_vertices


def create_cube_voxels(cube_vertices, density=10):
    """
    Create a dense point cloud (voxels) on the cube surface.

    Args:
        cube_vertices: 8 vertices of the cube (8x3 array)
        density: number of points per edge

    Returns:
        voxels: Nx3 array of 3D points on cube surface
        colors: Nx3 array of RGB colors for each voxel
    """
    # Cube vertices are indexed as:
    # 0-3: front face (lower Z), 4-7: back face (higher Z)
    # Each face: 0,1,2,3 in counter-clockwise order when viewed from outside

    # Define the 6 faces of the cube using vertex indices
    # Each face is ordered as: bottom-left, bottom-right, top-right, top-left (CCW from outside)
    faces = [
        [0, 1, 2, 3],  # front face (Z = min)
        [5, 4, 7, 6],  # back face (Z = max)
        [4, 5, 1, 0],  # bottom face (Y = min)
        [3, 2, 6, 7],  # top face (Y = max)
        [4, 0, 3, 7],  # left face (X = min)
        [1, 5, 6, 2]   # right face (X = max)
    ]

    # Different colors for each face
    face_colors = [
        [1.0, 0.0, 0.0],  # red - front
        [0.0, 1.0, 0.0],  # green - back
        [0.0, 0.0, 1.0],  # blue - bottom
        [1.0, 1.0, 0.0],  # yellow - top
        [1.0, 0.0, 1.0],  # magenta - left
        [0.0, 1.0, 1.0]   # cyan - right
    ]

    voxels = []
    colors = []

    # Generate points on each face
    for face_idx, face in enumerate(faces):
        # Get the 4 vertices of this face
        v0, v1, v2, v3 = [cube_vertices[i] for i in face]

        # Create a grid of points on this face
        for i in range(density):
            for j in range(density):
                u = i / (density - 1) if density > 1 else 0.5
                v = j / (density - 1) if density > 1 else 0.5

                # Bilinear interpolation on the face
                # v0 -- v1
                # |      |
                # v3 -- v2
                point = (1-u)*(1-v)*v0 + u*(1-v)*v1 + u*v*v2 + (1-u)*v*v3
                voxels.append(point)
                colors.append(face_colors[face_idx])

    return np.array(voxels), np.array(colors)


def apply_transformation(points, transform_mat):
    """
    Apply 3x4 transformation matrix to 3D points.

    Args:
        points: Nx3 array of 3D points
        transform_mat: 3x4 transformation matrix [R|t]

    Returns:
        Nx3 array of transformed points
    """
    # Convert to homogeneous coordinates
    points_homogeneous = np.hstack([points, np.ones((points.shape[0], 1))])

    # Apply transformation
    transformed = (transform_mat @ points_homogeneous.T).T

    return transformed


def project_points(points_3d, R_mat, t_vec, camera_matrix, dist_coeffs):
    """
    Project 3D points to 2D image coordinates.

    Args:
        points_3d: Nx3 array of 3D points in world coordinates
        R_mat: 3x3 rotation matrix (world-to-camera)
        t_vec: 3x1 translation vector (world-to-camera)
        camera_matrix: 3x3 camera intrinsic matrix
        dist_coeffs: distortion coefficients

    Returns:
        points_2d: Nx2 array of 2D image coordinates
        depths: N array of depths (Z coordinates in camera frame)
    """
    # Convert rotation matrix to rotation vector
    rvec, _ = cv2.Rodrigues(R_mat)

    # Project points using OpenCV
    points_2d, _ = cv2.projectPoints(
        points_3d, rvec, t_vec, camera_matrix, dist_coeffs
    )

    # Calculate depths (Z coordinate in camera frame)
    points_camera = (R_mat @ points_3d.T).T + t_vec.reshape(1, 3)
    depths = points_camera[:, 2]

    # Reshape points_2d from (N, 1, 2) to (N, 2)
    points_2d = points_2d.reshape(-1, 2)

    return points_2d, depths


def draw_cube_with_painters_algorithm(image, points_2d, depths, colors, voxels_camera, point_size=3):
    """
    Draw cube voxels on image using painter's algorithm.

    Painter's Algorithm:
    1. Filter voxels by viewing angle (remove those at extreme angles)
    2. Sort remaining voxels by depth
    3. Draw voxels from furthest to closest

    Args:
        image: input image to draw on
        points_2d: Nx2 array of 2D image coordinates
        depths: N array of depths
        colors: Nx3 array of RGB colors [0-1 range]
        voxels_camera: Nx3 array of voxel positions in camera coordinates
        point_size: size of each voxel point

    Returns:
        image with drawn cube
    """
    # Create a copy of the image
    output = image.copy()

    h, w = image.shape[:2]

    # Filter voxels by viewing angle
    # In camera coordinates: +Z is forward, X is right, Y is down
    # A voxel at (X, Y, Z) has viewing angle = atan2(sqrt(X² + Y²), Z)
    # Only draw voxels within reasonable field of view (< 80 degrees from center)

    valid_mask = np.ones(len(depths), dtype=bool)

    for idx in range(len(voxels_camera)):
        x_cam, y_cam, z_cam = voxels_camera[idx]

        # Skip if behind camera
        if z_cam <= 0:
            valid_mask[idx] = False
            continue

        # Calculate viewing angle from camera center
        # Distance from camera's Z-axis (optical axis)
        lateral_dist = np.sqrt(x_cam**2 + y_cam**2)

        # Angle from optical axis
        angle = np.arctan2(lateral_dist, z_cam)
        angle_degrees = np.degrees(angle)

        # Skip voxels at extreme angles (> 50 degrees)
        # These are either behind camera or at extreme periphery
        if angle_degrees > 50:
            valid_mask[idx] = False
            continue

        # Also check if within image bounds
        x_2d, y_2d = points_2d[idx]
        if x_2d < 0 or x_2d >= w or y_2d < 0 or y_2d >= h:
            valid_mask[idx] = False
            continue

    # Get valid indices
    valid_indices = np.where(valid_mask)[0]

    if len(valid_indices) == 0:
        return output

    # Sort valid voxels by depth (furthest first)
    valid_depths = depths[valid_indices]
    sorted_order = np.argsort(-valid_depths)
    sorted_valid_indices = valid_indices[sorted_order]

    # Draw each voxel from furthest to closest
    for idx in sorted_valid_indices:
        x, y = points_2d[idx]

        # Convert color from [0-1] to [0-255] BGR format
        color_bgr = (
            int(colors[idx][2] * 255),  # B
            int(colors[idx][1] * 255),  # G
            int(colors[idx][0] * 255)   # R
        )

        # Draw the voxel as a filled circle
        cv2.circle(output, (int(x), int(y)), point_size, color_bgr, -1)

    return output


def quaternion_to_rotation_matrix(qx, qy, qz, qw):
    """
    Convert quaternion to rotation matrix.

    Args:
        qx, qy, qz, qw: quaternion components

    Returns:
        3x3 rotation matrix
    """
    rot = R.from_quat([qx, qy, qz, qw])
    return rot.as_matrix()


def generate_ar_video(output_path='ar_cube_output.mp4', fps=30, voxel_density=15, point_size=3):
    """
    Generate AR video with virtual cube on validation images.

    Args:
        output_path: path to save output video
        fps: frames per second
        voxel_density: number of voxels per cube edge
        point_size: size of each voxel point in pixels
    """
    print("Loading data...")

    # Load cube transformation
    transform_mat, cube_vertices = load_cube_transform()
    print(f"Cube transformation matrix:\n{transform_mat}")

    # Load camera parameters
    camera_matrix = np.array([
        [1868.27, 0, 540],
        [0, 1869.18, 960],
        [0, 0, 1]
    ])
    dist_coeffs = np.array([0.0847023, -0.192929, -0.000201144, -0.000725352])

    # Load image data
    images_df = pd.read_pickle("data/images.pkl")

    # Get validation images sorted by numeric ID
    validation_images = images_df[images_df["NAME"].str.startswith("valid_")].copy()

    # Extract numeric IDs and sort
    def extract_id(name):
        match = re.search(r'(\d+)', name)
        return int(match.group(1)) if match else 0

    validation_images['numeric_id'] = validation_images['NAME'].apply(extract_id)
    validation_images = validation_images.sort_values('numeric_id')

    print(f"Processing {len(validation_images)} validation images...")

    # Create cube voxels
    print(f"Creating cube voxels (density={voxel_density})...")
    voxels, voxel_colors = create_cube_voxels(cube_vertices, density=voxel_density)
    print(f"Generated {len(voxels)} voxels")

    # Apply cube transformation to voxels
    voxels_transformed = apply_transformation(voxels, transform_mat)

    # Initialize video writer
    first_image_path = "data/frames/" + validation_images.iloc[0]["NAME"]
    first_image = cv2.imread(first_image_path)
    h, w = first_image.shape[:2]

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    print(f"Generating AR video: {output_path}")

    # Process each image
    for _, row in tqdm(validation_images.iterrows(), total=len(validation_images)):
        # Load image
        image_path = "data/frames/" + row["NAME"]
        image = cv2.imread(image_path)

        if image is None:
            print(f"Warning: Could not load image {image_path}")
            continue

        # Get camera pose (world-to-camera)
        qx, qy, qz, qw = row["QX"], row["QY"], row["QZ"], row["QW"]
        tx, ty, tz = row["TX"], row["TY"], row["TZ"]

        R_mat = quaternion_to_rotation_matrix(qx, qy, qz, qw)
        t_vec = np.array([tx, ty, tz])

        # Project cube voxels to image
        points_2d, depths = project_points(
            voxels_transformed, R_mat, t_vec, camera_matrix, dist_coeffs
        )

        # Calculate voxel positions in camera coordinates (needed for angle checking)
        voxels_camera = (R_mat @ voxels_transformed.T).T + t_vec.reshape(1, 3)

        # Check visibility before drawing
        h, w = image.shape[:2]
        points_in_front = np.sum(depths > 0)
        points_in_bounds = np.sum((points_2d[:, 0] >= 0) & (points_2d[:, 0] < w) &
                                  (points_2d[:, 1] >= 0) & (points_2d[:, 1] < h) &
                                  (depths > 0))

        # Debug: print visibility for each frame
        if points_in_bounds > 0:
            print(f"Frame {row['NAME']}: {points_in_bounds}/{len(depths)} voxels visible (before angle filter), "
                  f"depth range: [{depths[depths>0].min():.2f}, {depths[depths>0].max():.2f}]")
        else:
            print(f"Frame {row['NAME']}: NO VOXELS VISIBLE (all outside frame or behind camera)")

        # Draw cube using painter's algorithm with angle filtering
        output_image = draw_cube_with_painters_algorithm(
            image, points_2d, depths, voxel_colors, voxels_camera, point_size=point_size
        )

        # Write frame to video
        video_writer.write(output_image)

    # Release video writer
    video_writer.release()

    print(f"\n{'='*60}")
    print(f"AR video successfully generated!")
    print(f"Output: {output_path}")
    print(f"Resolution: {w}x{h}")
    print(f"FPS: {fps}")
    print(f"Total frames: {len(validation_images)}")
    print(f"Voxels per frame: {len(voxels)}")
    print(f"{'='*60}\n")


def main():
    """Main function to generate AR video."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate AR video with virtual cube on validation images'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='ar_cube_output.mp4',
        help='Output video path (default: ar_cube_output.mp4)'
    )
    parser.add_argument(
        '--fps',
        type=int,
        default=30,
        help='Frames per second (default: 30)'
    )
    parser.add_argument(
        '--density', '-d',
        type=int,
        default=15,
        help='Voxel density per cube edge (default: 15)'
    )
    parser.add_argument(
        '--point-size', '-p',
        type=int,
        default=3,
        help='Voxel point size in pixels (default: 3)'
    )

    args = parser.parse_args()

    try:
        generate_ar_video(
            output_path=args.output,
            fps=args.fps,
            voxel_density=args.density,
            point_size=args.point_size
        )
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nPlease follow these steps:")
        print("1. Run: python3 transform_cube.py")
        print("2. Use keyboard to position the cube (A/S/D for translation, Z/X/C for rotation, V for scale)")
        print("3. Close the window to save the transformation")
        print("4. Run this script again to generate the AR video")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
