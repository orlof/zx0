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


# compress.py

import sys
from .zx0_common import Block, BitStreamWriter, INITIAL_OFFSET, elias_gamma_bits

def compress(optimal_end_block: Block or None,
             input_data: bytes,
             input_size: int,
             skip: int,
             backwards_mode: bool,
             invert_mode: bool) -> tuple[bytearray or None, int, int]:
    """
    Generates the compressed data stream from the optimal path.

    Args:
        optimal_end_block: The last block of the optimal path from optimize().
        input_data: The raw input data.
        input_size: Total size of input_data.
        skip: Bytes skipped at the start.
        backwards_mode: Flag for backwards compression mode.
        invert_mode: Flag for Eilas Gamma bit inversion (v2+ format).

    Returns:
        A tuple containing:
        - The compressed data as a bytearray (or None on error).
        - The final size of the compressed data.
        - The calculated delta (max difference between output size and input size during compression).
    """
    if optimal_end_block is None:
        # Handle case where optimization failed or input was empty/skipped
        print("Warning: No optimal block provided to compress.", file=sys.stderr)
        return None, 0, 0

    # Calculate initial output size estimate (for diff calculation)
    # The C code uses (optimal->bits + 25) / 8. Let's use ceiling division.
    # optimal_end_block.bits includes marker bits, but maybe not the final one?
    # Let's add bits for the end marker: 1 + elias_gamma_bits(256)
    # Note: +7 for ceiling division by 8
    estimated_bits = optimal_end_block.bits + 1 + elias_gamma_bits(256)
    output_size_estimate = (estimated_bits + 7) // 8

    # Initialize bit stream writer and state
    writer = BitStreamWriter(backwards_mode, invert_mode)
    writer.diff = output_size_estimate - (input_size - skip) # Initial diff estimate
    delta = 0
    input_index = skip

    # --- Un-reverse the optimal sequence ---
    path = []
    curr = optimal_end_block
    while curr and curr.index >= skip: # Stop at the block before the actual data start
        path.append(curr)
        curr = curr.chain
    path.reverse() # Now path goes from start to end

    if not path:
         print("Warning: Compression path is empty.", file=sys.stderr)
         return None, 0, 0


    # --- Generate output ---
    last_offset = INITIAL_OFFSET
    # Start from the first *real* block (index >= skip)
    # The chain pointer connects blocks, length is difference in indices
    for i in range(len(path)):
        current_block = path[i]
        # Determine the previous index to calculate length
        # Handle the very first block correctly (previous index is skip-1)
        prev_index = path[i-1].index if i > 0 else skip - 1
        length = current_block.index - prev_index

        if length <= 0 and i > 0:
             # This shouldn't happen in a valid path, but check defensively
             print(f"Warning: Zero or negative length ({length}) detected in path at index {i}", file=sys.stderr)
             continue


        # --- Write block based on type (offset) ---
        if current_block.offset == 0:
            # Literals block
            writer.write_bit(0) # Literal indicator bit
            writer.write_interlaced_elias_gamma(length) # Literals length

            # Write literal bytes
            for _ in range(length):
                if input_index >= input_size:
                     raise IndexError(f"Input index {input_index} out of bounds reading literals.")
                writer.write_byte(input_data[input_index])
                # Update state after writing byte
                input_index += 1
                writer.diff += 1 # Input byte consumed, potentially increasing diff relative to initial estimate
                if delta < writer.diff:
                    delta = writer.diff

        else:
            # Match block (copy)
            offset = current_block.offset

            if offset == last_offset:
                # Copy from last offset
                writer.write_bit(0) # Copy indicator bit (shared with literal)
                writer.write_interlaced_elias_gamma(length) # Copy length
                # Update state after determining block type and length
                input_index += length
                # diff doesn't change here directly, but input bytes are consumed
                writer.diff += length
                if delta < writer.diff:
                    delta = writer.diff
            else:
                # Copy from new offset
                writer.write_bit(1) # New offset indicator bit

                # Write offset MSB (Elias Gamma coded)
                offset_msb = (offset - 1) // 128 + 1
                writer.write_interlaced_elias_gamma(offset_msb)

                # Write offset LSB (raw byte, adjusted)
                offset_lsb = (offset - 1) % 128
                if backwards_mode:
                     byte_val = offset_lsb << 1
                else:
                     byte_val = (127 - offset_lsb) << 1
                writer.write_byte(byte_val) # LSB byte written, MSB of byte is 0 for now
                # The LSB (bit 0) of this byte will be set later by write_bit if backtrack=True

                # Write copy length (Elias Gamma coded, length-1)
                writer.backtrack = True # Next write_bit modifies the LSB of the byte just written
                if length < 1:
                     raise ValueError("Match length must be at least 1 for new offset.")
                writer.write_interlaced_elias_gamma(length - 1)

                # Update state after determining block type, offset, and length
                input_index += length
                writer.diff += length # Input bytes consumed
                if delta < writer.diff:
                    delta = writer.diff

                last_offset = offset

    # --- End marker ---
    writer.write_bit(1) # End marker indicator bit
    writer.write_interlaced_elias_gamma(256) # Value > 255 indicates end

    # Final check/adjustment for delta
    # The C code calculates delta based on `diff` which tracks `output_index - input_index` offset by initial estimate.
    # Let's recalculate delta based on the actual final size if needed, though the running max should be correct.
    final_output_size = len(writer.output_data)

    return writer.output_data, final_output_size, delta
