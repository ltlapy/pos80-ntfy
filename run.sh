#!/bin/bash

source ./venv/bin/activate

export $(grep -v '^#' .env | xargs)
./stream_ntfy.py

# unset environments
# https://stackoverflow.com/a/20909045
unset $(grep -v '^#' .env | sed -E 's/(.*)=.*/\1/' | xargs)
