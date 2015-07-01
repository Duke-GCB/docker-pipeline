# docker-pipeline
#
# The MIT License (MIT)
#
# Copyright (c) 2015 Dan Leehr
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from docker.client import Client
from docker.utils import kwargs_from_env


class Runner():
    def __init__(self, pipeline=None):
        self.pipeline = pipeline
        self.client = Runner.get_client()
        self.remove_containers = False
        self.result = None

    @classmethod
    def get_client(cls):
        # Using boot2docker instructions for now
        # http://docker-py.readthedocs.org/en/latest/boot2docker/
        # Workaround for requests.exceptions.SSLError: hostname '192.168.59.103' doesn't match 'boot2docker'
        client = Client(version='auto', **kwargs_from_env(assert_hostname=False))
        return client

    def run(self):
        if self.pipeline.debug:
            print "Running pipeline: {}".format(self)
        for each_step in self.pipeline.steps:
            if self.pipeline.pull_images:
                self.pull_image(each_step)
            container = self.create_container(each_step)
            self.start_container(container, each_step)
            self.result = self.get_result(container, each_step)
            self.finish_container(container, each_step)
            if self.result['code'] != 0:
                # Container exited with nonzero status code
                print "Error: step exited with code {}".format(self.result['code'])
                # Pipeline breaks if nonzero result is encountered
                break
        if self.pipeline.debug:
            print 'Result: {}'.format(self.result)

    def pull_image(self, step):
        if self.pipeline.debug:
            print 'Pulling image for step: {}'.format(step)
        image_result = self.client.pull(step.image)
        if self.pipeline.debug:
            print image_result

    def create_container(self, step):
        if self.pipeline.debug:
            print 'Creating container for step: {}'.format(step)
            print 'Image: {}'.format(step.image)
            print 'Volumes: {}'.format(step.get_volumes())
            print 'Environment: {}'.format(step.environment)
        container = self.client.create_container(step.image,
                                                 command=step.command,
                                                 environment=step.environment,
                                                 volumes=step.get_volumes())
        return container

    def start_container(self, container, step):
        if self.pipeline.debug:
            print 'Running container for step {}'.format(step)
            print 'Binds: {}'.format(step.binds)
        # client.start does not return anything
        self.client.start(container, binds=step.binds)

    def get_result(self, container, step):
        logs = self.client.attach(container, stream=True, logs=True)
        result = {'image': step.image}
        print 'step: {}\nimage: {}\n==============='.format(step.name, step.image)
        all_logs = str()
        for log in logs:
            all_logs = all_logs + log
            print log,
        # Store the return value
        code = self.client.wait(container)
        result['code'] = code
        return result

    def finish_container(self, container, step):
        if self.pipeline.debug:
            print 'Cleaning up container for step {}'.format(step)
        if self.remove_containers:
            self.client.remove_container(container)
