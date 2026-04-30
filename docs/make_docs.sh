#!/bin/zsh -f

source ../venv/bin/activate
pip install sphinx sphinx_rtd_theme

PROJECTDIR=${0:a:h}/..
export PYTHONPATH="$PROJECTDIR/src:$PROJECTDIR/tests"

echo "Project Folder : $PROJECTFIR" 
echo "PYTHONPATH     : $PYTHONPATH"

make html
deactivate
