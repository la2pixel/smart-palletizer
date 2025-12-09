"""
Task 1- 2D Detection

This script detects the visible 2D bounding boxes for small and medium boxes using the provided instance masks.
For each mask, the visible region is extracted, a rotated bounding box is fitted, and basic metadata such as confidence and visible fraction are computed. 
Small boxes are processed first-then their combined mask is used to remove occluded areas from the medium box.

The output consists of two images saved to 'outputs/task1' showing the final overlays and detected boxes.
"""
import os
import glob
import cv2
import numpy as np


TASK1_OUT_DIR = os.path.join("outputs", "task1")


def aabb_from_points(box_pts: np.ndarray) -> list:
    """
    Compute axis-aligned bounding box (AABB) from rotated box corners.

    Parameters
    ----------
    box_pts : ndarray, shape (4, 2)
        Corner coordinates from cv2.boxPoints.

    Returns
    -------
    list
        [xmin, ymin, xmax, ymax] as floats.
    """
    xs = box_pts[:, 0]
    ys = box_pts[:, 1]
    return [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]


def iou_aabb(b1, b2) -> float:
    """
    Compute IoU (Intersection over Union) between two axis-aligned boxes.

    Parameters
    ----------
    b1 : list of float
        First bounding box [xmin, ymin, xmax, ymax].
    b2 : list of float
        Second bounding box [xmin, ymin, xmax, ymax].

    Returns
    -------
    float
        IoU value in the range [0,1].
    """
    x1_min, y1_min, x1_max, y1_max = b1
    x2_min, y2_min, x2_max, y2_max = b2

    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)

    iw = max(0.0, inter_xmax - inter_xmin)
    ih = max(0.0, inter_ymax - inter_ymin)
    inter_area = iw * ih

    area1 = max(0.0, x1_max - x1_min) * max(0.0, y1_max - y1_min)
    area2 = max(0.0, x2_max - x2_min) * max(0.0, y2_max - y2_min)

    denom = area1 + area2 - inter_area + 1e-6
    return inter_area / denom if denom > 0.0 else 0.0


def suppress_overlapping(dets, iou_thresh: float = 0.9):
    """
    Apply a simple non-maximum suppression (NMS) based on IoU and confidence.

    Parameters
    ----------
    dets : list of dict
        Each detection must contain keys 'confidence' and 'aabb'.
    iou_thresh : float
        IoU threshold for suppression.

    Returns
    -------
    list of dict
        Detection list after NMS.
    """
    dets = sorted(dets, key=lambda d: d["confidence"], reverse=True)
    kept = []
    for d in dets:
        bb = d["aabb"]
        if all(iou_aabb(bb, k["aabb"]) < iou_thresh for k in kept):
            kept.append(d)
    return kept


def build_union_mask(mask_dir: str, pattern: str):
    """
    Build a union mask from all masks in a directory.

    Parameters
    ----------
    mask_dir : str
        Directory containing mask images.
    pattern : str
        Glob pattern matching mask filenames.

    Returns
    -------
    ndarray or None
        Binary mask (uint8, values {0,1}) representing union of all masks.
    """
    paths = sorted(glob.glob(os.path.join(mask_dir, pattern)))
    union = None
    for p in paths:
        m = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        if m is None:
            continue
        mb = (m > 0).astype(np.uint8)
        union = mb if union is None else np.logical_or(union, mb).astype(np.uint8)
    return union


