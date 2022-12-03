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


# Parameters
# -----------------------------------------------
# Change these params

PYTHON_CMD="python3.9"
PIP_CMD="pip"


# Argument Parsing
# -----------------------------------------------

VIRTUAL_ENV_LOC=$2
VIRTUAL_ENV_NAME=$1

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
