#!/bin/bash
#
# Simple wrapper script to run docker-pipeline
# First argument should be the absolute path to the YAML file.
# All other arguments will be passed to pipeline.py

if [ -z "$1" ]; then
  echo "Please provide the absolute path to a YAML file"
  exit 1
fi

docker run -v /var/run/docker.sock:/var/run/docker.sock -v $1:/pipeline.yaml:ro dukegcb/docker-pipeline /pipeline.yaml ${*:2}
