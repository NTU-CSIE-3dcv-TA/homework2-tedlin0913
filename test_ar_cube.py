"""
Test script for AR cube video generation.
Verifies all components work before generating the full video.
"""

import numpy as np
import cv2
import os
import pandas as pd


def test_data_files():
    """Test that all required data files exist."""
    print("Testing data files...")

    required_files = [
        "data/images.pkl",
        "data/points3D.pkl",
        "data/frames/"
    ]

    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - NOT FOUND")
            all_exist = False

    if not all_exist:
        print("\n⚠️  Some data files are missing!")
        return False

    # Check validation images
    images_df = pd.read_pickle("data/images.pkl")
    validation_images = images_df[images_df["NAME"].str.startswith("valid_")]
    print(f"  ✓ Found {len(validation_images)} validation images")

    return True


def test_cube_transform():
    """Test that cube transformation files exist."""
    print("\nTesting cube transformation files...")

    if os.path.exists('cube_transform_mat.npy') and os.path.exists('cube_vertices.npy'):
        transform_mat = np.load('cube_transform_mat.npy')
        cube_vertices = np.load('cube_vertices.npy')

        print(f"  ✓ cube_transform_mat.npy - shape {transform_mat.shape}")
        print(f"  ✓ cube_vertices.npy - shape {cube_vertices.shape}")
        print(f"\nTransformation matrix:")
        print(transform_mat)

        return True
    else:
        print("  ✗ Cube transformation files not found")
        print("\n⚠️  Please run transform_cube.py first!")
        return False


def test_video_generation():
    """Test generating a single frame."""
    print("\nTesting AR rendering on single frame...")

    try:
        from ar_cube_video import (
            create_cube_voxels,
            apply_transformation,
            project_points,
            draw_cube_with_painters_algorithm,
            quaternion_to_rotation_matrix
        )

        # Load data
        transform_mat = np.load('cube_transform_mat.npy')
        cube_vertices = np.load('cube_vertices.npy')
        images_df = pd.read_pickle("data/images.pkl")

        # Get first validation image
        validation_images = images_df[images_df["NAME"].str.startswith("valid_")]
        first_image_row = validation_images.iloc[0]

        # Load image
        image_path = "data/frames/" + first_image_row["NAME"]
        image = cv2.imread(image_path)

        if image is None:
            print(f"  ✗ Could not load image: {image_path}")
            return False

        print(f"  ✓ Loaded image: {first_image_row['NAME']} - {image.shape}")

        # Create voxels
        voxels, colors = create_cube_voxels(cube_vertices, density=10)
        print(f"  ✓ Created {len(voxels)} voxels")

        # Transform voxels
        voxels_transformed = apply_transformation(voxels, transform_mat)
        print(f"  ✓ Applied transformation")

        # Camera parameters
        camera_matrix = np.array([[1868.27, 0, 540], [0, 1869.18, 960], [0, 0, 1]])
        dist_coeffs = np.array([0.0847023, -0.192929, -0.000201144, -0.000725352])

        # Get camera pose
        qx, qy, qz, qw = first_image_row["QX"], first_image_row["QY"], first_image_row["QZ"], first_image_row["QW"]
        tx, ty, tz = first_image_row["TX"], first_image_row["TY"], first_image_row["TZ"]

        R_mat = quaternion_to_rotation_matrix(qx, qy, qz, qw)
        t_vec = np.array([tx, ty, tz])

        # Project points
        points_2d, depths = project_points(voxels_transformed, R_mat, t_vec, camera_matrix, dist_coeffs)
        print(f"  ✓ Projected voxels to 2D")

        # Count visible points
        h, w = image.shape[:2]
        visible = np.sum((points_2d[:, 0] >= 0) & (points_2d[:, 0] < w) &
                        (points_2d[:, 1] >= 0) & (points_2d[:, 1] < h) &
                        (depths > 0))
        print(f"  ✓ {visible}/{len(voxels)} voxels visible in frame")

        # Render
        output = draw_cube_with_painters_algorithm(image, points_2d, depths, colors, point_size=3)
        print(f"  ✓ Rendered cube using painter's algorithm")

        # Save test image
        cv2.imwrite('test_ar_frame.jpg', output)
        print(f"  ✓ Saved test frame: test_ar_frame.jpg")

        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("AR Cube Video - Test Suite")
    print("="*60 + "\n")

    tests = [
        ("Data files", test_data_files),
        ("Cube transformation", test_cube_transform),
        ("Video generation", test_video_generation)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Ready to generate AR video.")
        print("\nRun: python3 ar_cube_video.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")

    print("="*60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
