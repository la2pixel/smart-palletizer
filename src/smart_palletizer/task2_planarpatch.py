"""
Task 2- Planar Patch Detection(3D)

For each *_raw.ply point cloud, this script extracts planar surfaces with RANSAC algorithm and some simple post-processing. 
The goal of the script is to identify the major visible faces of each box.

Pipeline:
    1.Extract planes iteratively using RANSAC
    2.Merge planes with similar normals
    3.Keep the largest 1 to 2 planes per box
    4.Assign each plane as 'top' or 'side' based on normal and extent
    5.Save visualization to 'outputs/task2/'

"""

from pathlib import Path
import os
import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt


def extract_planes(pcd, dist=0.005, min_pts=350, max_iter=2000):
    """Extract planar patches by iterative RANSAC."""
    planes = []
    remaining = pcd

    while True:
        pts = np.asarray(remaining.points)
        if pts.shape[0] < min_pts:
            break

        model, inliers = remaining.segment_plane(dist, 3, max_iter)
        if len(inliers) < min_pts:
            break

        patch = pts[inliers]
        normal = model[:3] / np.linalg.norm(model[:3])
        extent = np.ptp(patch, axis=0)

        if abs(normal[2]) > 0.8 and extent[2] < 0.5 * max(extent[0], extent[1]):
            label = "top"
        else:
            label = "side"

        planes.append({
            "normal": normal,
            "points": patch,
            "center": patch.mean(axis=0),
            "extent": extent,
            "num": patch.shape[0],
            "label": label,
        })

        # remove inliers
        mask = np.ones(len(pts), dtype=bool)
        mask[inliers] = False
        pts = pts[mask]

        remaining = o3d.geometry.PointCloud()
        remaining.points = o3d.utility.Vector3dVector(pts)

    return planes


def merge_planes(planes, tol=0.15):
    """Merge planes with nearly identical normals."""
    if len(planes) <= 1:
        return planes

    merged = []
    used = set()

    for i, p1 in enumerate(planes):
        if i in used:
            continue

        group = [p1]
        n1 = p1["normal"]

        for j, p2 in enumerate(planes):
            if j in used or j == i:
                continue

            if abs(np.dot(n1, p2["normal"])) > (1 - tol):
                group.append(p2)
                used.add(j)

        best = max(group, key=lambda p: p["num"])
        merged.append(best)
        used.add(i)

    return merged


def save_gridplot_full(results, out_path, rows=4, cols=4):
    """
    Create a grid where each subplot shows the full point cloud of a box with its extracted planar patches overlaid 

    results : dict {ply_stem: [plane_dict, ...]}
    """
    keys = list(results.keys())
    if len(keys) == 0:
        return

    N = min(len(keys), rows * cols)

    fig = plt.figure(figsize=(cols * 4, rows * 4))
    colors = ["tab:red", "tab:blue", "tab:green", "tab:purple"]

    for idx in range(N):
        stem = keys[idx]
        planes = results[stem]
        if not planes:
            continue

     
        ply_name = stem + ".ply"
        ply_path = None

        for root, dirs, files in os.walk("/workspace/data"):
            if ply_name in files:
                ply_path = os.path.join(root, ply_name)
                break

        if ply_path is None:
            continue

        pcd = o3d.io.read_point_cloud(ply_path)
        pts = np.asarray(pcd.points)

        #downsampling full cloud for plotting
        if pts.shape[0] > 5000:
            idxs = np.random.choice(pts.shape[0], 5000, replace=False)
            pts = pts[idxs]

        ax = fig.add_subplot(rows, cols, idx + 1, projection="3d")
        ax.set_title(stem, fontsize=8)

        #full cloud
        ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
                   s=1, c="lightgray", alpha=0.3)

        for i, p in enumerate(planes):
            pts_p = p["points"]
            col = colors[i % len(colors)]
            ax.scatter(pts_p[:, 0], pts_p[:, 1], pts_p[:, 2],
                       s=3, c=col, alpha=0.9)

        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=180)
    plt.close(fig)

    print("[GRID SAVED]", out_path)


def planes_for_box(ply_path, keep=2):
    """Return strongest 1 or 2 planes for one box."""
    pcd = o3d.io.read_point_cloud(str(ply_path))
    pts = np.asarray(pcd.points)

    print(f"Processing {ply_path.name}: {len(pts)} points")

    if len(pts) == 0:
        return []

    planes = extract_planes(pcd)
    if not planes:
        return []

    planes = merge_planes(planes)
    planes = sorted(planes, key=lambda p: p["num"], reverse=True)

    return planes[:keep]


#Run this for Task 2 pipeline

def run_task2(base_dir, verbose=False, save_viz=False):
    """
    Run Task 2 on all *_raw.ply files under `base_dir`.

    Returns:
        dict: { ply_stem : [planes] }
    """
    base = Path(base_dir)
    ply_files = sorted(base.rglob("*_raw.ply"))

    print("\nTASK 2\n")
    print("Searching in:", base.resolve(), "\n")

    if not ply_files:
        print("No *_raw.ply files found.")
        return {}

    results = {}

    for ply in ply_files:
        planes = planes_for_box(ply)
        results[ply.stem] = planes

        labels = [p["label"] for p in planes]
        print(f"{ply.stem}: {len(planes)} planes → {labels}")

        if verbose:
            for i, p in enumerate(planes):
                n = p["normal"]
                c = p["center"]
                e = p["extent"]
                print(f"    [{i}] {p['label']}: "
                      f"normal={n.round(3)} "
                      f"center={c.round(3)} "
                      f"extent={e.round(3)} "
                      f"points={p['num']}")
        print()

        #individual visualizations are disabled as requested.
        # if save_viz:
        #     save_plane_vis(ply, planes)

    if save_viz:
        out_dir = "outputs/task2"
        os.makedirs(out_dir, exist_ok=True)

        small_entries = {k: v for (k, v) in results.items() if "small_box" in k}
        medium_entries = {k: v for (k, v) in results.items() if "medium_box" in k}

        save_gridplot_full(
            small_entries,
            os.path.join(out_dir, "task2_grid_smallbox.png"),
            rows=4, cols=4
        )

        save_gridplot_full(
            medium_entries,
            os.path.join(out_dir, "task2_grid_mediumbox.png"),
            rows=2, cols=2
        )

    return results
