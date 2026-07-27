import os
import sys
import glob
import numpy
import argparse
import subprocess
from PIL import Image

# Settings
osname = "windows" if os.name in ["windows", "nt"] else "linux"
fext = ".exe" if os.name in ["windows", "nt"] else ""

dji_sdk_dir = os.path.join(
    os.path.dirname(__file__), "utility", "bin", osname, "release_x68"
    )

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
prj_raw = os.path.join(args.prj_directory, "raw")
prj_tif = os.path.join(args.prj_directory, "images")

if not os.path.exists(prj_raw):
    os.makedirs(prj_raw)

if not os.path.exists(prj_tif):
    os.makedirs(prj_tif)

# Process images
print(f"DJI SDK in {dji_sdk_dir}.")

src_files = glob.glob(os.path.join(args.src_directory, "*T.JPG"))
print(f"Found {len(src_files)} thermal images in {args.src_directory}.")

for src_file in src_files:
    print(f"Processing {src_file}...")
    src_file_norm = os.path.normpath(src_file).replace("\\", "/")
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
    subprocess.run(
        [
            "./dji_irp" + fext,
            "-s", src_file_norm,
            "-a", "measure",
            "-o", raw_file_norm,
            "--measuremefmt", "float32"
            ],
        cwd = dji_sdk_dir,
        check = True
        )
    img = Image.open(src_file)
    width = img.width
    height = img.height
    raw_arr = numpy.fromfile(
        os.path.join(prj_raw, raw_file_norm),
        dtype = numpy.float32
    )
    scaling = 2 * raw_arr.shape[0] / (width * height)
    tif_arr = raw_arr.reshape((int(height * scaling), int(width * scaling)))
    exf = img.getexif()
    tif_arr.save(
        tif_file_norm,
        format = "TIFF",
        exif = exf
    )
    del img
    del tif_arr
    print(f"Saved {tif_file}.")

# Run ODM
print("Running OpenDroneMap...")
subprocess.run([
    "docker", "run", "-ti", "--rm",
    "-v", f"{os.path.abspath(args.prj_directory)}:/datasets",
    "opendronemap/odm",
    "--project-path", "/datasets", "project"
])

# End
print("Thermal orthomosaic creation complete.")
sys.sleep(5)