def detect_from_masks(
    image_path: str,
    mask_dir: str,
    mask_pattern: str,
    category_name: str,
    color_rgb: tuple,
    occluder_mask=None,
    visible_fraction_thresh: float | None = None,
    verbose: bool = False,
):
    """
    Detect 2D boxes from instance masks and draw them on the image.

    Parameters
    ----------
    image_path : str
        Path to the input BGR image.
    mask_dir : str
        Directory containing segmentation masks.
    mask_pattern : str
        Glob pattern for mask filenames.
    category_name : str
        Category label (e.g., "small_box", "medium_box").
    color_rgb : tuple of int
        RGB color used for overlays and contours.
    occluder_mask : ndarray or None
        Mask of occluding objects, removed from visible region.
    visible_fraction_thresh : float or None
        Minimum visible fraction required to keep detection.
    verbose : bool
        If True, prints per-mask visibility info.

    Returns
    -------
    vis_rgb : ndarray
        Visualization image (RGB).
    dets : list of dict
        Detection metadata.
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise FileNotFoundError(image_path)

    vis_bgr = img_bgr.copy()

    mask_paths = sorted(glob.glob(os.path.join(mask_dir, mask_pattern)))
    if verbose:
        print(f"\n[{category_name}] Found {len(mask_paths)} masks in {mask_dir}")

    raw_dets = []

    for mpath in mask_paths:
        mask = cv2.imread(mpath, cv2.IMREAD_GRAYSCALE)
        if mask is None:
            continue

        fg = (mask > 0).astype(np.uint8)

        if occluder_mask is not None:
            vis_mask = fg.copy()
            vis_mask[(occluder_mask > 0) & (fg > 0)] = 0
        else:
            vis_mask = fg

        total = int(fg.sum())
        visible = int(vis_mask.sum())
        visible_frac = visible / total if total > 0 else 0.0

        if verbose:
            print(
                f"{category_name} {os.path.basename(mpath)}   "
                f"visible_frac={visible_frac:.4f}"
            )

        if visible_fraction_thresh is not None and visible_frac < visible_fraction_thresh:
            continue

        contours, _ = cv2.findContours(
            (vis_mask * 255).astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        if not contours:
            continue

        cnt = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(cnt)
        box_pts = cv2.boxPoints(rect).astype(int)
        area_rect = cv2.contourArea(box_pts)
        if area_rect <= 0:
            continue

        conf = float(np.clip(cv2.contourArea(cnt) / area_rect, 0.0, 1.0))
        aabb = aabb_from_points(box_pts)

        raw_dets.append(
            {
                "category": category_name,
                "mask_file": os.path.basename(mpath),
                "confidence": conf,
                "visible_fraction": visible_frac,
                "box_points": box_pts.tolist(),
                "aabb": aabb,
                "color": color_rgb,
            }
        )

        #Mask overlay on colorimage
        cbgr = np.array(color_rgb[::-1], dtype=np.uint8)
        overlay = np.zeros_like(vis_bgr, dtype=np.uint8)
        overlay[:] = cbgr
        alpha = 0.4

        mask_3c = np.repeat((fg > 0)[:, :, None], 3, axis=2)
        vis_bgr = np.where(
            mask_3c,
            (alpha * overlay + (1 - alpha) * vis_bgr).astype(np.uint8),
            vis_bgr,
        )

    dets = suppress_overlapping(raw_dets)

    #Draw contours+ labels for detections
    for d in dets:
        pts = np.array(d["box_points"], dtype=int)
        cbgr = d["color"][::-1]
        cv2.drawContours(vis_bgr, [pts], 0, cbgr, 2)

        x_min = int(min(p[0] for p in pts))
        y_min = int(min(p[1] for p in pts))

        label = f"{d['category']} {d['confidence']*100:.0f}%"
        text_y = max(y_min + 20, 20)

        cv2.putText(
            vis_bgr,
            label,
            (x_min, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

    return cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB), dets


def save_image(window_name: str, img_rgb: np.ndarray, out_dir: str = TASK1_OUT_DIR):
    """
    Save visualization outputs.

    Parameters
    ----------
    window_name : str
        Logical identifier for output.
    img_rgb : ndarray
        RGB image to save.
    out_dir : str
        Directory where output is written.
    """
    os.makedirs(out_dir, exist_ok=True)
    fname = window_name.lower().replace(" ", "_") + ".png"
    out_path = os.path.join(out_dir, fname)
    cv2.imwrite(out_path, img_rgb[:, :, ::-1])  #RGB -> BGR
    print("[SAVED]", out_path)

#Runs the task1 piepline
def run_task1(base_dir: str, verbose: bool = False):
    """
    Run Task 1 (2D bounding box detection).

    Parameters
    ----------
    base_dir : str
        Dataset root containing 'small_box/' and 'medium_box/'.
    verbose : bool
        If True, print summary and per-mask visibility.

    Returns
    -------
    tuple
        small_vis, medium_vis, small_dets, medium_dets
    """
    image_path = os.path.join(base_dir, "medium_box", "color_image.png")

    #Small boxes (no occlusion removal)
    small_vis, small_dets = detect_from_masks(
        image_path=image_path,
        mask_dir=os.path.join(base_dir, "small_box"),
        mask_pattern="small_box_mask_*.png",
        category_name="small_box",
        color_rgb=(0, 255, 0),
        occluder_mask=None,
        visible_fraction_thresh=None,
        verbose=verbose,
    )

    #Union of small boxes as occluder mask
    small_union = build_union_mask(
        os.path.join(base_dir, "small_box"),
        "small_box_mask_*.png",
    )

    #Medium box with occlusion removed within threshold visible fraction
    medium_vis, medium_dets = detect_from_masks(
        image_path=image_path,
        mask_dir=os.path.join(base_dir, "medium_box"),
        mask_pattern="medium_box_mask_*.png",
        category_name="medium_box",
        color_rgb=(255, 0, 0),
        occluder_mask=small_union,
        visible_fraction_thresh=0.5,
        verbose=verbose,
    )

    save_image("Small boxes", small_vis, out_dir=TASK1_OUT_DIR)
    save_image("Medium box", medium_vis, out_dir=TASK1_OUT_DIR)

    if verbose:
        print("Small boxes detected :", len(small_dets))
        print("Medium boxes detected:", len(medium_dets))

    return small_vis, medium_vis, small_dets, medium_dets


