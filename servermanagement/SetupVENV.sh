#!/usr/bin/env bash
#
# SetupVENV.sh
# Collin F. Lynch

# This script performs the basic VENV setup necessary for our LO
# server.  When called it takes as an argument the path for the
# VENV storage and a name.  It then generates the VENV and upgrades
# the local pip install.  It does *not* install the workbench or
# LO code.  That part must be done with separate scripts that
# are located in this folder and in the AWE_Workbench code.


# Argument Parsing
# -----------------------------------------------
# The first argument to the script will specify the name of
# the virtual environment.  Use something simple like WOVenv
VIRTUAL_ENV_NAME=$1

# The second should be a path to your working directory (above the
# repositories) where you will actually run the code.  
VIRTUAL_ENV_LOC=$2


# Parameters
# -----------------------------------------------
# Change these params if you need to shift python
# or pip versions.  Otherwise leave them as-is.

PYTHON_CMD="python3.9"
PIP_CMD="pip"


# Execution
# ---------------------------------------------------------
echo "1) Generating VENV"
"$PYTHON_CMD" -m venv "$VIRTUAL_ENV_LOC/$VIRTUAL_ENV_NAME"

# Initialize
echo "2) Starting $VIRTUAL_ENV_NAME"
source "$VIRTUAL_ENV_LOC/$VIRTUAL_ENV_NAME/bin/activate"

# Update the Pip Version.
echo "3) Updgrading Pip"
"$PIP_CMD" install --upgrade pip
