#!/usr/bin/env python3
"""
Example demonstrating how to use ZX0 as a library for batch compression.

This script shows how to compress multiple files in a directory,
which would be cumbersome to do with the command-line interface.
"""

import os
import sys
import time
import argparse
from zx0 import zx0_compress

def compress_file(input_path, output_path=None, backwards=False, classic=False, quick=False):
    """Compress a single file using ZX0."""
    # Determine output path if not provided
    if output_path is None:
        output_path = input_path + ".zx0"
    
    # Read input file
    try:
        with open(input_path, "rb") as f:
            input_data = f.read()
    except Exception as e:
        print(f"Error reading {input_path}: {e}")
        return False
    
    # Compress the data
    try:
        compressed_data, stats = zx0_compress(
            input_data,
            backwards=backwards,
            classic=classic,
            quick=quick
        )
    except Exception as e:
        print(f"Error compressing {input_path}: {e}")
        return False
    
    # Write output file
    try:
        with open(output_path, "wb") as f:
            f.write(compressed_data)
    except Exception as e:
        print(f"Error writing {output_path}: {e}")
        return False
    
    # Print statistics
    print(f"{input_path} -> {output_path}: {stats['original_size']} -> {stats['compressed_size']} bytes ({stats['ratio']:.4f})")
    return True

def batch_compress(directory, extension=None, recursive=False, backwards=False, classic=False, quick=False):
    """Compress all files in a directory (and optionally subdirectories)."""
    start_time = time.time()
    success_count = 0
    fail_count = 0
    
    # Function to process a single directory
    def process_directory(dir_path):
        nonlocal success_count, fail_count
        
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            
            # Skip directories if not recursive
            if os.path.isdir(item_path):
                if recursive:
                    process_directory(item_path)
                continue
            
            # Skip files that don't match the extension filter
            if extension and not item.endswith(extension):
                continue
            
            # Skip files that are already compressed
            if item.endswith(".zx0"):
                continue
            
            # Compress the file
            if compress_file(item_path, backwards=backwards, classic=classic, quick=quick):
                success_count += 1
            else:
                fail_count += 1
    
    # Start processing
    try:
        process_directory(directory)
    except Exception as e:
        print(f"Error processing directory {directory}: {e}")
    
    # Print summary
    end_time = time.time()
    print(f"\nBatch compression complete in {end_time - start_time:.2f} seconds")
    print(f"Successfully compressed: {success_count} files")
    if fail_count > 0:
        print(f"Failed to compress: {fail_count} files")

def main():
    parser = argparse.ArgumentParser(
        description="Batch compress files using ZX0",
        epilog="Example: python batch_compress.py data_dir -r -e .bin"
    )
    parser.add_argument("directory", help="Directory containing files to compress")
    parser.add_argument("-r", "--recursive", action="store_true", help="Process subdirectories recursively")
    parser.add_argument("-e", "--extension", help="Only process files with this extension")
    parser.add_argument("-b", "--backwards", action="store_true", help="Compress backwards")
    parser.add_argument("-c", "--classic", action="store_true", help="Use classic file format (v1.*)")
    parser.add_argument("-q", "--quick", action="store_true", help="Use quick non-optimal compression")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a directory")
        return 1
    
    batch_compress(
        args.directory,
        extension=args.extension,
        recursive=args.recursive,
        backwards=args.backwards,
        classic=args.classic,
        quick=args.quick
    )
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
