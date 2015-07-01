#!/bin/bash

# docker-pipeline-wrapper.sh <pipeline yaml file> <args>

# Must be run as sudo

# Must be root via sudo
if [ "$(whoami)" != "root" ] || [ -z "$SUDO_UID" ]; then
  echo "Error: Must be run with sudo"
  exit 1
fi

# Specify exact python location - uses 2.7 and doesn't rely on path
PYTHON_BIN="/usr/local/bin/python"
SITE_PACKAGES=$($PYTHON_BIN -c "import site;print site.getsitepackages()[0]")

ACCESS=$(sudo -u "#$SUDO_UID" "$PYTHON_BIN" "$SITE_PACKAGES/docker-pipeline/check_pipeline_volumes.py" $@)
if [ $? -ne 0 ]; then
  echo $ACCESS
  exit 1
fi

# Run the docker-pipeline docker image

docker run -i -v /var/run/docker.sock:/var/run/docker.sock -v $1:/pipeline.yaml:ro dukegcb/docker-pipeline /pipeline.yaml ${*:2}
