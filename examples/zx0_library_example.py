#!/usr/bin/env python3
"""
Example demonstrating how to use ZX0 as a Python library.

This script shows how to import and use the zx0_compress function
directly from your Python code, without using the command-line interface.
"""

import os
import sys
from zx0 import zx0_compress

def main():
    # Example 1: Compress data from a file
    print("Example 1: Compress data from a file")
    input_file = "example_data.bin"  # Replace with your input file
    
    # Check if the file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        print("Please create this file or modify the script to use an existing file.")
        return
    
    # Read the input file
    with open(input_file, "rb") as f:
        input_data = f.read()
    
    # Compress the data
    compressed_data, stats = zx0_compress(input_data)
    
    # Write the compressed data to a file
    output_file = input_file + ".zx0"
    with open(output_file, "wb") as f:
        f.write(compressed_data)
    
    # Print statistics
    print(f"Compressed {input_file} from {stats['original_size']} to {stats['compressed_size']} bytes")
    print(f"Compression ratio: {stats['ratio']:.4f}")
    print(f"Processing time: {stats['duration']:.2f} seconds")
    print()
    
    # Example 2: Compress in-memory data
    print("Example 2: Compress in-memory data")
    # Create some sample data (a repeating pattern)
    sample_data = bytes([i % 256 for i in range(1000)])
    
    # Compress with different options
    compressed_data, stats = zx0_compress(
        sample_data,
        backwards=True,  # Compress backwards
        quick=True       # Use quick compression
    )
    
    print(f"Compressed in-memory data from {stats['original_size']} to {stats['compressed_size']} bytes")
    print(f"Compression ratio: {stats['ratio']:.4f}")
    print(f"Processing time: {stats['duration']:.2f} seconds")
    print()
    
    # Example 3: Compress part of the data (using skip)
    print("Example 3: Compress with skip")
    skip_bytes = 100
    compressed_data, stats = zx0_compress(
        sample_data,
        skip=skip_bytes  # Skip the first 100 bytes
    )
    
    print(f"Compressed data (skipping first {skip_bytes} bytes) from {stats['original_size']} to {stats['compressed_size']} bytes")
    print(f"Compression ratio: {stats['ratio']:.4f}")
    print(f"Processing time: {stats['duration']:.2f} seconds")

if __name__ == "__main__":
    main()
