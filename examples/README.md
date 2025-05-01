# ZX0 Library Usage Examples

This directory contains examples demonstrating how to use ZX0 as a Python library in your own scripts.

## Example Files

- `zx0_library_example.py`: Shows how to import and use the `zx0_compress` function directly from your Python code.
- `batch_compress.py`: Demonstrates a practical use case - batch compressing multiple files in a directory. This would be cumbersome to do with the command-line interface.

## Running the Examples

To run the examples, make sure you have installed the ZX0 package:

```bash
pip install zx0
```

Then you can run the example scripts:

```bash
# Basic library usage example
python examples/zx0_library_example.py

# Batch compression example
python examples/batch_compress.py /path/to/directory -r -e .bin
```

Notes:
- The `zx0_library_example.py` script looks for a file named `example_data.bin` in the current directory. You'll need to create this file or modify the script to use an existing file.
- The `batch_compress.py` script takes a directory path as an argument and compresses all files in that directory. Use the `-r` flag to process subdirectories recursively, and the `-e` flag to only process files with a specific extension.

## Using ZX0 in Your Own Projects

To use ZX0 in your own Python projects, simply import the `zx0_compress` function:

```python
from zx0 import zx0_compress

# Compress some data
data = b"Your binary data here"
compressed_data, stats = zx0_compress(data)

# Use the compressed data
print(f"Compressed from {stats['original_size']} to {stats['compressed_size']} bytes")
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
