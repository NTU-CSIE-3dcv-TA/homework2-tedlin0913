from scipy.spatial.transform import Rotation as R
import pandas as pd
import numpy as np
import random
import cv2
import time

from tqdm import tqdm
import open3d as o3d
np.random.seed(1428) # do not change this seed
random.seed(1428) # do not change this seed

def average(x):
    return list(np.mean(x,axis=0))

def average_desc(train_df, points3D_df):
    train_df = train_df[["POINT_ID","XYZ","RGB","DESCRIPTORS"]]
    desc = train_df.groupby("POINT_ID")["DESCRIPTORS"].apply(np.vstack)
    desc = desc.apply(average)
    desc = desc.reset_index()
    desc = desc.join(points3D_df.set_index("POINT_ID"), on="POINT_ID")
    return desc

def pnpsolver(query,model,cameraMatrix=0,distortion=0):
    """
    Solve PnP problem to estimate camera pose from 2D-3D correspondences.

    Args:
        query: tuple of (kp_query, desc_query) - 2D keypoints and descriptors
        model: tuple of (kp_model, desc_model) - 3D points and descriptors
        cameraMatrix: camera intrinsic matrix (not used, using hardcoded values)
        distortion: distortion coefficients (not used, using hardcoded values)

    Returns:
        retval: success flag
        rvec: rotation vector (world-to-camera)
        tvec: translation vector (world-to-camera)
        inliers: indices of inlier matches
    """
    kp_query, desc_query = query
    kp_model, desc_model = model
    cameraMatrix = np.array([[1868.27,0,540],[0,1869.18,960],[0,0,1]])
    distCoeffs = np.array([0.0847023,-0.192929,-0.000201144,-0.000725352])

    # Step 1: Descriptor matching using BFMatcher with L2 norm
    bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    matches = bf.knnMatch(desc_query, desc_model, k=2)

    # Step 2: Apply Lowe's ratio test
    good_matches = []
    for match in matches:
        if len(match) == 2:
            m, n = match
            if m.distance < 0.75 * n.distance:  # ratio threshold
                good_matches.append(m)

    # Step 3: Extract matched 2D and 3D points
    if len(good_matches) < 4:
        return False, None, None, None

    pts_2d = np.array([kp_query[m.queryIdx] for m in good_matches], dtype=np.float32)
    pts_3d = np.array([kp_model[m.trainIdx] for m in good_matches], dtype=np.float32)

    # Step 4: Solve PnP using RANSAC
    retval, rvec, tvec, inliers = cv2.solvePnPRansac(
        pts_3d, pts_2d, cameraMatrix, distCoeffs,
        iterationsCount=100,
        reprojectionError=8.0,
        confidence=0.99,
        flags=cv2.SOLVEPNP_EPNP
    )

    return retval, rvec, tvec, inliers

def rotation_error(R1, R2):
    """
    Calculate rotation error between ground truth and estimated rotation.

    Args:
        R1: Ground truth rotation as quaternion [QX, QY, QZ, QW] (1x4 array)
        R2: Estimated rotation as rotation vector (3x1 or 3, array)

    Returns:
        Rotation angle error in degrees
    """
    # Convert quaternion to rotation matrix
    # Note: scipy expects [x, y, z, w] order
    qx, qy, qz, qw = R1[0]
    R1_mat = R.from_quat([qx, qy, qz, qw]).as_matrix()

    # Convert rotation vector to rotation matrix
    R2_mat = R.from_rotvec(R2.reshape(3)).as_matrix()

    # Calculate relative rotation: R_rel = R_est @ R_gt^T
    # This gives us the rotation needed to go from ground truth to estimated
    R_rel = R2_mat @ R1_mat.T

    # Calculate rotation angle from axis-angle representation
    # Using trace formula: trace(R) = 1 + 2*cos(theta)
    trace = np.trace(R_rel)
    angle = np.arccos(np.clip((trace - 1) / 2, -1.0, 1.0))

    # Convert to degrees
    return np.degrees(angle)

