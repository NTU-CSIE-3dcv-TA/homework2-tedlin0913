# Complete Usage Guide for Q2-2: AR Cube Video

## What This Does

Creates an Augmented Reality video where a colorful virtual cube is rendered on top of validation images from the NTU Front Gate dataset. The cube appears to be part of the 3D scene.

## Files Overview

| File | Purpose |
|------|---------|
| `transform_cube.py` | Interactive tool to position the virtual cube (ALREADY PROVIDED) |
| `ar_cube_video.py` | Main script that generates the AR video (NEW) |
| `test_ar_cube.py` | Test script to verify everything works (NEW) |
| `Q2-2_README.md` | Detailed documentation (NEW) |

## Step-by-Step Guide

### Prerequisites

Make sure you have the data ready:
```bash
ls data/
# Should show: images.pkl, points3D.pkl, train.pkl, point_desc.pkl, frames/
```

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

**Tips for positioning:**
- Use mouse to rotate the view and see the cube from different angles
- Position the cube where it will be visible in most validation images
- Try placing it near the gate or in front of it
- A scale of 0.3-0.5 usually works well

**When done:**
- Simply close the window (click X)
- The transformation is automatically saved to:
  - `cube_transform_mat.npy`
  - `cube_vertices.npy`

### Step 2: Test (Optional but Recommended)

Before generating the full video, test on a single frame:

```bash
python3 test_ar_cube.py
```

This will:
- ✓ Check all data files exist
- ✓ Verify cube transformation files
- ✓ Render one test frame
- ✓ Save as `test_ar_frame.jpg`

**Check the test image:**
```bash
# View the test frame to see if cube looks good
xdg-open test_ar_frame.jpg  # Linux
# or
open test_ar_frame.jpg      # macOS
```

If the cube looks wrong:
- Go back to Step 1 and reposition it
- The test is fast, so iterate until it looks right

### Step 3: Generate the Full AR Video

Run the video generator:

```bash
python3 ar_cube_video.py
```

**What happens:**
1. Loads cube transformation
2. Creates 1,350 colored voxels on cube surface (15×15×6 faces)
3. Processes all 130 validation images
4. For each frame:
   - Projects voxels to 2D
   - Sorts by depth (painter's algorithm)
   - Draws from back to front
5. Saves video as `ar_cube_output.mp4`

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

### Step 4: View the Result

```bash
# Play the video
vlc ar_cube_output.mp4
# or
mpv ar_cube_output.mp4
```

## Customization Options

### Higher Quality (More Voxels)

```bash
python3 ar_cube_video.py --density 20 --point-size 4
```

- More voxels = smoother cube surface
- Larger points = cube is more visible
- Takes longer to generate

### Fast Preview (Fewer Voxels)

```bash
python3 ar_cube_video.py --density 10 --point-size 2
```

- Fewer voxels = faster generation
- Good for testing positions
- Lower visual quality

### Different Output Name

```bash
python3 ar_cube_video.py --output my_ar_cube.mp4
```

### All Options Together

```bash
python3 ar_cube_video.py \
    --output high_quality_cube.mp4 \
    --density 20 \
    --point-size 5 \
    --fps 30
```

## Understanding the Output

### Cube Colors

Each face of the cube has a different color:
- **Front face**: Red
- **Back face**: Green
- **Bottom face**: Blue
- **Top face**: Yellow
- **Left face**: Magenta
- **Right face**: Cyan

This makes it easy to see the cube's 3D orientation!

### Painter's Algorithm Visualization

The algorithm ensures correct occlusion:
1. Voxels further from camera are drawn first
2. Closer voxels are drawn on top
3. This creates proper depth ordering without complex rendering

You can see this in action:
- As the camera moves, different faces become visible
- Closer faces properly occlude farther faces
- No "see-through" artifacts

## Troubleshooting

### Problem: "cube_transform_mat.npy not found"

**Solution:**
```bash
# Run the positioning tool first
python3 transform_cube.py
# Position the cube, then close the window
```

### Problem: Cube not visible in video

**Possible causes:**
1. Cube positioned outside camera view
2. Cube too small or too far

**Solution:**
```bash
# Reposition the cube
python3 transform_cube.py
# Try positioning it near the center of the point cloud
# Make it bigger with 'V' key
```

### Problem: Video is all black or corrupted

**Check:**
```bash
# Verify validation images exist
ls data/frames/valid_*.jpg | head

# Run test first
python3 test_ar_cube.py
```

### Problem: Cube looks blocky

**Solution:**
```bash
# Increase voxel density
python3 ar_cube_video.py --density 25 --point-size 4
```

### Problem: Generation is too slow

**Solution:**
```bash
# Reduce voxel density
python3 ar_cube_video.py --density 10
```

## For the Report

### What to Include

1. **Screenshots from transform_cube.py:**
   - Show the cube positioned in the 3D point cloud
   - From multiple angles

2. **Test frame:**
   - The `test_ar_frame.jpg` showing cube rendered correctly

3. **Video frames:**
   - Screenshots from the output video
   - Show different camera angles
   - Demonstrate the cube is properly rendered

4. **YouTube link:**
   - Upload `ar_cube_output.mp4` to YouTube
   - Include the link in your report

### What to Explain

1. **Painter's Algorithm:**
   ```
   For each frame:
     1. Project all voxels to 2D
     2. Calculate depth for each voxel
     3. Sort voxels by depth (descending)
     4. Draw from furthest to closest
   ```

2. **Cube Representation:**
   - Dense point cloud on surface
   - 6 faces with different colors
   - Configurable density (voxels per edge)

3. **Transformation Pipeline:**
   - Cube vertices → Transform matrix → World coords
   - World coords → Camera extrinsic → Camera coords
   - Camera coords → Intrinsic + distortion → Image coords

## Performance Notes

**Typical timing (130 frames):**
- Density 10: ~10 seconds
- Density 15: ~15 seconds (default)
- Density 20: ~25 seconds
- Density 25: ~40 seconds

**Memory usage:**
- Low (< 500 MB)
- All processing is per-frame

## Quick Reference

```bash
# Complete workflow
python3 transform_cube.py          # Position cube
python3 test_ar_cube.py            # Test (optional)
python3 ar_cube_video.py           # Generate video

# View results
xdg-open test_ar_frame.jpg         # Test frame
vlc ar_cube_output.mp4             # Full video

# Customization
python3 ar_cube_video.py --density 20 --point-size 4  # Higher quality
python3 ar_cube_video.py --density 10 --point-size 2  # Faster preview
```

## Questions?

If something doesn't work:
1. Run `test_ar_cube.py` to diagnose
2. Check that all data files are in `data/`
3. Verify cube transformation was saved
4. Try repositioning the cube

Good luck! 🎬
