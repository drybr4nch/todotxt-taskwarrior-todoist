#!/usr/bin/python3

import os
import shutil
from tqdm import tqdm

def copy_files_with_progress(src, dst):
    total_files = sum([len(files) for r, d, files in os.walk(src)])
    with tqdm(total=total_files, unit='file', desc='Copying files') as pbar:
        for root, dirs, files in os.walk(src):
            for dir in dirs:
                dest_dir = os.path.join(dst, os.path.relpath(os.path.join(root, dir), src))
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dst, os.path.relpath(src_file, src))

                if os.path.exists(dest_file):
                    src_stat = os.stat(src_file)
                    dest_stat = os.stat(dest_file)
                    if src_stat.st_size == dest_stat.st_size and src_stat.st_mtime == dest_stat.st_mtime:
                        # If the file already exists and is the same, skip copying
                        pbar.update(1)
                        continue

                shutil.copy2(src_file, dest_file)
                pbar.update(1)

def delete_extra_files(src, dst):
    for root, dirs, files in os.walk(dst):
        for file in files:
            dst_file = os.path.join(root, file)
            src_file = os.path.join(src, os.path.relpath(dst_file, dst))
            if not os.path.exists(src_file):
                os.remove(dst_file)
                print(f"Deleted: {dst_file}")
        for dir in dirs:
            dst_dir = os.path.join(root, dir)
            src_dir = os.path.join(src, os.path.relpath(dst_dir, dst))
            if not os.path.exists(src_dir):
                shutil.rmtree(dst_dir)
                print(f"Deleted directory: {dst_dir}")

# Define the source and destination paths
source_path = "/mnt/c/users/tadej/Documents"
destination_path = "/mnt/c/Users/tadej/OneDrive - Univerza v Ljubljani/Documents"

# Check if the source directory exists
if not os.path.exists(source_path):
    print(f"The source directory {source_path} does not exist.")
else:
    # Create the destination directory if it does not exist
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

    # Delete extra files in the destination directory
    try:
        delete_extra_files(source_path, destination_path)
        print(f"Deleted extra files in {destination_path} successfully.")
    except Exception as e:
        print(f"Error while deleting extra files: {e}")

    # Copy the source directory to the destination directory with progress
    try:
        copy_files_with_progress(source_path, destination_path)
        print(f"Copied {source_path} to {destination_path} successfully.")
    except Exception as e:
        print(f"Error while copying files: {e}")