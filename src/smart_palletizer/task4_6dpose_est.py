# """
# Task 4 – Multi-Box 6D Pose Estimation (Axes-Only Visualization)
# ----------------------------------------------------------------

# A clean geometric pipeline for estimating the 6D pose of each box
# in medium_box/ and small_box/ using RGB-D + intrinsics + masks.

# For each mask, we:
# 1. Convert masked depth pixels → 3D camera-frame points.
# 2. PCA → get dominant axes and centroid.
# 3. Reorder axes to match known physical box dimensions.
# 4. Correct orientation so +Z (normal) faces the camera.
# 5. Project the box’s local coordinate frame as RGB arrows on the image.
# 6. Convert camera-frame pose → root/world frame (cam2root.json).
# 7. Save both visualization and SE(3) pose.

# """

# import numpy as np
# import cv2
# import json
# from pathlib import Path
# import matplotlib.pyplot as plt



# def load_scene(scene_dir):
#     scene_dir = Path(scene_dir)

#     with open(scene_dir / "intrinsics.json") as f:
#         intr = json.load(f)

#     color = cv2.cvtColor(
#         cv2.imread(str(scene_dir / "color_image.png")),
#         cv2.COLOR_BGR2RGB
#     )

#     depth = cv2.imread(str(scene_dir / "raw_depth.png"),
#                        cv2.IMREAD_ANYDEPTH).astype(np.float32)
#     if depth.max() > 50:  # mm → m
#         depth /= 1000.0

#     return color, depth, intr


# def load_mask(mask_path):
#     m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
#     return m > 0


# # Depth -> Camera points.

# def depth_to_camera_points(depth, mask, intr):
#     fx, fy, cx, cy = intr["fx"], intr["fy"], intr["cx"], intr["cy"]
#     ys, xs = np.where(mask)

#     Z = depth[ys, xs]
#     X = (xs - cx) * Z / fx
#     Y = (ys - cy) * Z / fy

#     pts = np.stack([X, Y, Z], axis=1)
#     return pts[(pts[:,2] > 0) & np.isfinite(pts[:,0])]



# def pca_pose(pts):
#     t = pts.mean(axis=0)
#     P = pts - t
#     H = P.T @ P
#     vals, vecs = np.linalg.eigh(H)
#     order = np.argsort(-vals)

#     R = vecs[:, order]
#     if np.linalg.det(R) < 0:
#         R[:,2] *= -1

#     return R, t


# #Since we already know box dimensions, we can align PCA axes accordingly

# def align_axes_to_dims(R, dims):
#     order = np.argsort(-dims)    #match largest PCA axis to longest side
#     dims_sorted = dims[order]
#     R2 = R[:, order]

#     if np.linalg.det(R2) < 0:
#         R2[:,2] *= -1

#     return R2, dims_sorted


# #We make sure that +Z faces the camera

# def correct_orientation(R):
#     if R[2,2] < 0:
#         R[:,2] *= -1

#     R[:,0] = np.cross(R[:,1], R[:,2]); R[:,0] /= np.linalg.norm(R[:,0])
#     R[:,1] = np.cross(R[:,2], R[:,0]); R[:,1] /= np.linalg.norm(R[:,1])
#     return R


# # Overlay the axes on the colour image

# def draw_axes_only(color, R, t, intr, axis_length=0.12):
#     img = color.copy()
#     fx, fy, cx, cy = intr["fx"], intr["fy"], intr["cx"], intr["cy"]

#     def proj(pt):
#         X, Y, Z = pt
#         return (int(fx*X/Z + cx), int(fy*Y/Z + cy))

#     origin_2d = proj(t)
#     X_2d = proj(t + R[:,0] * axis_length)
#     Y_2d = proj(t + R[:,1] * axis_length)
#     Z_2d = proj(t + R[:,2] * axis_length)

#     cv2.arrowedLine(img, origin_2d, X_2d, (255,0,0), 3)
#     cv2.arrowedLine(img, origin_2d, Y_2d, (0,255,0), 3)
#     cv2.arrowedLine(img, origin_2d, Z_2d, (0,0,255), 3)

#     return img


# # Convert camera pose → root/world frame

# def to_root_frame(scene_dir, R, t):
#     with open(Path(scene_dir) / "cam2root.json") as f:
#         raw = json.load(f)

#     cam2root = np.array(raw["cam2root"], dtype=float).reshape(4,4)

#     T = np.eye(4)
#     T[:3,:3] = R
#     T[:3, 3] = t

#     return cam2root @ T


# #Save functions
# def save_image(img, path):
#     Path(path).parent.mkdir(parents=True, exist_ok=True)
#     cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
#     print(f"[Task 4] Saved → {path}")


# def save_json(data, path):
#     Path(path).parent.mkdir(parents=True, exist_ok=True)
#     with open(path, "w") as f:
#         json.dump(data, f, indent=4)
#     print(f"[Task 4] Saved → {path}")


