# ZX0 - Python Port

This repository contains a Python port of **ZX0**, an optimal data compressor originally developed in C by Einar Saukas.

**Original Project:** You can find the original C implementation and more details here:
[https://github.com/einar-saukas/ZX0](https://github.com/einar-saukas/ZX0)

## Description

ZX0 is designed to find the optimal LZ77 parsing for data, particularly targeting scenarios where decompression speed and simplicity are important (like on Z80 microprocessors), while still achieving excellent compression ratios.

This Python version aims to replicate the functionality of the C implementation (specifically targeting v2.2 features) for understanding, experimentation, and use in Python-based environments.

## Features (Mirrored from C v2.2)

*   **Optimal Compression:** Finds the theoretically optimal parsing according to the ZX0 cost model (default).
*   **Quick Mode (`-q`):** Uses a smaller offset limit (like ZX7) for faster, near-optimal compression.
*   **Backwards Compression (`-b`):** Compresses the input file starting from the end.
*   **Skip Bytes (`--skip N`):** Allows skipping a specified number of bytes at the beginning of the input file.
*   **Classic Format (`-c`):** Supports generating output compatible with the older v1 format (disables v2 inverted Elias Gamma bits).
*   **Modern v2 Format:** Default output format unless `-c` or `-b` is specified.

## Requirements

*   Python 3.x (Tested with 3.12+, should work on most recent versions)

## Installation

Normal pip installation

```bash
pip install zx0
```

## Usage

ZX0 can be used either as a command-line tool or as a Python library in your own scripts.

### Command-Line Usage

The main script is zx0.py. Run it from your terminal:

```bash
zx0 [options] input_file [output_file]
```

#### Arguments:

- input_file: Path to the file you want to compress.
- output_file (optional): Path for the compressed output. If omitted, defaults to <input_file>.zx0.

#### Options:

- -f, --force: Force overwrite of the output file if it already exists.
- -c, --classic: Use classic file format (v1.*).
- -b, --backwards: Compress backwards.
- -q, --quick: Use quick (non-optimal) compression mode.
- --skip N: Skip the first N bytes of the input file.

#### Examples:

```bash
# Compress data.bin to data.bin.zx0
zx0 data.bin

# Compress image.raw to compressed.zx0
zx0 image.raw compressed.zx0

# Compress backwards and force overwrite
zx0 code.asm code.zx0 -b -f

# Compress using quick mode, skipping 64 bytes
zx0 level.map level.zx0 -q --skip 64
```

### Library Usage

You can also use ZX0 as a library in your Python scripts:

```python
from zx0 import zx0_compress

# Compress some data
data = b"Your binary data here"
compressed_data, stats = zx0_compress(data)

# Use the compressed data
print(f"Compressed from {stats['original_size']} to {stats['compressed_size']} bytes")
print(f"Compression ratio: {stats['ratio']:.4f}")
```

The `zx0_compress` function accepts the following parameters:

- `input_data` (bytes or bytearray): The data to compress
- `skip` (int, optional): Number of bytes to skip from the beginning. Default: 0
- `backwards` (bool, optional): Compress backwards. Default: False
- `classic` (bool, optional): Use classic file format (v1.*). Default: False
- `quick` (bool, optional): Use quick non-optimal compression. Default: False

It returns a tuple containing:
1. The compressed data as bytes
2. A dictionary with compression statistics:
   - `original_size`: Size of the input data (after skip)
   - `compressed_size`: Size of the compressed data
   - `delta`: Difference between original and compressed sizes
   - `duration`: Time taken to compress in seconds
   - `ratio`: Compression ratio (compressed_size / original_size)

For more examples, see the `examples` directory.

## Files

- zx0.py: The main command-line interface script. Handles arguments, file I/O, and orchestrates the process.
- optimize.py: Implements the core dynamic programming algorithm to find the optimal compression path.
- compress.py: Takes the optimal path and generates the compressed bitstream according to the ZX0 format.
- zx0_common.py: Contains shared constants, the Block class definition, and helper functions/classes used by other modules.

## License

This Python port is licensed under the BSD 3-Clause License, consistent with the original C source code license.
The individual .py files contain the following copyright notice and license terms, as required by the original license:

```python
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
```

## Note

Please be aware that this Python implementation is primarily intended for educational purposes, experimentation, and integration within Python toolchains. Translation from C to python was done using AI model and this implementation is not well tested.
