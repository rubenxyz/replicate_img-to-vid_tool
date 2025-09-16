#!/bin/bash

# Activate virtual environment and run the verbose main script
source venv/bin/activate
python -m src.main_verbose "$@"