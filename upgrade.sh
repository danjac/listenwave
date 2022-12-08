#!/usr/bin/env bash


# Python dependencies

pip-compile --upgrade --resolver=backtracking -o requirements.txt pyproject.toml
pip-compile --upgrade --resolver=backtracking --extra dev -o dev-requirements.txt pyproject.toml
pip-compile --upgrade --resolver=backtracking --extra ci -o ci-requirements.txt pyproject.toml

pip install -r dev-requirements.txt

# Frontend dependencies

npm run check-updates
npm install

# Pre-commit dependencies

pre-commit autoupdate
