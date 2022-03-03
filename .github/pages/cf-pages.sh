#!/bin/bash
sudo pkg install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
cd docs
python3.7 -m pip install -U -r requirements.txt
sphinx-build -b html . ../dist
