#!/bin/bash

# Activate virtual environment and run the main script
source venv/bin/activate
python -m src.main "$@"