# # Process every mask in a box folder
# def process_folder(scene_dir, dims):
#     scene_dir = Path(scene_dir)
#     color, depth, intr = load_scene(scene_dir)

#     masks = sorted(scene_dir.glob("*mask*.png"))
#     if not masks:
#         print(f"No masks in {scene_dir}")
#         return

#     print(f"\nProcessing: {scene_dir} ({len(masks)} masks)")

#     for mask_path in masks:
#         name = mask_path.stem     
#         print(f"\n-> Box: {name}")

#         mask = load_mask(mask_path)
#         pts = depth_to_camera_points(depth, mask, intr)

#         if len(pts) < 50:
#             print(" Skipped: too few points")
#             continue

#         R, t = pca_pose(pts)
#         R, dims_sorted = align_axes_to_dims(R, dims)
#         R = correct_orientation(R)

#         img = draw_axes_only(color, R, t, intr)
#         save_image(img, f"task4_outputs/{name}_axes.png")

#         T_root = to_root_frame(scene_dir, R, t)
#         save_json({"T_root_obj": T_root.tolist()},
#                   f"task4_outputs/{name}_pose.json")




# def main():
#     data_root = Path("/workspace/data")

#     #Known dimensions of boxes in metres
#     dims_medium = np.array([0.255, 0.155, 0.100])
#     dims_small  = np.array([0.340, 0.250, 0.095])

#     process_folder(data_root / "medium_box", dims_medium)
#     process_folder(data_root / "small_box", dims_small)


# if __name__ == "__main__":
#     main()


"""
Task 4 – Multi-Box 6D Pose Estimation (Axes-Only Visualization)
----------------------------------------------------------------

Goal:
Estimate a stable 6D pose (rotation + translation) for each detected box using
only RGB-D data and mask images. The orientation is visualized with 3 coordinate
axes drawn directly on the color image.

Why this works:
- A box is a rigid object with three orthogonal directions.
- Masked depth pixels give us a clean 3D point cloud for each box.
- PCA recovers the dominant geometric directions.
- Since we already know the real physical box dimensions, we can reorder PCA
  axes to ensure the orientation corresponds to an actual box (not arbitrary).
- cam2root.json gives the rigid transform from the camera frame to the robot’s
  root frame, enabling consistent multi-sensor world alignment.
"""

import numpy as np
import cv2
import json
from pathlib import Path
import matplotlib.pyplot as plt


def load_scene(scene_dir):
    """
    Load the colour image, depth map and camera intrinsics.

    Returns numpy arrays for color, depth, and a dictionary for intrinsics.
    """
    scene_dir = Path(scene_dir)

    #Use the camera intrinsics file we have
    with open(scene_dir / "intrinsics.json") as f:
        intr = json.load(f)

    color = cv2.cvtColor(
        cv2.imread(str(scene_dir / "color_image.png")),
        cv2.COLOR_BGR2RGB
    )

    #Load depth
    depth = cv2.imread(str(scene_dir / "raw_depth.png"),
                       cv2.IMREAD_ANYDEPTH).astype(np.float32)

    if depth.max() > 50:
        depth /= 1000.0   # mm -> m

    return color, depth, intr


def load_mask(mask_path):
    """
    Load a mask as a boolean array.
    """
    m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    return m > 0


def depth_to_camera_points(depth, mask, intr):
    """
    Convert masked depth pixels into 3D camera-frame coordinates.

    We use this formula
        X = (u - cx) * Z / fx
        Y = (v - cy) * Z / fy
        Z = depth(u, v)

    Each pixel becomes a 3D point lying along a ray that originates from the camera.
    We also filter out invalid depths because noisy edges or missing values
    can affect PCA calculations.
    """
    fx, fy, cx, cy = intr["fx"], intr["fy"], intr["cx"], intr["cy"]

    ys, xs = np.where(mask)

    Z = depth[ys, xs]
    X = (xs - cx) * Z / fx
    Y = (ys - cy) * Z / fy

    pts = np.stack([X, Y, Z], axis=1)

    #keep only postive, finite points
    return pts[(pts[:, 2] > 0) & np.isfinite(pts[:, 0])]




def pca_pose(pts):
    """
    Recover centroid and the principal axes from raw 3D points.

    Logic:
    - PCA gives us three orthogonal axes in decreasing order of variance.
    - The centroid is simply the mean of all points.

    The pose is not yet true to the correct box dimensions, but it gives a consistent rotation-orthonormal frame.
    """
    t = pts.mean(axis=0)
    P = pts - t

    # A
    H = P.T @ P
    vals, vecs = np.linalg.eigh(H)

    #Sort eigenvectors by descending eigenvalue
    order = np.argsort(-vals)
    R = vecs[:, order]

    #!right-handed coordinate system
    if np.linalg.det(R) < 0:
        R[:, 2] *= -1

    return R, t


