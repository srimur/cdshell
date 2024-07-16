#!/bin/bash

# Compile shell.c to create libshell.so
gcc -shared -o libshell.so -fPIC shell.c

# Ensure required Python packages are installed
pip3 install requests tkterm groq

# Run shell_GUI.py using Python 3
python3 shell_GUI.py
