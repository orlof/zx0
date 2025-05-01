#!/usr/bin/env python3

# This Python file is a translation/port of the ZX0 C implementation.
#
# Original C code Author: Einar Saukas
# Original C code License: BSD 3-Clause
#
# --- Start of Original C Code Notice ---
#
# (c) Copyright 2021 by Einar Saukas. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * The name of its author may not be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# --- End of Original C Code Notice ---

# This Python translation is also licensed under the BSD 3-Clause License,
# consistent with the original C code license.

# zx0.py - Main compression script

import sys
import argparse
import os
import time

# Import from our modules
from .zx0_common import MAX_OFFSET_ZX0, MAX_OFFSET_ZX7
from .optimize import optimize
from .compress import compress

def reverse_bytearray(data: bytearray):
    """Reverses a bytearray in-place."""
    left, right = 0, len(data) - 1
    while left < right:
        data[left], data[right] = data[right], data[left]
        left += 1
        right -= 1

def zx0_compress(input_data: bytes | bytearray,
                 skip: int = 0,
                 backwards: bool = False,
                 classic: bool = False,
                 quick: bool = False) -> tuple[bytes, dict]:
    """
    Compresses the input data using the ZX0 algorithm.

    Args:
        input_data: The raw byte data to compress.
        skip: Number of bytes to skip from the beginning of input_data. Defaults to 0.
        backwards: Compress in reverse order. Defaults to False.
        classic: Use classic v1 format (affects invert_mode). Defaults to False.
        quick: Use faster, less optimal compression (ZX7 offset limit). Defaults to False.

    Returns:
        A tuple containing:
        - compressed_data: The compressed data as bytes.
        - stats: A dictionary with compression statistics like
                 {'original_size': int, 'compressed_size': int,
                  'delta': int, 'duration': float}.
                 original_size refers to the size of the data actually compressed (after skip).

    Raises:
        ValueError: If skip value is invalid or input_data is empty/too short after skip.
        RuntimeError: If optimization or compression fails internally.
    """
    # Validate input
    input_size = len(input_data)
    if input_size == 0:
        raise ValueError("Empty input data")
    
    if skip < 0:
        raise ValueError(f"Invalid skip value {skip}")
    
    if skip >= input_size:
        raise ValueError(f"Skip value {skip} exceeds input data size {input_size}")
    
    # Make input data mutable if needed
    if isinstance(input_data, bytes):
        input_data = bytearray(input_data)
    
    # Start timing
    start_time = time.time()
    
    # Conditionally reverse input for backwards mode
    if backwards:
        reverse_bytearray(input_data)
        # Note: The 'skip' parameter applies to the *original* file start.
        # In backwards mode, the effective data to compress is the *last*
        # (input_size - skip) bytes of the original file, which are now
        # at the *beginning* of the reversed buffer.
        effective_input_size = input_size
        effective_skip = 0  # We process from the start of the reversed buffer
        data_to_compress_len = input_size - skip  # This is the amount of data we care about
    else:
        # Normal mode: compress data from index `skip` onwards
        effective_input_size = input_size
        effective_skip = skip
        data_to_compress_len = input_size - skip
    
    offset_limit = MAX_OFFSET_ZX7 if quick else MAX_OFFSET_ZX0
    
    # Invert mode logic (v2+ feature, disabled for classic or backwards)
    invert_mode = not classic and not backwards
    
    # Run Optimization
    optimal_block = optimize(input_data, effective_input_size, effective_skip, offset_limit)
    
    if optimal_block is None:
        raise RuntimeError("Optimization failed")
    
    # Run Compression
    output_data, output_size, delta = compress(
        optimal_block, input_data, effective_input_size, effective_skip,
        backwards, invert_mode
    )
    
    if output_data is None:
        raise RuntimeError("Compression failed")
    
    # Conditionally reverse output data if compressing backwards
    if backwards:
        reverse_bytearray(output_data)
    
    # Calculate stats
    end_time = time.time()
    duration = end_time - start_time
    
    stats = {
        'original_size': data_to_compress_len,
        'compressed_size': output_size,
        'delta': delta,
        'duration': duration,
        'ratio': (output_size / data_to_compress_len if data_to_compress_len > 0 else 0)
    }
    
    # Return compressed data as bytes and stats
    return bytes(output_data), stats

