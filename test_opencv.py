import cv2
import numpy as np
import os

# Test if OpenCV can write files AT ALL
print("🧪 Testing basic OpenCV file writing capability...")

# Create a simple test image
test_image = np.zeros((100, 100, 3), dtype=np.uint8)
test_image[25:75, 25:75] = [255, 0, 0]  # Red square

# Test writing to current directory
cwd = os.getcwd()
test_file_local = os.path.join(cwd, "opencv_test.png")

print(f"📁 Current working directory: {cwd}")
print(f"🧪 Testing write to: {test_file_local}")

# Try to write test file
write_result = cv2.imwrite(test_file_local, test_image)
print(f"   cv2.imwrite() returned: {write_result}")

# Check if file actually exists
if os.path.exists(test_file_local):
    size = os.path.getsize(test_file_local)
    print(f"   ✅ File EXISTS: {size} bytes")

    # Clean up test file
    os.remove(test_file_local)
    print("   🗑️ Test file removed")
else:
    print("   ❌ File does NOT exist despite success return")

# Test writing to Google Drive location
test_file_gdrive = r"G:\My Drive\Code\Python\cubist_art\input\opencv_test.png"
print(f"\n🧪 Testing write to Google Drive: {test_file_gdrive}")

write_result_gd = cv2.imwrite(test_file_gdrive, test_image)
print(f"   cv2.imwrite() returned: {write_result_gd}")

if os.path.exists(test_file_gdrive):
    size = os.path.getsize(test_file_gdrive)
    print(f"   ✅ Google Drive file EXISTS: {size} bytes")

    # Clean up
    os.remove(test_file_gdrive)
    print("   🗑️ Test file removed")
else:
    print("   ❌ Google Drive file does NOT exist")

print(f"\n🔍 OpenCV version: {cv2.__version__}")


def create_edge_density_map():
    """Create edge density map for your input image."""

    input_path = r"G:\My Drive\Code\Python\cubist_art\input\your_input_image.jpg"
    output_density = (
        r"G:\My Drive\Code\Python\cubist_art\input\edge_density_your_input_image.png"
    )
    output_preview = r"G:\My Drive\Code\Python\cubist_art\input\edge_density_your_input_image_preview.png"

    print("\n🎨 Creating edge density map...")
    print(f"   Input: {input_path}")
    print(f"   Output: {output_density}")

    # Load input image
    image = cv2.imread(input_path)
    if image is None:
        print(f"❌ Could not load input image: {input_path}")
        return False

    height, width = image.shape[:2]
    print(f"   Image size: {width}x{height}")

    # Create edge-based density map
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Thicken edges and blur for density distribution
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    edges_thick = cv2.dilate(edges, kernel, iterations=1)
    density_raw = edges_thick.astype(np.float32) / 255.0
    density_smooth = cv2.GaussianBlur(density_raw, (15, 15), 0)

    # Normalize and add minimum density
    if density_smooth.max() > density_smooth.min():
        density_norm = (density_smooth - density_smooth.min()) / (
            density_smooth.max() - density_smooth.min()
        )
    else:
        density_norm = density_smooth

    density_final = density_norm * 0.9 + 0.1  # 10% minimum density everywhere
    density_image = (density_final * 255).astype(np.uint8)

    # Save density map
    success = cv2.imwrite(output_density, density_image)
    if not success:
        print("❌ Failed to save density map")
        return False

    # Verify file exists
    if os.path.exists(output_density):
        size = os.path.getsize(output_density)
        print(f"   ✅ Density map saved: {size:,} bytes")
    else:
        print("   ❌ Density map file not found after save")
        return False

    # Create preview
    density_colored = cv2.applyColorMap(density_image, cv2.COLORMAP_JET)
    preview = cv2.addWeighted(image, 0.6, density_colored, 0.4, 0)

    # Add legend
    legend_height = 60
    legend = np.zeros((legend_height, width, 3), dtype=np.uint8)
    cv2.putText(
        legend,
        "Edge Density Map: Red/Yellow=High Density, Blue=Low Density",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        1,
    )

    preview_final = np.vstack([preview, legend])

    success_preview = cv2.imwrite(output_preview, preview_final)
    if success_preview and os.path.exists(output_preview):
        size = os.path.getsize(output_preview)
        print(f"   ✅ Preview saved: {size:,} bytes")
    else:
        print("   ⚠️ Preview creation failed")

    print("\n✅ Edge density map creation complete!")
    print(f"📁 Density map: {output_density}")
    print(f"📁 Preview: {output_preview}")
    return True


# Call the edge density function
print("\n" + "=" * 60)
create_edge_density_map()
