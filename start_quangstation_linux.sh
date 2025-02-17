#!/bin/bash

ENV_NAME="quangstation_venv"
ENV_PATH="$PWD/$ENV_NAME"

# Directory that contains this script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Check if the virtual environment exists
if [ -f "$ENV_PATH/bin/activate" ]; then
    echo "$ENV_PATH virtual environment found.";
else
    echo "We couldn't find the activation command for the virtual environment $ENV_PATH. Did you run the install script and are you in the directory where the virtual environment directory $ENV_NAME was created?"
    exit;
fi

# Activate the virtual environment
source $ENV_PATH/bin/activate

# Set PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/core:$SCRIPT_DIR/gui"

# Run main.py
python3 "$SCRIPT_DIR/quangstation_gui/quangstation/gui/main.py"