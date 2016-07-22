#!/usr/bin/env bash -ev

mkvirtualenv open-source-init
workon open-source-init

pip install -e .
pip install -r requirements_dev.txt
