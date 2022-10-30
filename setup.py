from distutils.core import setup
from Cython.Build import cythonize

setup(ext_modules = cythonize('cfuncts.pyx'))

#Instructions on how to set up cython code in python
#https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html
