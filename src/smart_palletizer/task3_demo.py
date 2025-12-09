# smart_palletizer/task3_demo.py 
import open3d as o3d
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path 

def plot_grid(raw_pts, clean_pts, save_path): # Shared XY bounds 
xmin = min(raw_pts[:,0].min(), clean_pts[:,0].min()) 
xmax = max(raw_pts[:,0].max(), clean_pts[:,0].max()) 
ymin = min(raw_pts[:,1].min(), clean_pts[:,1].min()) 
ymax = max(raw_pts[:,1].max(), clean_pts[:,1].max()) 

# Shared XZ bounds 
zmin = min(raw_pts[:,2].min(), clean_pts[:,2].min()) 
zmax = max(raw_pts[:,2].max(), clean_pts[:,2].max()) 
fig, ax = plt.subplots(2, 2, figsize=(12, 10)) 
# RAW XY 
ax[0,0].scatter(raw_pts[:,0], raw_pts[:,1], s=1) 
ax[0,0].set_title("RAW XY") ax[0,0].set_xlim([xmin, xmax]); 
ax[0,0].set_ylim([ymin, ymax]) ax[0,0].set_aspect("equal", "box") 
# CLEAN XY 
ax[0,1].scatter(clean_pts[:,0], clean_pts[:,1], s=1) 
ax[0,1].set_title("CLEAN XY") ax[0,1].set_xlim([xmin, xmax]); 
ax[0,1].set_ylim([ymin, ymax]) ax[0,1].set_aspect("equal", "box") 
# RAW XZ 
ax[1,0].scatter(raw_pts[:,0], raw_pts[:,2], s=1) 
ax[1,0].set_title("RAW XZ") 
ax[1,0].set_xlim([xmin, xmax]); 
ax[1,0].set_ylim([zmin, zmax]) 
ax[1,0].set_aspect("equal", "box") 
# CLEAN XZ
ax[1,1].scatter(clean_pts[:,0], clean_pts[:,2], s=1) 
ax[1,1].set_title("CLEAN XZ") 
ax[1,1].set_xlim([xmin, xmax]); 
ax[1,1].set_ylim([zmin, zmax]) 
ax[1,1].set_aspect("equal", "box") 
plt.tight_layout() 
plt.savefig(save_path, dpi=200) 
plt.close() print(f"saved plots here: {save_path}") 

#run task3 demo pipeline 
def run_task3_demo(data_root): 
    data_root = Path(data_root) 
    out_dir = Path("task3_visualizations") 
    out_dir.mkdir(exist_ok=True) 
    print("\nStarting demo visualizations") 
    
    for folder in ["small_box", "medium_box"]: 
        box_dir = data_root / folder 
        raw_files = sorted(box_dir.glob("*_raw.ply")) 
        print(f"\n→ Folder: {folder}") 
        
    for raw_path in raw_files: 
        print(f" - {raw_path.name}") 
        clean_path = raw_path.with_name( raw_path.stem.replace("_raw", "_clean") + ".ply" ) 
        if not clean_path.exists(): 
            print(f" Missing cleaned file → skipped {clean_path.name}") \
            continue 
            
        #load both clouds
        raw_pcd = o3d.io.read_point_cloud(str(raw_path)) 
        clean_pcd = o3d.io.read_point_cloud(str(clean_path)) 
        raw_pts = np.asarray(raw_pcd.points) 
        clean_pts = np.asarray(clean_pcd.points) 
        fig_path = out_dir / f"{raw_path.stem}_grid.png" 
        plot_grid(raw_pts, clean_pts, fig_path) 
        print("\nTask 3 demo Completed for all boxes.\n")