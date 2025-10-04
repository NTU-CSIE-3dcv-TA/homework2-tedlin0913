from scipy.spatial.transform import Rotation as R
import pandas as pd
import numpy as np
import random
import cv2
import time

from tqdm import tqdm

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
    kp_query, desc_query = query
    kp_model, desc_model = model
    cameraMatrix = np.array([[1868.27,0,540],[0,1869.18,960],[0,0,1]])
    distCoeffs = np.array([0.0847023,-0.192929,-0.000201144,-0.000725352])

    # Descriptor matching using BFMatcher with L2 norm
    bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    matches = bf.knnMatch(desc_query, desc_model, k=2)

    # Apply Lowe's ratio test
    good_matches = []
    for match in matches:
        if len(match) == 2:
            m, n = match
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

    # Extract matched 2D and 3D points
    if len(good_matches) < 4:
        return False, None, None, None

    pts_2d = np.array([kp_query[m.queryIdx] for m in good_matches], dtype=np.float32)
    pts_3d = np.array([kp_model[m.trainIdx] for m in good_matches], dtype=np.float32)

    # Solve PnP using RANSAC
    retval, rvec, tvec, inliers = cv2.solvePnPRansac(
        pts_3d, pts_2d, cameraMatrix, distCoeffs,
        iterationsCount=1000,
        reprojectionError=8.0,
        confidence=0.99,
        flags=cv2.SOLVEPNP_EPNP
    )

    return retval, rvec, tvec, inliers

def rotation_error(R1, R2):
    # R1 is quaternion (QX, QY, QZ, QW), R2 is rotation vector
    # Convert quaternion to rotation matrix
    qx, qy, qz, qw = R1[0]
    R1_mat = R.from_quat([qx, qy, qz, qw]).as_matrix()

    # Convert rotation vector to rotation matrix
    R2_mat = R.from_rotvec(R2.reshape(3)).as_matrix()

    # Calculate relative rotation
    R_rel = R2_mat.T @ R1_mat

    # Calculate rotation angle from trace
    trace = np.trace(R_rel)
    angle = np.arccos(np.clip((trace - 1) / 2, -1.0, 1.0))

    # Convert to degrees
    return np.degrees(angle)

def translation_error(t1, t2):
    # Calculate Euclidean distance between two translation vectors
    return np.linalg.norm(t1 - t2)

def visualization(Camera2World_Transform_Matrixs, points3D_df):
    import open3d as o3d

    # Create point cloud from 3D points
    pcd = o3d.geometry.PointCloud()
    points_xyz = np.array(points3D_df["XYZ"].to_list())
    pcd.points = o3d.utility.Vector3dVector(points_xyz)

    # Add RGB colors if available
    if "RGB" in points3D_df.columns:
        points_rgb = np.array(points3D_df["RGB"].to_list()) / 255.0
        pcd.colors = o3d.utility.Vector3dVector(points_rgb)

    # Create camera frustums
    geometries = [pcd]
    for i, c2w in enumerate(Camera2World_Transform_Matrixs):
        # Create coordinate frame for each camera
        camera_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.5)
        camera_frame.transform(c2w)
        geometries.append(camera_frame)

    # Visualize
    o3d.visualization.draw_geometries(geometries,
                                      window_name="Camera Poses and 3D Points",
                                      width=1024, height=768)

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


    IMAGE_ID_LIST = [200,201]
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
        # rotq = R.from_rotvec(rvec.reshape(1,3)).as_quat() # Convert rotation vector to quaternion
        # tvec = tvec.reshape(1,3) # Reshape translation vector
        r_list.append(rvec)
        t_list.append(tvec)

        # Get camera pose groudtruth
        ground_truth = images_df.loc[images_df["IMAGE_ID"]==idx]
        rotq_gt = ground_truth[["QX","QY","QZ","QW"]].values
        tvec_gt = ground_truth[["TX","TY","TZ"]].values

        # Calculate error
        r_error = rotation_error(rotq_gt, rvec)
        t_error = translation_error(tvec_gt, tvec)
        rotation_error_list.append(r_error)
        translation_error_list.append(t_error)

    # Calculate median of relative rotation angle differences and translation differences
    median_rotation_error = np.median(rotation_error_list)
    median_translation_error = np.median(translation_error_list)
    print(f"Median Rotation Error: {median_rotation_error:.4f} degrees")
    print(f"Median Translation Error: {median_translation_error:.4f}")

    # Result visualization
    Camera2World_Transform_Matrixs = []
    for r, t in zip(r_list, t_list):
        # Convert rotation vector to rotation matrix
        R_mat = R.from_rotvec(r.reshape(3)).as_matrix()

        # Camera-to-world transformation (inverse of world-to-camera)
        # World-to-camera: [R|t], Camera-to-world: [R^T | -R^T*t]
        c2w = np.eye(4)
        c2w[:3, :3] = R_mat.T
        c2w[:3, 3] = -R_mat.T @ t.reshape(3)
        Camera2World_Transform_Matrixs.append(c2w)
    visualization(Camera2World_Transform_Matrixs, points3D_df)