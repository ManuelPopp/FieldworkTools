import os
import sys
import glob
import numpy
import argparse
import subprocess
from PIL import Image

# Settings
osname = "windows" if os.name == "nt" else "linux"
fext = ".exe" if os.name == "nt" else ""

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
src_files = glob.glob(os.path.join(args.src_directory, "*T.JPG"))

for src_file in src_files:
    raw_file = os.path.join(
        prj_raw,
        os.path.basename(src_file).replace(".JPG", ".raw")
    )
    tif_file = os.path.join(
        prj_tif,
        os.path.basename(src_file).replace(".JPG", ".tif")
    )
    subprocess.run(
        [
            "dji_irp" + fext,
            "-s", src_file,
            "-a", "measure",
            "-o", raw_file,
            "--measuremefmt", "float32"
            ],
        cwd = dji_sdk_dir,
        check = True
        )
    img = Image.open(src_file)
    width = img.width
    height = img.height
    raw_arr = numpy.fromfile(
        os.path.join(prj_raw, raw_file),
        dtype = numpy.float32
    )
    scaling = 2 * raw_arr.shape[0] / (width * height)
    tif_arr = raw_arr.reshape((int(height * scaling), int(width * scaling)))
    exf = img.getexif()
    tif_arr.save(
        tif_file,
        format = "TIFF",
        exif = exf
    )
    del img
    del tif_arr

# Run ODM
subprocess.run([
    "docker", "run", "-ti", "--rm",
    "-v", f"{os.path.abspath(args.prj_directory)}:/datasets",
    "opendronemap/odm",
    "--project-path", "/datasets", "project"
])

# End
print("Thermal orthomosaic creation complete.")
sys.sleep(5)