#Align axes according to known box dimensions
def align_axes_to_dims(R, dims):
    """
    Align PCA axes to the real-world box dimensions.
    PCA gives correct *orthogonal directions*, but their ordering is arbitrary. The 'longest PCA axis' may correspond to width or height depending on noise.

    Since we know the real physical dimensions, we reorder the axes to imposeva physically meaningful interpretation:
       -  longest size : PCA axis with max spread
       -  medium size : PCA axis with second max spread
       -  shortest size : PCA remaining axis
    """
    #Sort dimemsions in descending order and map PCA axes accordingly
    order = np.argsort(-dims)
    dims_sorted = dims[order]
    R2 = R[:, order]

    if np.linalg.det(R2) < 0:   #to be really sure sign isnt flipped while resorting
        R2[:, 2] *= -1

    return R2, dims_sorted



def correct_orientation(R):
    """
    Ensure the rotation matrix has a consistent direction.

    PCA does not know which way the normal should point.

    Heuristic:
    - If Z-axis points away from the camera, flip it.
    - Then re-orthogonalize the basis.
    """
    #Z-axis should point toward camera (+Z -> more away)
    if R[2, 2] < 0:
        R[:, 2] *= -1

    #Rebuild a clean orthonormal basis
    R[:, 0] = np.cross(R[:, 1], R[:, 2])
    R[:, 0] /= np.linalg.norm(R[:, 0])

    R[:, 1] = np.cross(R[:, 2], R[:, 0])
    R[:, 1] /= np.linalg.norm(R[:, 1])

    return R


def draw_axes_only(color, R, t, intr, axis_length=0.12):
    """
    Draw the object's coordinate frame (X,Y,Z axes) on the RGB image.
    """
    img = color.copy()

    fx, fy, cx, cy = intr["fx"], intr["fy"], intr["cx"], intr["cy"]

    def proj(pt):
        """Project 3D ->pixel coordinates."""
        X, Y, Z = pt
        u = int(fx * X / Z + cx)
        v = int(fy * Y / Z + cy)
        return (u, v)

    origin_2d = proj(t)
    X_2d = proj(t + R[:, 0] * axis_length)
    Y_2d = proj(t + R[:, 1] * axis_length)
    Z_2d = proj(t + R[:, 2] * axis_length)

    #Draw arrows: X=red, Y=green, Z=blue
    cv2.arrowedLine(img, origin_2d, X_2d, (255, 0, 0), 3)
    cv2.arrowedLine(img, origin_2d, Y_2d, (0, 255, 0), 3)
    cv2.arrowedLine(img, origin_2d, Z_2d, (0, 0, 255), 3)

    return img



def to_root_frame(scene_dir, R, t):
    """
    Convert object pose from camera frame to world frame.
    Multiplying cam2root * T_cam_obj gives the object pose in root frame.
    """
    with open(Path(scene_dir) / "cam2root.json") as f:
        raw = json.load(f)

    cam2root = np.array(raw["cam2root"], dtype=float).reshape(4, 4)

    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t

    return cam2root @ T


#utils

def save_image(img, path):
    """Save RGB image (creating directories if needed)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print(f"[Task 4] Saved → {path}")


def save_json(data, path):
    """Save dictionary to JSON with indentation."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[Task 4] Saved → {path}")



def process_folder(scene_dir, dims):
    """
    Process each mask in the directory, treat it as an independent box, and estimate its full 6D pose.
    This function essentially handles the full Task 4 flow.
    """
    scene_dir = Path(scene_dir)
    color, depth, intr = load_scene(scene_dir)

    masks = sorted(scene_dir.glob("*mask*.png"))
    if not masks:
        print(f"No masks in {scene_dir}")
        return

    print(f"\nProcessing: {scene_dir} ({len(masks)} masks)")

    for mask_path in masks:
        name = mask_path.stem
        print(f"\n-> Box: {name}")

        mask = load_mask(mask_path)
        pts = depth_to_camera_points(depth, mask, intr)

        if len(pts) < 50:
            print(" Skipped: too few points (insufficient geometry for PCA)")
            continue

        R, t = pca_pose(pts)
        R, sorted_dims = align_axes_to_dims(R, dims)
        R = correct_orientation(R)

        #Axes visualization
        img = draw_axes_only(color, R, t, intr)
        save_image(img, f"outputs/task4/{name}_axes.png")

        # Pose in world frame
        T_root = to_root_frame(scene_dir, R, t)
        save_json({"T_root_obj": T_root.tolist()},
                f"outputs/task4/{name}_pose.json")


# Run Task4 pipeline

def main():
    """
    Run Task 4 for both provided datasets: medium_box and small_box.

    Each dataset uses different known box dimensions.
    These help disambiguate PCA axis ordering.
    """
    data_root = Path("/workspace/data")

    dims_medium = np.array([0.255, 0.155, 0.100])  # L, W, H in meters
    dims_small  = np.array([0.340, 0.250, 0.095])

    process_folder(data_root / "medium_box", dims_medium)
    process_folder(data_root / "small_box", dims_small)


if __name__ == "__main__":
    main()
