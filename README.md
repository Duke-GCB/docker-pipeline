# docker-pipeline
Python tool to run docker containers in sequence

Installing
----------

Install dependencies with pip

    pip install -r requirements.txt

Connecting to Docker
--------------------

[pipeline.py](pipeline.py) uses [docker-py](https://github.com/docker/docker-py/) to communicate with Docker. Pipeline assumes your docker host and ssl certificates for connecting are set in your environment, as `$(boot2docker shellinit)` will do, but this should be changed to match your Docker deployment.

Files and Volumes
-----------------

TODO

Usage
-----

    python pipeline.py <yaml file>
    
See [mmap.yaml](mmap.yaml) for examples on structuring a pipeline.
