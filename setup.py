# setup.py
import setuptools
from setuptools import find_packages
import os

# Function to read the README file.
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    try:
        with open(readme_path, encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Python port of ZX0 compressor by Einar Saukas." # Fallback description

setuptools.setup(
    name="zx0",
    version="2.2.0",
    author="Orlof, Einar Saukas (Original C Author)",
    author_email='orlof@users.noreply.github.com',
    description="Python port of ZX0 v2.2 optimal data compressor",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/orlof/zx0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={
        'console_scripts': [
            'zx0 = zx0.zx0:main', # Creates 'zx0' command running the main() function in zx0/zx0.py
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: System :: Archiving :: Compression",
    ],
    python_requires='>=3.6',
    license="BSD 3-Clause",
)
