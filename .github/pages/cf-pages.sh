#!/bin/bash
cd docs
apt install portaudio19-dev
python3.7 -m pip install -U -r requirements.txt
sphinx-build -b html . ../dist
