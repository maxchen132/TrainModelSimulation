#!/bin/bash

set -e # stop on error

echo "[1/3] Running kmltogps.py..."
python3 kmltogps.py

echo "[2/3] Running gpstometers.py..."
python3 gpstometers.py

echo "[3/3] Running meterstomat.py..."
python3 meterstomat.py

echo "All steps completed successfully."
