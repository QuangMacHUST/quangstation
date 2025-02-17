@echo off

if not defined CONDA_PREFIX (
     echo No anaconda prompt detected.
     echo Run this script in an anaconda prompt.
     exit /b
)

call conda activate quangstation

set "PYTHONPATH=%~dp0core;%~dp0gui"

python "%~dp0quangstation_gui\quangstation\gui\main.py"