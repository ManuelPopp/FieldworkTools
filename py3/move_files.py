# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import os
import shutil
import hashlib
import pickle as pk
from glob import glob
from tqdm import tqdm

def file_hash(path, algo = "sha256", chunk_size = 1024 * 1024):
    h = hashlib.new(algo)
    
    with open(path, "rb") as f:
        h.update(f.read(chunk_size))
    
    return h.hexdigest()

def equal_content(*files):
    hashes = [file_hash(f) for f in files]
    
    return len(set(hashes)) == 1

src_dir = "/media/pi1/FieldBackup/FIELDWORK"
dst_dir = "/media/dme/plotdata"
airborne_dst = os.path.join(dst_dir, "measurments", "airborne")
ground_dst = os.path.join(dst_dir, "measurments", "ground")

overwrite = False

# Metadata filepattern
boundary_src = os.path.join(src_dir, "{plot}", "{plot}_boundary.gpkg")
boundary_dst = os.path.join(
    dst_dir, "metadata", "boundaries", "{plot}_boundary.gpkg"
    )
gpx_src = os.path.join(src_dir, "{plot}", "{plot}.gpx")
gpx_dst = os.path.join(dst_dir, "metadata", "gpx", "{plot}.gpx")

# LiDAR filepattern
lidar_src = os.path.join(src_dir, "{plot}", "DJITerra", "cloud_merged.las")
lidar_dst = os.path.join(
    airborne_dst, "lidar", "pointclouds", "{plot}", "{plot}_pointcloud.las"
    )

dem_src = os.path.join(src_dir, "{plot}", "DJITerra", "dem.tif")
dem_dst = os.path.join(airborne_dst, "lidar", "dem", "{plot}", "{plot}_dem.tif")

dom_src = os.path.join(src_dir, "{plot}", "DJITerra", "dom.tif")
dom_dst = os.path.join(airborne_dst, "lidar", "dom", "{plot}", "{plot}_dom.tif")

dsm_src = os.path.join(src_dir, "{plot}", "DJITerra", "dsm.tif")
dsm_dst = os.path.join(airborne_dst, "lidar", "dsm", "{plot}", "{plot}_dsm.tif")

lidarmeta_src = os.path.join(src_dir, "{plot}", "{plot}_L2_report.txt")
lidarmeta_dst = os.path.join(airborne_dst, "lidar", "metadata", "{plot}_L2_report.txt")

# Multispectral filepattern
rgb_src = os.path.join(src_dir, "{plot}", "DJITerra", "result.tif")
rgb_dst = os.path.join(airborne_dst, "multispectral", "rgb", "{plot}", "{plot}_rgb.tif")

ms_dsm_src = os.path.join(src_dir, "{plot}", "DJITerra", "dsm_m3m.tif")
ms_dsm_dst = os.path.join(airborne_dst, "multispectral", "dsm", "{plot}", "{plot}_m3m_dsm.tif")

gndvi_src = os.path.join(src_dir, "{plot}", "DJITerra", "GNDVI.tif")
gndvi_dst = os.path.join(airborne_dst, "multispectral", "gndvi", "{plot}", "{plot}_gndvi.tif")

gsddsm_src = os.path.join(src_dir, "{plot}", "DJITerra", "gsddsm.tif")
gsddsm_dst = os.path.join(airborne_dst, "multispectral", "gsddsm", "{plot}", "{plot}_gsddsm.tif")

lci_src = os.path.join(src_dir, "{plot}", "DJITerra", "LCI.tif")
lci_dst = os.path.join(airborne_dst, "multispectral", "lci", "{plot}", "{plot}_lci.tif")

ndre_src = os.path.join(src_dir, "{plot}", "DJITerra", "NDRE.tif")
ndre_dst = os.path.join(airborne_dst, "multispectral", "ndre", "{plot}", "{plot}_ndre.tif")

ndvi_src = os.path.join(src_dir, "{plot}", "DJITerra", "NDVI.tif")
ndvi_dst = os.path.join(airborne_dst, "multispectral", "ndvi", "{plot}", "{plot}_ndvi.tif")

osavi_src = os.path.join(src_dir, "{plot}", "DJITerra", "OSAVI.tif")
osavi_dst = os.path.join(airborne_dst, "multispectral", "osavi", "{plot}", "{plot}_osavi.tif")

green_src = os.path.join(src_dir, "{plot}", "DJITerra", "result_Green.tif")
green_dst = os.path.join(airborne_dst, "multispectral", "green", "{plot}", "{plot}_green.tif")

