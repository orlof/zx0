#!/usr/bin/env python3

# This is a wrapper script that imports and runs the main function from the zx0 package.
# It allows users to run the tool directly from the command line without having to install it.

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now we can import from the package
from zx0.zx0 import main

if __name__ == "__main__":
    main()
