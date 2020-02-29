import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


requirements = ['pyexcel', 'pyexcel-odsr', 'pyexcel-xls']

setup(
    name = "kicad2charmhigh",
    version = "0.0.1",
    
    # packages=find_packages(),
    # py_modules = ["convert", "Feeder", "FileOperations", "ICTray", "PartPlacement"],
    package_dir={'kicad2charmhigh': '.'},
    packages=['kicad2charmhigh'],
    # package_dir = {'kicad2charmhigh': '.'},
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'kicad2charmhigh=kicad2charmhigh.convert:cli',
        ],
    },

    author = "Vivien Henry",
    # author_email = "vivien.henry@outlook.fr",
    # keywords = "example documentation tutorial",
    # url = "http://packages.python.org/an_example_pypi_project",
    description = ("This takes a KiCad POS file and converts it to a CharmHigh desktop pick and place work file"),
    license = "MIT",
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        # "License :: OSI Approved :: BSD License",
    ],
)
