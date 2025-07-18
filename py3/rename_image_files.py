import os
import shutil
import argparse
from tqdm import tqdm
from warnings import warn

def parse_args():
    '''Parse command line arguments.

    Returns:
        argparse.Namespace: Command line arguments.
    '''
    parser = argparse.ArgumentParser(description = "Copy and rename images.")
    parser.add_argument(
        "-src", "--src_dir",
        type = str,
        help = "Directory containing images to be copied."
        )
    parser.add_argument(
        "-dst", "--dst_dir",
        type = str,
        help = "Output directory."
        )
    parser.add_argument(
        "-o", "--overwrite",
        action = "store_true",
        help = "Overwrite existing files."
        )
    
    return parser.parse_args()

def rename_img(filename):
    '''Rename image files to the standard format expected by ODM.

    Args:
        filename (str): Original image file name or path.

    Returns:
        str: Standardised image file name or path.
    '''
    basename = os.path.basename(filename)
    dirname = os.path.dirname(filename)
    img_num, img_type, img_band = basename.replace(".", "_").split("_")[2:5]
    out_band, out_ext = ("RGB", ".jpg") if img_band == "JPG" else (
        img_band, ".tif"
        )
    out_name = os.path.join(dirname, f"{img_num}_{out_band}{out_ext}")
    
    return out_name

def copy_images(src_dir, dst_dir, overwrite = False):
    '''Copy images to a new directory and rename them.

    Args:
        src_dir (str): Directory containing images to be copied.
        dst_dir (str): Output directory.
        overwrite (bool): Overwrite existing files with the same name. Default is False.
    '''
    os.makedirs(dst_dir, exist_ok = True)
    image_files = os.listdir(src_dir)
    
    for filename in tqdm(image_files, desc = "Copying images", unit = "file"):
        dst_file = rename_img(os.path.join(dst_dir, filename))
        if filename.endswith(".TIF") or filename.endswith(".JPG"):
            if os.path.isfile(dst_file):
                warn(f"File already exists: {dst_file}.")
                
                if not overwrite:
                    continue
            
            shutil.copy2(os.path.join(src_dir, filename), dst_file)
    
    return

if __name__ == "__main__":
    args = parse_args()
    copy_images(args.src_dir, args.dst_dir, overwrite = args.overwrite)
