[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/lyfclldM)
# Homework2

Checkout my report: [link](report.md)

# Quick Start

## Downlaod the dataset
Dataset: [Download](https://drive.google.com/u/0/uc?export=download&confirm=qrVw&id=1GrCpYJFc8IZM_Uiisq6e8UxwVMFvr4AJ)

```
cd homework2-tedlin0913
pip install gdown
gdown 1GrCpYJFc8IZM_Uiisq6e8UxwVMFvr4AJ
```

## Setup the environment

python version: 3.12
```
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## Q2-1: Camera Pose Estimation

Run the camera relocalization and pose estimation:

```bash
python3 2d3dmatching.py
```

**What it does:**
1. Loads validation images and performs 2D-3D descriptor matching
2. Solves PnP using RANSAC for each validation image
3. Calculates median rotation and translation errors
4. Visualizes camera poses (red pyramids), trajectory (green line), and 3D point cloud

**Output:**
```
Processing 130 validation images...
100%|████████████████████| 130/130 [03:54<00:00,  1.80s/it]

==================================================
Results for 130 images:
Median Rotation Error: X.XXXX degrees
Median Translation Error: X.XXXX
==================================================
```

The script will automatically open an Open3D window showing the visualization. You can rotate, zoom, and pan to explore the scene.

---

## Q2-2: Augmented Reality
### Step 1: Position the Virtual Cube

Open the interactive 3D viewer:

```bash
python3 transform_cube.py
```
You'll see:
- The 3D point cloud of NTU Front Gate
- A cube (initially at origin, gold color)
- Coordinate axes (Red=X, Green=Y, Blue=Z)

**How to position the cube:**

1. **Translate** - Move the cube in 3D space:
   - `A` / `Shift+A` → X-axis (red)
   - `S` / `Shift+S` → Y-axis (green)
   - `D` / `Shift+D` → Z-axis (blue)

2. **Rotate** - Rotate the cube:
   - `Z` / `Shift+Z` → around X-axis
   - `X` / `Shift+X` → around Y-axis
   - `C` / `Shift+C` → around Z-axis

3. **Scale** - Make it bigger/smaller:
   - `V` / `Shift+V` → increase/decrease size

**When done:**
- Simply close the window (click X)
- The transformation is automatically saved to:
  - `cube_transform_mat.npy`
  - `cube_vertices.npy`

### Step 2: Generate the Full AR Video

Run the video generator:

```bash
python3 ar_cube_video.py
```

```bash
python3 ar_cube_video.py --density 20 --point-size 4
```

- More voxels = smoother cube surface
- Larger points = cube is more visible

**Progress:**
```
Loading data...
Creating cube voxels (density=15)...
Generated 1350 voxels
Generating AR video: ar_cube_output.mp4
100%|████████████████████| 130/130 [00:15<00:00,  8.32it/s]

============================================================
AR video successfully generated!
Output: ar_cube_output.mp4
Resolution: 1920x1080
FPS: 30
Total frames: 130
Voxels per frame: 1350
============================================================
```

Play the video when done
```
vlc ar_cube_output.mp4
```
