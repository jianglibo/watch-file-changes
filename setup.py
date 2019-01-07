import os
from pathlib import Path

from cx_Freeze import Executable, setup

# python setup.py bdist_msi

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
print(PYTHON_INSTALL_DIR)
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

print(os.environ['TCL_LIBRARY'])
# sys.exit(0)
here: Path = Path(__file__).parent
run_py: Path = here.joinpath('run.py')
run_py = run_py.resolve()
# Dependencies are automatically detected, but it might need
# fine tuning.

include_files = [str(here.joinpath(s).resolve())
                 for s in ["config", "instance"]]
print(include_files)
buildOptions = dict(packages=['jinja2', 'jinja2.ext'],
                    excludes=[], include_files=include_files)
print(str(run_py))
base = 'Console'

executables = [
    Executable(str(run_py),
               base=base,
               targetName='watch-file-changes.exe')
]

setup(name='watch-file-changes',
      version='1.0',
      description='to watch and record changed files.',
      options=dict(build_exe=buildOptions),
      executables=executables)
