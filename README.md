# docker-pipeline [![Circle CI](https://circleci.com/gh/Duke-GCB/docker-pipeline/tree/master.svg?style=svg)](https://circleci.com/gh/Duke-GCB/docker-pipeline/tree/master)
Python tool to run docker containers in sequence, for reproducible computational analysis pipelines.

## Installation

Installing and running via Docker is recommended.

### Docker Image

1. Pull the docker-pipeline image (Optional, `docker run` will automatically pull the image)

        docker pull dukegcb/docker-pipeline

### Local/Development

1. Clone this GitHub repository

        git clone git@github.com:Duke-GCB/docker-pipeline.git

2. Install dependencies with pip

        cd docker-pipeline
        pip install -r requirements.txt

## Write a Pipeline

Pipelines are defined by [YAML](http://yaml.org) files. They specify which Docker images to run, and what files/parameters to provide to containers at runtime them. Each step __must__ specify an image, which can be a name (e.g. `dleehr/filesize`), or an Image ID (`10baa1fc6046`).
If the image accepts environment variables, specify these as `infiles`, `outfiles`, and `parameters`. More on that below

    name: Total Size
    steps:
      -
        name: Get size of file 1
        image: dleehr/filesize
        infiles:
          CONT_INPUT_FILE: /data/raw/file1
        outfiles:
          CONT_OUTPUT_FILE: /data/step1/size
      -
        name: Get size of file 2
        image: dleehr/filesize
        infiles:
          CONT_INPUT_FILE: /data/raw/file2
        outfiles:
          CONT_OUTPUT_FILE: /data/step2/size
      -
        name: Add sizes of files
        image: dleehr/add
        infiles:
          CONT_INPUT_FILE1: /data/step1/size
          CONT_INPUT_FILE2: /data/step2/size
        outfiles:
          CONT_OUTPUT_FILE: /data/step3/total_size

Paths to files should be specified as absolute paths on the Docker host. See [Files and Volumes](#files-and-volumes) for more details.

## Run

### Docker

    docker run \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v /path/to/total_size.yaml:/pipeline.yaml:ro \
      dukegcb/docker-pipeline /pipeline.yaml

Since docker-pipeline creates and starts docker containers, it must have access to `/var/run/docker.sock` on the host. It also must have access to the YAML file, which is mounted as `/pipeline.yaml` in this example.

### Local

    python pipeline.py /path/to/total_size.yaml

## Advanced Usage

docker-pipeline extends YAML with custom tags, allowing simple file name operations and access to variables specified at runtime. This is handy with file names, which make little sense to hard-code in a config file.

For example, file names in the above pipeline can be replaced as such:

      -
        infiles:
          CONT_INPUT_FILE: !var FILE1
      -
        infiles:
          CONT_INPUT_FILE: !var FILE2
      -
        outfiles:
          CONT_OUTPUT_FILE: !var RESULTS

And this pipeline can be run with:

    python pipeline.py total_size.yaml \
      FILE1=/data/raw/file1 \
      FILE2=/data/raw/file2 \
      RESULTS=/data/step3/total_size

The following tags are available, see [tag_handlers.py](tag_handlers.py) for details:

- `!var`: replace a variable specified on the command-line
- `!join`: concatenate multiple values into a single string. Useful for building up file paths
- `!change_ext`: change the extension of a filename
- `!base`: get the base file name (remove parent directories) from a path

Tags can be chained together. See [test_tag_handlers.py](test_tag_handlers.py) for exmaples. In some cases.

Connecting to Docker
--------------------

[pipeline.py](pipeline.py) uses [docker-py](https://github.com/docker/docker-py/) to communicate with Docker. It has been tested with Boot2Docker on OS X, provided `$(boot2docker shellinit)` has been executed. It also works on Docker hosts connecting locally.

Files and Volumes
-----------------

Without explicit access provided at runtime, docker containers cannot access filesystems or paths outside the container. docker-pipeline handles this transparently, allowing you to reference files named in your pipeline, with some added safety features.

First, each container only gets volume access for directories specified within `infiles` and `outfiles`. docker-pipeline will mount only the innermost subdirectory when specifying volume mounts. Keep in mind that the containers do get __root__ access to these directories, so do __NOT__ place your data to analyze in `/` or otherwise sensitive directories.

Second, volumes created for `infiles` are mounted read-only, and volumes for `outfiles` are mounted read-write. This prevents containers from modifying source data for their step. Of course, one step `outfile` may be another container's `infile`. This mechanism allows the file to be written when it's an `outfile`. Ideally, raw data would only ever be passed as an `infile`, so it should be protected.
