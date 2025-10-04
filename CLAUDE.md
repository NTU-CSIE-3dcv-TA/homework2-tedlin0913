# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a 3D Computer Vision homework assignment focused on camera pose estimation and 3D-2D point matching. The project contains two main Python scripts that work with point cloud data and camera parameters.

## Dataset

Download required dataset from: https://drive.google.com/u/0/uc?export=download&confirm=qrVw&id=1GrCpYJFc8IZM_Uiisq6e8UxwVMFvr4AJ

The dataset should be extracted to a `data/` directory containing:
- `points3D.pkl` - 3D point cloud data
- `images.pkl` - Image metadata with camera poses
- `train.pkl` - Training data with descriptors
- `point_desc.pkl` - Point descriptors for queries
- `frames/` - Directory containing image frames

## Main Scripts

### 1. transform_cube.py
Interactive 3D visualization tool for transforming a cube in point cloud space.

**Run:**
```bash
python3 transform_cube.py
```

**Keyboard Controls:**
- `A` / `Shift+A` - Translate along X-axis
- `S` / `Shift+S` - Translate along Y-axis
- `D` / `Shift+D` - Translate along Z-axis
- `Z` / `Shift+Z` - Rotate along X-axis
- `X` / `Shift+X` - Rotate along Y-axis
- `C` / `Shift+C` - Rotate along Z-axis
- `V` / `Shift+V` - Scale

**Outputs:**
- `cube_transform_mat.npy` - Final transformation matrix (3x4)
- `cube_vertices.npy` - Transformed cube vertices

### 2. 2d3dmathcing.py
Camera pose estimation using PnP solver with 2D-3D point correspondences.

**Run:**
```bash
python3 2d3dmathcing.py
```

**Key Functions to Implement:**
- `pnpsolver()` (line 24) - Solve PnP using descriptor matching and ratio test
- `rotation_error()` (line 34) - Calculate rotation error metric
- `translation_error()` (line 38) - Calculate translation error metric
- `visualization()` (line 42) - Visualize camera poses in 3D

**Camera Parameters:**
- Camera matrix: `[[1868.27,0,540],[0,1869.18,960],[0,0,1]]`
- Distortion coefficients: `[0.0847023,-0.192929,-0.000201144,-0.000725352]`

## Architecture Notes

**Coordinate Systems:**
- transform_cube.py uses Euler angles (XYZ convention, degrees) for rotations
- 2d3dmathcing.py uses quaternions (QX, QY, QZ, QW) for ground truth poses
- Both scripts use 3x4 transformation matrices: `[R|t]` where R is rotation (3x3) and t is translation (3x1)

**Random Seeds:**
Fixed seeds are set in 2d3dmathcing.py (seed=1428) - do not modify these for reproducibility.

## Dependencies

- open3d - 3D visualization and geometry
- opencv-python (cv2) - Computer vision operations
- numpy - Numerical operations
- scipy - Spatial transformations (Rotation)
- pandas - Data manipulation
- tqdm - Progress bars
