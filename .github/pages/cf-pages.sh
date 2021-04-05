#!/bin/bash
cd docs
python3.7 -m pip install -U -r requirements.txt
sphinx-build -b html . ../dist