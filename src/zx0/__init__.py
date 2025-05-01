# This file marks the directory as a Python package

# Expose the main compression function for easy importing
from .zx0 import zx0_compress

# Define what gets imported with "from zx0 import *"
__all__ = ['zx0_compress']
