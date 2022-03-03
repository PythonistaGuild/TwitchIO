#!/bin/bash
cd docs
python3.7 -m pip install -U -r requirements.txt
python3.7 -m pip install -U -r docs/requirements.txt
sphinx-build -b html . ../dist
