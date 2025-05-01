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

# zx0_common.py

# Constants from zx0.h and zx0.c
INITIAL_OFFSET = 1
MAX_OFFSET_ZX0 = 32640
MAX_OFFSET_ZX7 = 2176 # For quick mode
MAX_SCALE = 50 # From optimize.c for progress reporting

class Block:
    """Represents a block in the optimal compression path."""
    def __init__(self, bits: int, index: int, offset: int, chain: 'Block' or None):
        self.bits: int = bits          # Cost in bits to reach this block
        self.index: int = index        # Input data index where this block ends
        self.offset: int = offset      # Offset for copy operations (0 for literals)
        self.chain: Block or None = chain # Previous block in the optimal path
        # NOTE: ghost_chain and references were part of C custom memory management,
        # which is not needed with Python's garbage collection.

    def __repr__(self) -> str:
        chain_idx = self.chain.index if self.chain else -1
        return f"Block(idx={self.index}, off={self.offset}, bits={self.bits}, chain_idx={chain_idx})"

def elias_gamma_bits(value: int) -> int:
    """Calculate the number of bits for an Elias Gamma code."""
    if value <= 0:
        raise ValueError("Elias Gamma codes are for positive integers.")
    bits = 1
    value_copy = value
    while value_copy > 1:
        value_copy >>= 1
        bits += 2
    return bits

def offset_ceiling(index: int, offset_limit: int) -> int:
    """Calculate the maximum allowed offset."""
    # Original C logic: return index > offset_limit ? offset_limit : index < INITIAL_OFFSET ? INITIAL_OFFSET : index;
    # Simplified: The offset cannot be more than the limit, nor more than the current index. It must be at least INITIAL_OFFSET.
    limit = min(index, offset_limit)
    return max(INITIAL_OFFSET, limit)

# --- Helper for compress ---
# We need a way to manage bit writing state. A class is suitable.
class BitStreamWriter:
    def __init__(self, backwards_mode: bool, invert_mode: bool):
        self.output_data = bytearray()
        self.bit_mask = 0
        self.bit_index = -1 # Index in output_data for the current byte being built
        self.backtrack = True # Special state for first bit after offset LSB
        self.diff = 0 # Tracks output_size - input_size, updated during compression
        self.backwards_mode = backwards_mode
        self.invert_mode = invert_mode

    def write_byte(self, value: int):
        self.output_data.append(value & 0xFF)
        self.diff -= 1

    def write_bit(self, value: int):
        if self.backtrack:
            if value:
                # Modify the LSB of the *last* fully written byte
                # This assumes the last operation was writing the offset LSB byte
                if not self.output_data:
                     raise IndexError("Cannot backtrack bit on empty output")
                self.output_data[-1] |= 1
            self.backtrack = False
        else:
            if self.bit_mask == 0:
                self.bit_mask = 128
                self.bit_index = len(self.output_data)
                self.write_byte(0) # Allocate space for the new bitmask byte

            if value:
                if self.bit_index < 0 or self.bit_index >= len(self.output_data):
                    raise IndexError(f"Bit index {self.bit_index} out of bounds for output data size {len(self.output_data)}")
                self.output_data[self.bit_index] |= self.bit_mask

            self.bit_mask >>= 1

    def write_interlaced_elias_gamma(self, value: int):
        if value <= 0:
             raise ValueError("Elias Gamma codes are for positive integers.")
        i = 2
        while i <= value:
            i <<= 1
        i >>= 1

        while True:
            i >>= 1
            if i == 0: break
            self.write_bit(self.backwards_mode)
            bit = (value & i) != 0
            self.write_bit(not bit if self.invert_mode else bit)

        self.write_bit(not self.backwards_mode)
