@echo off

if not defined CONDA_PREFIX (
     echo No anaconda prompt detected.
     echo Run this script in an anaconda prompt.
     exit /b
)

call conda activate quangstation

set "PYTHONPATH=%~dp0quangstation_core;%~dp0quangstation_gui"

python "%~dp0quangstation_gui\quangstation\gui\main.py"