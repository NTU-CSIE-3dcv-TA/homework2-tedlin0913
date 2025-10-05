# Q2-2: AR Cube Video Generation

This directory contains scripts for generating an Augmented Reality video with a virtual cube overlaid on validation images.

## Overview

The solution consists of two scripts:
1. **transform_cube.py** - Interactive tool to manually position the virtual cube
2. **ar_cube_video.py** - Generates the AR video using the positioned cube

## Quick Start

### Step 1: Position the Cube Interactively

Run the interactive cube positioning tool:

```bash
python3 transform_cube.py
```

**Keyboard Controls:**
- `A` / `Shift+A` - Translate along X-axis (forward/backward)
- `S` / `Shift+S` - Translate along Y-axis (left/right)
- `D` / `Shift+D` - Translate along Z-axis (up/down)
- `Z` / `Shift+Z` - Rotate along X-axis
- `X` / `Shift+X` - Rotate along Y-axis
- `C` / `Shift+C` - Rotate along Z-axis
- `V` / `Shift+V` - Scale (increase/decrease size)

**Instructions:**
1. The window shows the 3D point cloud and a cube
2. Use the keyboard controls to position the cube where you want it
3. Close the window when done - this automatically saves:
   - `cube_transform_mat.npy` - Transformation matrix
   - `cube_vertices.npy` - Transformed cube vertices

### Step 2: Generate AR Video

Run the AR video generator:

```bash
python3 ar_cube_video.py
```

**Options:**
```bash
python3 ar_cube_video.py --help

Options:
  --output, -o OUTPUT    Output video path (default: ar_cube_output.mp4)
  --fps FPS              Frames per second (default: 30)
  --density, -d DENSITY  Voxel density per cube edge (default: 15)
  --point-size, -p SIZE  Voxel point size in pixels (default: 3)
```

**Examples:**
```bash
# Default settings
python3 ar_cube_video.py

# High quality (more voxels, larger points)
python3 ar_cube_video.py --density 20 --point-size 4 --output ar_cube_hq.mp4

# Fast preview (fewer voxels)
python3 ar_cube_video.py --density 10 --point-size 2
```

## Implementation Details

### Painter's Algorithm

The script implements a simple but efficient painter's algorithm:

1. **Generate voxels**: Create a dense point cloud on the cube's 6 faces
2. **Transform voxels**: Apply the saved transformation matrix
3. **For each frame**:
   - Project 3D voxels to 2D image coordinates
   - Calculate depth for each voxel
   - Sort voxels by depth (furthest first)
   - Draw voxels from back to front

This ensures proper visibility without complex occlusion handling.

### Cube Representation

The virtual cube is represented as:
- **Point cloud (voxels)** on 6 faces
- Each face has a distinct color:
  - Front: Red
  - Back: Green
  - Bottom: Blue
  - Top: Yellow
  - Left: Magenta
  - Right: Cyan

### Camera Projection

Uses the provided camera parameters:
- **Intrinsic matrix**: `[[1868.27, 0, 540], [0, 1869.18, 960], [0, 0, 1]]`
- **Distortion coefficients**: `[0.0847023, -0.192929, -0.000201144, -0.000725352]`

Projects 3D points using OpenCV's `projectPoints()` with proper handling of distortion.

## Output

The script generates:
- **Video file**: `ar_cube_output.mp4` (or custom name)
- **Console output**: Summary of processing details

Example output:
```
============================================================
AR video successfully generated!
Output: ar_cube_output.mp4
Resolution: 1920x1080
FPS: 30
Total frames: 130
Voxels per frame: 1350
============================================================
```

## Troubleshooting

### "cube_transform_mat.npy not found"
- Run `transform_cube.py` first to position the cube
- Make sure to close the window to save the transformation

### Cube not visible in video
- The cube might be positioned outside the camera view
- Re-run `transform_cube.py` and adjust the position
- Try starting with default position (center of point cloud)

### Video looks wrong
- Check that validation images are in `data/frames/`
- Verify camera parameters match your dataset
- Try adjusting voxel density and point size

### Performance issues
- Reduce voxel density: `--density 10`
- Reduce point size: `--point-size 2`
- The script processes ~130 frames, should take 10-30 seconds

## Technical Notes

### Coordinate Systems

- **World coordinates**: 3D points from COLMAP reconstruction
- **Camera coordinates**: After applying camera extrinsic (R, t)
- **Image coordinates**: After projection with intrinsic matrix K

### Transformation Pipeline

```
Cube vertices (local)
  → Apply transformation matrix [scale * R | t]
  → World coordinates
  → Apply camera extrinsic [R_cam | t_cam]
  → Camera coordinates
  → Apply intrinsic K and distortion
  → Image coordinates (pixels)
```

### Painter's Algorithm Efficiency

- **Sorting**: O(n log n) where n = number of voxels
- **Drawing**: O(n) with bounds checking
- **Total**: ~O(n log n) per frame, very efficient

No complex data structures needed - just sort by depth!

## Dependencies

- opencv-python (cv2)
- numpy
- pandas
- scipy
- open3d
- tqdm

Install with:
```bash
pip install opencv-python numpy pandas scipy open3d tqdm
```
