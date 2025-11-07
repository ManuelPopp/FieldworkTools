import os
import shutil

dji_directory = "C:/Users/dme/Documents/DJI/DJITerra/dme@wsl.ch"
sample_main = "F:/FIELDWORK"
sample_directories = os.listdir(sample_main)

# Copy DJI Terra results for Mavic 3M
for sample in sample_directories:
    print(f"Processing M3M sample: {sample}")
    if os.path.exists(os.path.join(dji_directory, sample + "MS")):
        dst_dir = os.path.join(sample_main, sample, "DJITerra")

        # Copy level 0 files
        src_dir = os.path.join(dji_directory, sample + "MS", "map")
        tif_files_src = [f for f in os.listdir(src_dir) if f.endswith(".tif")]
        tif_files_dst = [
            f if not f == "dsm.tif" else "dsm_m3m.tif" for f in tif_files_src
            ]
        print(f"M3M source files: {tif_files_src}")
        print(f"Copy to: {tif_files_dst}")
        for f_src, f_dst in zip(tif_files_src, tif_files_dst):
            shutil.copy(
                os.path.join(src_dir, f_src),
                os.path.join(dst_dir, f_dst)
                )
        
        # Copy level -1 files
        src_dir = os.path.join(dji_directory, sample + "MS", "map", "index_map")
        tif_files = [f for f in os.listdir(src_dir) if f.endswith(".tif")]
        print(f"M3M maps: {tif_files}")
        for f in tif_files:
            if os.path.exists(
                os.path.join(src_dir, f)
                ) and not os.path.exists(os.path.join(dst_dir, f)):
                shutil.copy(
                    os.path.join(src_dir, f),
                    os.path.join(dst_dir, f)
                    )

# Copy DJI Terra results for L2
additional_files = {
    "lidars": "cloud_merged.las",
    "terra_dsm": "dsm.tif",
    "terra_dom": "dom.tif",
    "terra_dem": "dem.tif"
}

for sample in sample_directories:
    print(f"Processing L2 sample: {sample}")
    if os.path.exists(os.path.join(dji_directory, sample + "LiDAR")):
        for subfolder, filename in additional_files.items():
            src_path = os.path.join(
                dji_directory, sample + "LiDAR", "map", subfolder, filename
                )
            dst_path = os.path.join(
                sample_main, sample, "DJITerra", filename
                )
            if os.path.exists(src_path) and not os.path.exists(dst_path):
                shutil.copy(src_path, dst_path)