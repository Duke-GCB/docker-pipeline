#!/bin/bash

# docker-pipeline-wrapper.sh <pipeline yaml file> <args>

# Must be run as sudo

if [ -z "$SUDO_UID" ]; then
  echo "Error: Must be run with sudo"
  exit 1
fi

# Get the directory of this script, for paths to python files
DIR="$(dirname "$(readlink -f "$0")")"

# Specify exact python location - uses 2.7 and doesn't rely on path
PYTHON_BIN=$(which python2.7)

ACCESS=$(sudo -u "#$SUDO_UID" "$PYTHON_BIN" "$DIR/docker-pipeline/check_pipeline_volumes.py" $@)
if [ $? -ne 0 ]; then
  echo $ACCESS
  exit 1
fi

# Run the docker-pipeline docker image

docker run -i -v /var/run/docker.sock:/var/run/docker.sock -v $1:/pipeline.yaml:ro dukegcb/docker-pipeline /pipeline.yaml ${*:2}