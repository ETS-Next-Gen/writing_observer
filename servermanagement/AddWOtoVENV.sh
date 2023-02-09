#!/usr/bin/env bash
#
# Add AWOtoVENV
# Collin F. Lynch

# This script takes as argument a specified VENV.  It
# then adds the Learning Observer, Writing Observer, and
# the dashboard.  Construction of the VENV can be done
# using the SetupVENV script located in this directory.


# Argument
# --------------------------------------------
# This takes a single argument that should point
# to the directory of the VENV.  You can then
# use this to make any necessary changes.  
VIRTUAL_ENV="$1"
echo "USING VENV: $VIRTUAL_ENV"



# Parameters:
# ---------------------------------------------
# Change these if you need to use a different
# python or pip.  Otherwise leave them as-is. 
PYTHON_CMD="python"
PIP_CMD="pip"

CODE_REPOS_LOC="../../"


# Activate VENV
# ---------------------------------------------------------
source "$VIRTUAL_ENV/bin/activate"


# Installation
# ----------------------------------------------------------

# Install basic requirements.
echo -e "\n=== Installing Requirements.txt ==="
cd ..
"$PIP_CMD" install -r requirements.txt

echo -e "\n=== Installing Learning Observer ==="
cd learning_observer
"$PYTHON_CMD" setup.py develop


echo -e "\n=== Installing Writing Observer ==="
cd ../modules/writing_observer
"$PYTHON_CMD" setup.py develop


echo -e "\n=== Installing Brad's Dashboard ==="
cd ../../learning_observer/prototypes/dash_wo_teacher_dashboard
"$PYTHON_CMD" setup.py develop

