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

# optimize.py

import sys
from .zx0_common import Block, INITIAL_OFFSET, elias_gamma_bits, offset_ceiling, MAX_SCALE

def optimize(input_data: bytes, input_size: int, skip: int, offset_limit: int) -> Block or None:
    """
    Find the optimal compression path using dynamic programming.

    Args:
        input_data: The raw data to compress (as bytes or bytearray).
        input_size: The total size of input_data.
        skip: Number of bytes to skip at the beginning of input_data.
        offset_limit: Maximum offset allowed for matches.

    Returns:
        The final Block object representing the end of the optimal path,
        or None if no compression path is found (e.g., empty input after skip).
    """
    max_offset = offset_ceiling(input_size - 1, offset_limit)
    if max_offset < INITIAL_OFFSET: # Handle very small inputs
         max_offset = INITIAL_OFFSET

    # Allocate main data structures
    # Using lists instead of C pointers. None indicates no block assigned yet.
    # +1 for max_offset because C arrays were size max_offset+1
    last_literal = [None] * (max_offset + 1) # Stores the last literal block ending at a given offset
    last_match = [None] * (max_offset + 1)   # Stores the last match block ending at a given offset
    optimal = [None] * input_size            # Stores the optimal block ending at each index
    match_length = [0] * (max_offset + 1)    # Current match length for each offset
    # best_length[L] = Smallest M <= L such that block(index-M) + cost(M) is minimal
    best_length = [0] * input_size           # Max length needed is input_size

    if input_size > 2 + skip:
         # Initialize best_length for length 2 if possible
        if 2 < len(best_length): # Check bounds
            best_length[2] = 2

    print("Optimizing:", end="")
    sys.stdout.flush()

    # Start with a fake block before the actual data (index skip-1)
    # Note: bits=-1 is just a marker, doesn't affect calculations starting from index=skip
    start_block = Block(bits=-1, index=skip - 1, offset=INITIAL_OFFSET, chain=None)
    last_match[INITIAL_OFFSET] = start_block # Initialize for offset 1

    dots = 0

    # Process remaining bytes
    for index in range(skip, input_size):
        current_max_offset = offset_ceiling(index, offset_limit)
        best_len_size = 2 # Minimum match length is 2 for offset copies

        for offset in range(INITIAL_OFFSET, current_max_offset + 1):
            if index >= offset and input_data[index] == input_data[index - offset]:
                # --- Match found ---
                match_len = match_length[offset] + 1

                # 1. Try extending the previous literal run with this offset
                if last_literal[offset]:
                    prev_block = last_literal[offset]
                    # Length of copy is 1 (the current matching byte)
                    # The cost includes the literal run ending at prev_block->index,
                    # the 'copy from last offset' indicator (1 bit),
                    # and the Elias Gamma code for length 1.
                    length = 1 # A match starts, length 1 initially from this offset
                               # Wait, the C code calculates length as index - prev_block->index
                               # This seems wrong. If last_literal[offset] exists, it means
                               # input[index-1] != input[index-1-offset].
                               # Now input[index] == input[index-offset].
                               # This seems to initiate a match of length 1 *from this offset*.
                               # Let's re-read the C code carefully.

                    # C code: length = index - last_literal[offset]->index;
                    # This 'length' is the length of the *match* using the *last offset*.
                    # The C comment "copy from last offset" might be slightly misleading here.
                    # It seems to mean "start a match using this offset, which was last used for literals".

                    # Let's rethink: If last_literal[offset] is set, it means the *last* block using this offset
                    # was a literal block. That block ended at last_literal[offset]->index.
                    # The data between that index and the current `index` are implicitly literals.
                    # Now, at `index`, we find input[index] == input[data-offset].
                    # This signifies the *start* of a potential match using `offset`.
                    # The cost calculation in C: prev_block->bits + 1 + elias_gamma_bits(length)
                    # where length = index - prev_block->index. This length seems to be the number of
                    # *intermediate literals* before this match of length 1 starts? No, that looks more like
                    # the 'copy literals' case below.

                    # Revisiting C optimize.c, line 73:
                    # /* copy from last offset */
                    # if (last_literal[offset]) {
                    #     length = index-last_literal[offset]->index; // This is the length of the MATCH
                    #     bits = last_literal[offset]->bits + 1 + elias_gamma_bits(length); // cost(prev) + copy_last_flag(1) + cost(length)
                    #     assign(&last_match[offset], allocate(bits, index, offset, last_literal[offset])); // Create block ENDING here
                    #     if (!optimal[index] || optimal[index]->bits > bits)
                    #         assign(&optimal[index], last_match[offset]); // Update optimal if better
                    # }
                    # This implies a match of `length` ending at `index`, using the `offset`.
                    # It connects back to the `last_literal[offset]` block.
                    # This interpretation seems more consistent with the cost structure.

                    # Let's stick to the C code's logic for now:
                    length = index - last_literal[offset].index # Length of this match sequence
                    if length > 0: # Cannot have zero length match
                        bits = last_literal[offset].bits + 1 + elias_gamma_bits(length)
                        new_block = Block(bits, index, offset, last_literal[offset])
                        last_match[offset] = new_block # Update last match for this offset
                        if optimal[index] is None or optimal[index].bits > bits:
                            optimal[index] = new_block

                # 2. Try starting/extending a match using a *new* offset context
                # (or continuing a match from a previous step for this offset)
                match_length[offset] = match_len # Increment current run length for this offset

                if match_len > 1: # Only makes sense if match is longer than 1 byte
                     # Update best_length array if needed
                    if best_len_size < match_len:
                        # Calculate optimal length M for matches ending at `index`,
                        # where M is between best_len_size and match_len.
                        # We look back from index-M.
                        prev_optimal = optimal[index - best_length[best_len_size]]
                        if prev_optimal is not None: # Need a valid previous optimal path
                           bits = prev_optimal.bits + elias_gamma_bits(best_length[best_len_size] - 1)
                           while best_len_size < match_len:
                                best_len_size += 1
                                # Ensure index-best_len_size is valid
                                if index - best_len_size >= skip -1 : # Need valid optimal path back
                                    prev_optimal2 = optimal[index - best_len_size]
                                    if prev_optimal2 is not None:
                                        bits2 = prev_optimal2.bits + elias_gamma_bits(best_len_size - 1)
                                        if bits2 <= bits:
                                            best_length[best_len_size] = best_len_size
                                            bits = bits2
                                        else:
                                            best_length[best_len_size] = best_length[best_len_size - 1]
                                    else:
                                         # If no path back, can't use this length, inherit previous best
                                         best_length[best_len_size] = best_length[best_len_size - 1]

                                else:
                                     # Index out of bounds, can't use this length
                                     best_length[best_len_size] = best_length[best_len_size - 1]

                        else:
                             # If no optimal path back for the base case, inherit previous best lengths
                             while best_len_size < match_len:
                                 best_len_size += 1
                                 best_length[best_len_size] = best_length[best_len_size - 1]


                    # Now, calculate cost using the optimal length derived from best_length table
                    length = best_length[match_len] # Optimal length for this match run
                    # Ensure we have a valid previous block to connect to
                    if index - length >= skip - 1 and optimal[index - length] is not None :
                        # Cost = prev_optimal_bits + cost_new_offset_flag(1) + cost_offset_msb + cost_offset_lsb(8) + cost_length
                        # cost_offset_msb = elias_gamma_bits((offset-1)//128 + 1)
                        # cost_length = elias_gamma_bits(length-1)
                        offset_msb = (offset - 1) // 128 + 1
                        bits = optimal[index - length].bits + 1 + elias_gamma_bits(offset_msb) + 8 + elias_gamma_bits(length - 1)

                        # Update last_match[offset] only if this path is better *for this offset*
                        # or if it's the first match ending here for this offset
                        if last_match[offset] is None or last_match[offset].index != index or last_match[offset].bits > bits:
                           new_block = Block(bits, index, offset, optimal[index - length])
                           last_match[offset] = new_block
                           # Update optimal[index] if this path is better overall for this index
                           if optimal[index] is None or optimal[index].bits > bits:
                               optimal[index] = new_block
                    # else: Cannot form this path if optimal[index - length] doesn't exist

            else:
                # --- No match: potential end of a match run, start of literals ---
                match_length[offset] = 0 # Reset match length for this offset

                # If the last operation involving this offset was a match,
                # we now transition to literals. Record this possibility.
                if last_match[offset]:
                    prev_block = last_match[offset]
                    # Length of the literal run is from the end of the previous match block
                    length = index - prev_block.index
                    if length > 0:
                        # Cost = prev_match_bits + cost_literal_flag(1) + cost_len + cost_literal_bytes
                        bits = prev_block.bits + 1 + elias_gamma_bits(length) + length * 8
                        new_block = Block(bits, index, 0, prev_block) # Offset 0 means literal
                        last_literal[offset] = new_block # Update last literal for this offset context
                        # Update optimal if this path is better
                        if optimal[index] is None or optimal[index].bits > bits:
                            optimal[index] = new_block


        # Indicate progress
        processed_bytes = index - skip + 1
        total_bytes_to_process = input_size - skip
        if total_bytes_to_process > 0:
             scale_progress = (processed_bytes * MAX_SCALE) // total_bytes_to_process
             if scale_progress > dots:
                print("." * (scale_progress - dots), end="")
                sys.stdout.flush()
                dots = scale_progress

    print("]")

    # The final optimal block is the one ending at the last index
    # Ensure we actually have a path
    if input_size > skip:
        if optimal[input_size-1] is None:
            # This can happen if the input is very small or only contains the skipped part.
            # Or if there's a logic error.
            # Fallback: Treat everything as literals from the start block?
            # The C code seems robust against this, maybe due to initialization or implicit paths.
            # Let's check the logic paths again. If only literals are possible,
            # the `last_match[INITIAL_OFFSET]` starts things, and the "No match" case
            # should build a literal path.
            # If `optimal[input_size - 1]` is still None, something is fundamentally wrong.
             print("Warning: No optimal path found. Input might be too small or skipped.", file=sys.stderr)
             # Let's create a simple literal block as a fallback if possible
             if input_size > skip:
                 literal_len = input_size - skip
                 literal_bits = start_block.bits + 1 + elias_gamma_bits(literal_len) + literal_len * 8
                 optimal[input_size-1] = Block(literal_bits, input_size-1, 0, start_block)
             else:
                 return None # No data to compress

        return optimal[input_size-1]
    else:
        return None # Nothing to compress
