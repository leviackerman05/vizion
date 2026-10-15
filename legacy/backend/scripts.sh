#!/bin/bash

i() {
  pip install "$1"
  pip freeze > requirements.txt
}

venv() {
  source ./venv/bin/activate
}

format() {
  black .
  isort .
  flake8 .
}