nir_src = os.path.join(src_dir, "{plot}", "DJITerra", "result_NIR.tif")
nir_dst = os.path.join(airborne_dst, "multispectral", "nir", "{plot}", "{plot}_nir.tif")

red_src = os.path.join(src_dir, "{plot}", "DJITerra", "result_Red.tif")
red_dst = os.path.join(airborne_dst, "multispectral", "red", "{plot}", "{plot}_red.tif")

rededge_src = os.path.join(src_dir, "{plot}", "DJITerra", "result_RedEdge.tif")
rededge_dst = os.path.join(airborne_dst, "multispectral", "rededge", "{plot}", "{plot}_rededge.tif")

msmeta_src = os.path.join(src_dir, "{plot}", "{plot}_M3M_report.txt")
msmeta_dst = os.path.join(airborne_dst, "multispectral", "metadata", "{plot}_M3M_report.txt")

# Licor data
licor_src = os.path.join(src_dir, "{plot}", "Licor", "{plot}.csv")
licor_dst = os.path.join(ground_dst, "par", "licor", "{plot}", "{plot}.csv")

sources = [
    boundary_src, gpx_src, lidar_src, dem_src, dom_src, dsm_src, lidarmeta_src,
    rgb_src, ms_dsm_src, gndvi_src, gsddsm_src, lci_src, ndre_src, ndvi_src,
    osavi_src, green_src, nir_src, red_src, rededge_src, licor_src
    ]

destinations = [
    boundary_dst, gpx_dst, lidar_dst, dem_dst, dom_dst, dsm_dst, lidarmeta_dst,
    rgb_dst, ms_dsm_dst, gndvi_dst, gsddsm_dst, lci_dst, ndre_dst, ndvi_dst,
    osavi_dst, green_dst, nir_dst, red_dst, rededge_dst, licor_dst
    ]

# Loop over plots
plot_folders = os.listdir(src_dir)
exceptions = []

for i, folder in enumerate(plot_folders):
    print(f"Copying files for {folder} ({i} of {len(plot_folders)})")
    if not any([
            os.path.isdir(os.path.join(src_dir, folder)) for f in [
                "DJITerra", "Licor"
                ]
            ]) or folder == "00_template":
        continue
    
    plot = folder.lower()
    
    for src, dst in tqdm(zip(sources, destinations)):
        srcf = src.format(plot = folder)
        dstf = dst.format(plot = plot)
        exists = os.path.isfile(srcf)
        
        if exists and os.path.isfile(dstf):
            equal = equal_content(srcf, dstf)
            if not equal:
                print(
                    f"src: {srcf} and dst: {dstf} both exist but files " +
                    "differ. Overwriting dst."
                    )
        else:
            equal = False
        
        if overwrite or not equal:
            try:
                parent = os.path.dirname(dstf)
                os.makedirs(parent, exist_ok = True)
                shutil.copy(srcf, dstf)
            
            except Exception as e:
                exceptions.append(e)
                with open(os.path.join(src_dir, "move_files.err"), "wb") as f:
                    pk.dump(exceptions, f, protocol = 4)
                    print(e)
        else:
            print(
                f"File already exists: {dstf}. Set overwrite=True to overwrite."
                )

# Copy TOC photos
print("Copying TOC photos...")
toc_photo_src = os.path.join(src_dir, "{plot}", "TOCPhotos")
toc_photo_dst = os.path.join(airborne_dst, "visible_spectrum", "{plot}")

for i, folder in enumerate(plot_folders):
    print(f"Copying files for {folder} ({i + 1} of {len(plot_folders)})")
    
    if not any([
            os.path.isdir(os.path.join(src_dir, folder)) for f in ["TOCPhotos"]
            ]) or folder in ["00_template", ["zz_misc"]]:
        continue
    
    plot = folder.lower()
    src = toc_photo_src
    dst = toc_photo_dst
    
    parent = os.path.dirname(dst).format(plot = plot)
    os.makedirs(parent, exist_ok = True)
    sources = glob(toc_photo_src.format(plot = folder) + "/*.JPG")
    
    for src in sources:
        dst = os.path.join(
            toc_photo_dst.format(plot = plot), os.path.basename(src).lower()
            )
        
        try:
            shutil.copy(src, dst)
        except Exception as e:
            exceptions.append(e)
            
            with open(os.path.join(src_dir, "move_files.err"), "wb") as f:
                pk.dump(exceptions, f, protocol = 4)
                print(e)

print(
      f"All finished. View {os.path.join(src_dir, 'move_files.err')} to" +
      " check for errors."
      )