def translation_error(t1, t2):
    """
    Calculate translation error as Euclidean distance.

    Args:
        t1: Ground truth translation vector (1x3 or 3x1 array)
        t2: Estimated translation vector (3x1 or 3, array)

    Returns:
        Euclidean distance between translations
    """
    return np.linalg.norm(t1.reshape(3) - t2.reshape(3))

def create_camera_pyramid(c2w, color=[1, 0, 0], scale=0.3):
    """
    Create a camera frustum as a quadrangular pyramid.

    Args:
        c2w: Camera-to-world transformation matrix (4x4)
        color: RGB color for the pyramid edges
        scale: Size of the pyramid

    Returns:
        LineSet representing the camera pyramid
    """


    # Define pyramid vertices in camera coordinates
    # Apex at origin (optical center)
    apex = [0, 0, 0]
    # Base corners (forming a square facing the scene, at negative Z)
    base_size = scale
    base_depth = -scale * 1.5
    base = [
        [-base_size, -base_size, base_depth],  # bottom-left
        [base_size, -base_size, base_depth],   # bottom-right
        [base_size, base_size, base_depth],    # top-right
        [-base_size, base_size, base_depth]    # top-left
    ]

    # All vertices
    vertices = [apex] + base

    # Transform vertices to world coordinates
    vertices_homogeneous = np.hstack([vertices, np.ones((5, 1))])
    vertices_world = (c2w @ vertices_homogeneous.T).T[:, :3]

    # Define edges: from apex to each base corner, and base edges
    edges = [
        [0, 1], [0, 2], [0, 3], [0, 4],  # apex to base corners
        [1, 2], [2, 3], [3, 4], [4, 1]   # base edges
    ]

    # Create LineSet
    line_set = o3d.geometry.LineSet()
    line_set.points = o3d.utility.Vector3dVector(vertices_world)
    line_set.lines = o3d.utility.Vector2iVector(edges)
    line_set.colors = o3d.utility.Vector3dVector([color for _ in edges])

    return line_set

def visualization(Camera2World_Transform_Matrixs, points3D_df):
    """
    Visualize camera poses as pyramids along with trajectory and 3D point cloud.

    Args:
        Camera2World_Transform_Matrixs: List of camera-to-world transformation matrices
        points3D_df: DataFrame containing 3D points with XYZ and RGB columns
    """

    # Create point cloud from 3D points
    pcd = o3d.geometry.PointCloud()
    points_xyz = np.array(points3D_df["XYZ"].to_list())
    pcd.points = o3d.utility.Vector3dVector(points_xyz)

    # Add RGB colors if available
    if "RGB" in points3D_df.columns:
        points_rgb = np.array(points3D_df["RGB"].to_list()) / 255.0
        pcd.colors = o3d.utility.Vector3dVector(points_rgb)

    # Create geometries list
    geometries = [pcd]

    # Extract camera positions for trajectory
    camera_positions = []
    for c2w in Camera2World_Transform_Matrixs:
        camera_positions.append(c2w[:3, 3])

    # Create camera pyramids
    for i, c2w in enumerate(Camera2World_Transform_Matrixs):
        # Create camera pyramid (red color)
        pyramid = create_camera_pyramid(c2w, color=[1, 0, 0], scale=0.2)
        geometries.append(pyramid)

    # Create trajectory line
    if len(camera_positions) > 1:
        trajectory_points = np.array(camera_positions)
        trajectory_lines = [[i, i+1] for i in range(len(camera_positions)-1)]

        trajectory = o3d.geometry.LineSet()
        trajectory.points = o3d.utility.Vector3dVector(trajectory_points)
        trajectory.lines = o3d.utility.Vector2iVector(trajectory_lines)
        trajectory.colors = o3d.utility.Vector3dVector([[0, 1, 0] for _ in trajectory_lines])  # green
        geometries.append(trajectory)

    # Visualize
    o3d.visualization.draw_geometries(geometries,
                                      window_name="Camera Poses, Trajectory, and 3D Points",
                                      width=1280, height=720,
                                      point_show_normal=False)

