import os
import sys
import glob
import numpy
import platform
import argparse
import subprocess
import tifffile
import rasterio as rio
from PIL import Image

# Settings
architecture = "release_x64" if platform.architecture()[0] == "64bit" \
    else "release_x86"

osname = "windows" if os.name in ["windows", "nt"] else "linux"
fext = ".exe" if os.name in ["windows", "nt"] else ""

dji_sdk_dir = os.path.join(
    os.path.dirname(__file__), "utility", "bin", osname, architecture
    )
dji_sdk_dir_norm = os.path.normpath(dji_sdk_dir).replace("\\", "/")

# Get input arguments
parser = argparse.ArgumentParser(
    description = "Create a thermal orthomosaic from a set of images"
    )
parser.add_argument(
    "-src_dir", "--src_directory", type = str, required = True,
    help = "Input directory containing thermal images"
)
parser.add_argument(
    "-prj_dir", "--prj_directory", type = str, required = True,
    help = "Project directory"
)

args = parser.parse_args()

# Create directories
prj_main = os.path.abspath(os.path.dirname(args.prj_directory))
prj_main_norm = os.path.normpath(prj_main).replace("\\", "/")
prj_raw = os.path.join(args.prj_directory, "raw")
prj_tif = os.path.join(args.prj_directory, "images")

orthomosaic_file = os.path.join(
    args.prj_directory, "odm_orthophoto", "odm_orthphoto.tif"
    )

orthomosaic_scaled_file = os.path.join(
    prj_main, "thermal_mosaic.tif"
    )

if not os.path.exists(prj_main):
    os.makedirs(prj_main)

if not os.path.exists(prj_raw):
    os.makedirs(prj_raw)

if not os.path.exists(prj_tif):
    os.makedirs(prj_tif)

# Process images
print(f"DJI SDK in {dji_sdk_dir_norm}.")

src_files = glob.glob(os.path.join(args.src_directory, "*T.JPG"))
print(f"Found {len(src_files)} thermal images in {args.src_directory}.")

# Process JPEG files
for src_file in src_files:
    src_file_norm = os.path.normpath(src_file).replace("\\", "/")
    print(f"Processing {src_file_norm}.")
    raw_file = os.path.join(
        prj_raw,
        os.path.basename(src_file).replace(".JPG", ".raw")
    )
    raw_file_norm = os.path.normpath(raw_file).replace("\\", "/")

    if os.path.exists(raw_file):
        print(f"{raw_file} already exists. Skipping.")
        continue

    print(
        " ".join([
            os.path.join(dji_sdk_dir_norm, "dji_irp" + fext),
            "-s", src_file_norm, "-a", "measure",
            "-o", raw_file_norm, "--measurefmt", "float32"
            ])
        )
    subprocess.run(
        [
            os.path.join(dji_sdk_dir_norm, "dji_irp" + fext),
            "-s", src_file_norm,
            "-a", "measure",
            "-o", raw_file_norm,
            "--measurefmt", "float32"
            ],
        check = True
        )
    print(f"Saved {raw_file}.")

# Check scaling values
global_min = numpy.inf
global_max = -numpy.inf

for src_file in src_files:
    src_file_norm = os.path.normpath(src_file).replace("\\", "/")
    raw_file = os.path.join(
        prj_raw,
        os.path.basename(src_file).replace(".JPG", ".raw")
    )
    raw_arr = numpy.fromfile(
            os.path.join(prj_raw, raw_file_norm),
            dtype = numpy.float32
        )
    global_min = min(global_min, numpy.nanmin(raw_arr))
    global_max = max(global_max, numpy.nanmax(raw_arr))

with open(os.path.join(prj_main, "scaling.txt"), "w") as f:
    f.write(f"min: {global_min}\n")
    f.write(f"max: {global_max}\n")

# Process .raw files
for src_file in src_files:
    src_file_norm = os.path.normpath(src_file).replace("\\", "/")
    print(f"Processing {src_file_norm}.")
    raw_file = os.path.join(
        prj_raw,
        os.path.basename(src_file).replace(".JPG", ".raw")
    )
    raw_file_norm = os.path.normpath(raw_file).replace("\\", "/")
    tif_file = os.path.join(
        prj_tif,
        os.path.basename(src_file).replace(".JPG", ".tif")
    )
    tif_file_norm = os.path.normpath(tif_file).replace("\\", "/")

    if os.path.exists(tif_file):
        print(f"{tif_file} already exists. Skipping.")
        continue

    img = Image.open(src_file)
    width = img.width
    height = img.height
    raw_arr = numpy.fromfile(
        os.path.join(prj_raw, raw_file_norm),
        dtype = numpy.float32
    )
    scaling = 2 * raw_arr.shape[0] / (width * height)
    tif_arr = raw_arr.reshape((int(height * scaling), int(width * scaling)))
    tif_arr_scaled = (tif_arr - global_min) / (global_max - global_min)
    tifffile.imwrite(tif_file_norm, tif_arr_scaled.astype(numpy.float32))
    subprocess.run(
        [
            "exiftool",
            "-TagsFromFile", src_file_norm,
            "-EXIF:all",
            "-XMP:all",
            "-GPS:all",
            "-overwrite_original", tif_file_norm
            ],
        check = True
        )
    del img
    del tif_arr
    print(f"Saved {tif_file}.")

# Run ODM
if not os.path.isfile(orthomosaic_file):
    print("Running OpenDroneMap...")
    subprocess.run([
        "docker", "run", "-ti", "--rm",
        "-v", f"{prj_main_norm}:/datasets",
        "opendronemap/odm",
        "--project-path", "/datasets", "project"
    ])
    print("Thermal orthomosaic creation complete.")
else:
    print(f"{orthomosaic_file} already exists. Skipping ODM.")

# Re-scale the orthomosaic to the original temperature range
if os.path.isfile(orthomosaic_file) and not os.path.isfile(
    orthomosaic_scaled_file
    ):
    print("Re-scaling the orthomosaic to the original temperature range...")
    with rio.open(orthomosaic_file, "r+") as src:
        arr = src.read(1)
        arr_scaled = arr * (global_max - global_min) + global_min

        profile = src.profile
        profile.update(
            dtype = rio.float32,
            count = 1
        )

    with rio.open(orthomosaic_scaled_file, "w", **profile) as dst:
        dst.write(arr_scaled.astype(rio.float32), 1)
elif os.path.isfile(orthomosaic_scaled_file):
    print(f"{orthomosaic_scaled_file} already exists. Skipping re-scaling.")
else:
    print(f"{orthomosaic_file} does not exist. Cannot re-scale.")