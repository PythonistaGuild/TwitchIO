#!/bin/bash
cd docs
pip install conda
conda install pyaudio
python3.7 -m pip install -U -r requirements.txt
sphinx-build -b html . ../dist
echo ""