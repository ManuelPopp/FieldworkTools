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
        nargs = "+",
        help = "Directory or directories containing images to be copied."
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

def rename_img(filename, index = None, max_img = 1000):
    '''Rename image files to the standard format expected by ODM.

    Args:
        filename (str): Original image file name or path.
        index (int, optional): Index to use in the new file name. If None,
            the original index from the file name is used. Default is None.
        max_img (int, optional): Maximum number of images to process.
            Default is 1000.

    Returns:
        str: Standardised image file name or path.
    '''
    basename = os.path.basename(filename)
    dirname = os.path.dirname(filename)
    img_num, img_type, img_band = basename.replace(".", "_").split("_")[2:5]
    out_band, out_ext = ("RGB", ".jpg") if img_band == "JPG" else (
        img_band, ".tif"
        )
    
    num_digits = len(str(int(abs(max_img))))
    image_num = img_num if index is None else str(
        int(index) + 1
        ).zfill(num_digits)

    out_name = os.path.join(
            dirname, f"{image_num}_{out_band}{out_ext}"
        )
    
    return out_name

def copy_images(src_dir, dst_dir, overwrite = False):
    '''Copy images to a new directory and rename them.

    Args:
        src_dir (str): Directory containing images to be copied.
        dst_dir (str): Output directory.
        overwrite (bool): Overwrite existing files with the same name.
        Default is False.
    '''
    os.makedirs(dst_dir, exist_ok = True)
    if not isinstance(src_dir, list):
        src_dir = [src_dir]
    
    image_files = list()
    image_paths = list()
    for directory in src_dir:
        for file in os.listdir(directory):
            if file.endswith((".TIF", ".JPG")):
                image_files.append(file)
                image_paths.append(os.path.join(directory, file))
    
    file_basenames = [
        "_".join(
            file.replace("_D.", "_D_D.").split("_")[:-2]
            ) for file in image_paths
        ]

    basename_setlist = list()
    for file in file_basenames:
        if file not in basename_setlist:
            basename_setlist.append(file)
    
    image_indices = [basename_setlist.index(file) for file in file_basenames]
    for index, filename, filepath in zip(
        image_indices,
        tqdm(image_files, desc = "Copying images", unit = "file"),
        image_paths
        ):
        if len(src_dir) > 1:
            dst_file = rename_img(
                os.path.join(dst_dir, filename), index = index,
                max_img = len(image_files)
                )
        else:
            dst_file = rename_img(os.path.join(dst_dir, filename))
        
        if filename.endswith(".TIF") or filename.endswith(".JPG"):
            if os.path.isfile(dst_file):
                warn(f"File already exists: {dst_file}.")
                
                if not overwrite:
                    continue
            
            shutil.copy2(filepath, dst_file)
    
    return

if __name__ == "__main__":
    args = parse_args()
    copy_images(args.src_dir, args.dst_dir, overwrite = args.overwrite)