def main():
    parser = argparse.ArgumentParser(
        description="ZX0 v2.2 (Python): Optimal data compressor by Einar Saukas.",
        epilog="Example: python zx0.py input.bin output.zx0 -b"
    )
    parser.add_argument("input", help="Input file name")
    parser.add_argument("output", nargs='?', help="Output file name (defaults to input + '.zx0')")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite of output file")
    parser.add_argument("-c", "--classic", action="store_true", help="Classic file format (v1.*) - affects invert_mode")
    parser.add_argument("-b", "--backwards", action="store_true", help="Compress backwards")
    parser.add_argument("-q", "--quick", action="store_true", help="Quick non-optimal compression (uses smaller offset limit)")
    # Allow specifying skip offset like the C version, although less common in Python tools
    parser.add_argument("--skip", type=int, default=0, help="Number of bytes to skip from the beginning (default: 0)")


    if len(sys.argv) == 1:
        # Replicate C behavior: print usage if no args
        # Get script name correctly
        script_name = os.path.basename(sys.argv[0])
        if script_name == "__main__.py": # If run via python -m zx0
             script_name = "python -m zx0"
        elif not script_name.endswith(".py"): # If running an executable wrapper (pyinstaller etc)
             script_name = "zx0" # Assume it's named zx0
        else:
            script_name = f"python {script_name}" # Default if run as python zx0.py

        # Mimic C usage string structure
        print(f"Usage: {script_name} [-f] [-c] [-b] [-q] [--skip N] input [output.zx0]", file=sys.stderr)
        print("  -f         Force overwrite of output file", file=sys.stderr)
        print("  -c         Classic file format (v1.*)", file=sys.stderr)
        print("  -b         Compress backwards", file=sys.stderr)
        print("  -q         Quick non-optimal compression", file=sys.stderr)
        print("  --skip N   Skip N bytes at the start", file=sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    input_name = args.input
    output_name = args.output

    # Determine output filename if not provided
    if output_name is None:
        output_name = input_name + ".zx0"

    # --- Input File Handling ---
    try:
        with open(input_name, "rb") as ifp:
            input_data_bytes = ifp.read()
    except FileNotFoundError:
        print(f"Error: Cannot access input file {input_name}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error: Cannot read input file {input_name}: {e}", file=sys.stderr)
        sys.exit(1)

    input_size = len(input_data_bytes)
    if input_size == 0:
        print(f"Error: Empty input file {input_name}", file=sys.stderr)
        sys.exit(1)

    # --- Skip Validation ---
    skip = args.skip
    if skip < 0:
        print(f"Error: Invalid skip value {skip}", file=sys.stderr)
        sys.exit(1)
    if skip >= input_size:
        print(f"Error: Skipping entire input file {input_name}", file=sys.stderr)
        sys.exit(1)

    # --- Output File Handling ---
    if not args.force and os.path.exists(output_name):
        print(f"Error: Already existing output file {output_name} (use -f to overwrite)", file=sys.stderr)
        sys.exit(1)

    # Use the library function to compress the data
    try:
        if args.backwards:
            print("Compressing backwards...")
            
        output_data, stats = zx0_compress(
            input_data_bytes,
            skip=skip,
            backwards=args.backwards,
            classic=args.classic,
            quick=args.quick
        )
        
        # --- Write Output File ---
        try:
            with open(output_name, "wb") as ofp:
                bytes_written = ofp.write(output_data)
                if bytes_written != stats['compressed_size']:
                    raise IOError("Failed to write all compressed bytes")
        except IOError as e:
            print(f"Error: Cannot write output file {output_name}: {e}", file=sys.stderr)
            # Attempt to clean up potentially partially written file
            try:
                os.remove(output_name)
            except OSError:
                pass
            sys.exit(1)
            
        # --- Final Report ---
        print(f"File{(' partially' if skip > 0 else '')} compressed{(' backwards' if args.backwards else '')} from {stats['original_size']} to {stats['compressed_size']} bytes! (delta {stats['delta']})")
        print(f"Compression ratio: {stats['ratio']:.4f}")
        print(f"Processing time: {stats['duration']:.2f} seconds")
        
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
