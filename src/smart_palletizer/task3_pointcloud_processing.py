"""smart_palletizer/task3_pointcloud_processing.py

Point-cloud cleaning utilities for Task 3.
"""
import open3d as o3d
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import os

def clean_pointcloud(input_path, output_path=None):
	"""
	Post-processes point clouds with specific parameters for small and medium boxes.
	Saves cleaned file to `output_path`.

	Parameters
	----------
	input_path : str or Path
		Path to the input raw point cloud (PLY).
	output_path : str or Path, optional
		Where to write the cleaned point cloud. If None, a sibling filename
		with `_clean.ply` is used.

	Returns
	-------
	tuple
		(pcd_original, pcd_cleaned) as open3d.geometry.PointCloud objects.
	"""
	p = Path(input_path)
	folder = p.parent.name

	# final working parameters after some trial and error
	if "medium" in folder:
		crop_percentile = 1
		margin = 0.005      # 5 mm
		nb_neighbors = 8
	else:  # small box
		crop_percentile = 1
		margin = 0.003      # 3 mm
		nb_neighbors = 6

	pcd = o3d.io.read_point_cloud(str(input_path))
	pts = np.asarray(pcd.points)

	# crop by percentile
	low = np.percentile(pts, crop_percentile, axis=0)
	high = np.percentile(pts, 100 - crop_percentile, axis=0)
	aabb = o3d.geometry.AxisAlignedBoundingBox(low - margin, high + margin)
	pcd_crop = pcd.crop(aabb)

	# outlier removal
	pcd_clean, _ = pcd_crop.remove_statistical_outlier(
		nb_neighbors=nb_neighbors,
		std_ratio=3.0
	)

	# if output_path isn't provided, derive it from the input filename
	if output_path is None:
		output_path = p.with_name(p.stem.replace("_raw", "_clean") + ".ply")

	o3d.io.write_point_cloud(str(output_path), pcd_clean)

	return pcd, pcd_clean


def run_task3(data_root):
	"""
	Run Task 3 cleaning on raw point clouds for small and medium box categories.
	Saves cleaned files next to raw ones in their respective data folders.
	"""
	data_root = Path(data_root)

	for folder in ["small_box", "medium_box"]:
		box_dir = data_root / folder
		if not box_dir.exists():
			print(f"skipped missing folder: {folder}")
			continue

		print(f"processing folder: {folder}")
		raw_files = sorted(box_dir.glob("*_raw.ply"))

		for raw_path in raw_files:
			print(f"   - cleaning: {raw_path.name}")

			# filename generate
			clean_path = raw_path.with_name(
				raw_path.stem.replace("_raw", "_clean") + ".ply"
			)

			clean_pointcloud(str(raw_path), str(clean_path))
			print(f"saved cleaned file here: {clean_path.name}")

			# create per-file before/after visualization
			try:
				pcd_raw = o3d.io.read_point_cloud(str(raw_path))
				pcd_clean = o3d.io.read_point_cloud(str(clean_path))
				pts_raw = np.asarray(pcd_raw.points)
				pts_clean = np.asarray(pcd_clean.points)

				out_dir = Path("outputs") / "task3"
				out_dir.mkdir(parents=True, exist_ok=True)
				out_name = raw_path.stem.replace("_raw", "_before_after") + ".png"
				plot_grid(pts_raw, pts_clean, out_dir=str(out_dir), out_name=out_name)
				print(f"wrote visualization: {out_dir / out_name}")
			except Exception as e:
				print(f"WARNING: failed to create visualization for {raw_path.name}: {e}")

	print("\nPost-processing complete.\n")


def plot_grid(raw_pts, clean_pts, out_dir="task3_outputs", out_name="pointcloud_visualization.png"):
	"""Create and save a 2x2 grid visualization of raw vs cleaned points.

	Saves to `os.path.join(out_dir, out_name)`.
	"""

	# Compute shared axis limits for XY
	xmin = min(raw_pts[:, 0].min(), clean_pts[:, 0].min())
	xmax = max(raw_pts[:, 0].max(), clean_pts[:, 0].max())
	ymin = min(raw_pts[:, 1].min(), clean_pts[:, 1].min())
	ymax = max(raw_pts[:, 1].max(), clean_pts[:, 1].max())

	# Shared limits for XZ
	zmin = min(raw_pts[:, 2].min(), clean_pts[:, 2].min())
	zmax = max(raw_pts[:, 2].max(), clean_pts[:, 2].max())

	fig, ax = plt.subplots(2, 2, figsize=(12, 10))

	# RAW XY
	ax[0, 0].scatter(raw_pts[:, 0], raw_pts[:, 1], s=1)
	ax[0, 0].set_title("RAW XY")
	ax[0, 0].set_xlim([xmin, xmax])
	ax[0, 0].set_ylim([ymin, ymax])
	ax[0, 0].set_aspect("equal", "box")

	# CLEAN XY
	ax[0, 1].scatter(clean_pts[:, 0], clean_pts[:, 1], s=1)
	ax[0, 1].set_title("CLEAN XY")
	ax[0, 1].set_xlim([xmin, xmax])
	ax[0, 1].set_ylim([ymin, ymax])
	ax[0, 1].set_aspect("equal", "box")

	# RAW XZ
	ax[1, 0].scatter(raw_pts[:, 0], raw_pts[:, 2], s=1)
	ax[1, 0].set_title("RAW XZ")
	ax[1, 0].set_xlim([xmin, xmax])
	ax[1, 0].set_ylim([zmin, zmax])
	ax[1, 0].set_aspect("equal", "box")

	# CLEAN XZ
	ax[1, 1].scatter(clean_pts[:, 0], clean_pts[:, 2], s=1)
	ax[1, 1].set_title("CLEAN XZ")
	ax[1, 1].set_xlim([xmin, xmax])
	ax[1, 1].set_ylim([zmin, zmax])
	ax[1, 1].set_aspect("equal", "box")

	plt.tight_layout()
	os.makedirs(out_dir, exist_ok=True)
	out_file = os.path.join(out_dir, out_name)
	plt.savefig(out_file, dpi=100, bbox_inches="tight")
	print(f"[Task3] Plot saved to {out_file}")
	plt.close()


