FROM phusion/baseimage
MAINTAINER Dan Leehr <dan.leehr@duke.edu>

RUN apt-get update && apt-get install -y \
  python \
  python-dev \
  libffi-dev \
  libssl-dev \
  python-pip

COPY . /docker-pipeline
WORKDIR /docker-pipeline
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "pipeline.py"]
CMD ["-h"]