if __name__ == "__main__":
    # Load data
    images_df = pd.read_pickle("data/images.pkl")
    train_df = pd.read_pickle("data/train.pkl")
    points3D_df = pd.read_pickle("data/points3D.pkl")
    point_desc_df = pd.read_pickle("data/point_desc.pkl")

    # Process model descriptors
    desc_df = average_desc(train_df, points3D_df)
    kp_model = np.array(desc_df["XYZ"].to_list())
    desc_model = np.array(desc_df["DESCRIPTORS"].to_list()).astype(np.float32)

    # Get all validation images (images with names starting with 'valid_')
    validation_images = images_df[images_df["NAME"].str.startswith("valid_")]
    IMAGE_ID_LIST = validation_images["IMAGE_ID"].tolist()
    print(f"Processing {len(IMAGE_ID_LIST)} validation images...")
    r_list = []
    t_list = []
    rotation_error_list = []
    translation_error_list = []
    for idx in tqdm(IMAGE_ID_LIST):
        # Load quaery image
        fname = (images_df.loc[images_df["IMAGE_ID"] == idx])["NAME"].values[0]
        rimg = cv2.imread("data/frames/" + fname, cv2.IMREAD_GRAYSCALE)

        # Load query keypoints and descriptors
        points = point_desc_df.loc[point_desc_df["IMAGE_ID"] == idx]
        kp_query = np.array(points["XY"].to_list())
        desc_query = np.array(points["DESCRIPTORS"].to_list()).astype(np.float32)

        # Find correspondance and solve pnp
        retval, rvec, tvec, inliers = pnpsolver((kp_query, desc_query), (kp_model, desc_model))

        if not retval:
            print(f"Warning: PnP failed for image {idx}")
            continue

        r_list.append(rvec)
        t_list.append(tvec)

        # Get camera pose groudtruth
        ground_truth = images_df.loc[images_df["IMAGE_ID"]==idx]
        rotq_gt = ground_truth[["QX","QY","QZ","QW"]].values
        tvec_gt = ground_truth[["TX","TY","TZ"]].values

        # Calculate error (fixed bug: was comparing ground truth with itself)
        r_error = rotation_error(rotq_gt, rvec)
        t_error = translation_error(tvec_gt, tvec)
        rotation_error_list.append(r_error)
        translation_error_list.append(t_error)

    # Calculate median of relative rotation angle differences and translation differences
    median_rotation_error = np.median(rotation_error_list)
    median_translation_error = np.median(translation_error_list)
    print(f"\n{'='*50}")
    print(f"Results for {len(rotation_error_list)} images:")
    print(f"Median Rotation Error: {median_rotation_error:.4f} degrees")
    print(f"Median Translation Error: {median_translation_error:.4f}")
    print(f"{'='*50}\n")

    # Result visualization: Convert world-to-camera to camera-to-world
    Camera2World_Transform_Matrixs = []
    for r, t in zip(r_list, t_list):
        # PnP returns world-to-camera transformation: p_camera = R * p_world + t
        # We need camera-to-world: [R^T | -R^T * t]
        R_mat = R.from_rotvec(r.reshape(3)).as_matrix()

        # Create camera-to-world transformation matrix
        c2w = np.eye(4)
        c2w[:3, :3] = R_mat.T  # R^T
        c2w[:3, 3] = -R_mat.T @ t.reshape(3)  # -R^T * t

        # Fix coordinate system: flip Y and Z axes
        flip = np.diag([1, -1, -1, 1])
        c2w = c2w @ flip

        Camera2World_Transform_Matrixs.append(c2w)

    visualization(Camera2World_Transform_Matrixs, points3D_df)