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

from collections import defaultdict
from check_path_access import can_access
import os
import yaml


class Pipeline():
    def __init__(self, name, host=None, steps=[], debug=False, pull_images=True):
        if name is None:
            raise TypeError('Must provide a name for the pipeline')
        self.name = name
        self.host = host
        self.steps = steps
        self.debug = debug
        self.pull_images = pull_images

    def __unicode__(self):
        return u'<Pipeline: {} - steps: {} host: {}, debug: {} >'.format(self.name, len(self.steps), self.host, self.debug)

    def __str__(self):
        return unicode(self).encode('utf-8')

    @classmethod
    def from_dict(cls, pipeline_dict):
        pipeline_dict = defaultdict(lambda: None, pipeline_dict)
        step_dicts = pipeline_dict['steps']
        steps = list()
        for step_dict in step_dicts:
            step = Step.from_dict(step_dict)
            steps.append(step)
        name = pipeline_dict['name']
        host = pipeline_dict['host']
        debug = pipeline_dict['debug'] or False
        pull_images = pipeline_dict['pull_images'] or False
        return cls(name, host=host, steps=steps, debug=debug, pull_images=pull_images)

    @classmethod
    def from_yaml(cls, file):
        with open(file, 'r') as yamlfile:
            pipeline_dict = yaml.load(yamlfile)
        return cls.from_dict(pipeline_dict)

    def check_volumes(self):
        # Confirm access to directories
        for step in self.steps:
            step.check_volumes()


class Step():
    def __init__(self, name, image, command=None, parameters=None, infiles={}, outfiles={}):
        if image is None:
            raise TypeError('Must provide an image name for the step')
        if name is None:
            raise TypeError('Must provide a name for the pipeline')
        self.name = name
        self.image = image
        self.command = command
        self.infiles = infiles
        self.outfiles = outfiles

        # Inputs are mounted read-only
        self.infiles_dirnames_dict = Step.make_dirnames_dict(self.infiles.values())
        infiles_dirnames = set(self.infiles_dirnames_dict.values())
        self.infiles_volumes_dict = Step.make_volumes_dict(infiles_dirnames, '/mnt/input')

        # Outputs will be mounted read-write
        self.outfiles_dirnames_dict = Step.make_dirnames_dict(self.outfiles.values())
        outfiles_dirnames = set(self.outfiles_dirnames_dict.values())
        self.outfiles_volumes_dict = Step.make_volumes_dict(outfiles_dirnames, '/mnt/output')

        self.binds = self.generate_binds()

        # Structures for environment are simplified by having input and output together
        self.allfiles = dict(infiles.items() + outfiles.items())
        self.dirnames_dict = dict(self.infiles_dirnames_dict.items() + self.outfiles_dirnames_dict.items())
        self.volumes_dict = dict(self.infiles_volumes_dict.items() + self.outfiles_volumes_dict.items())

        # Environment variables passed to container execution must reference file paths from within the container
        # Also pass along parameters as environment variables
        self.environment = self.generate_file_parameters()
        if parameters is not None:
            self.environment = dict(self.environment.items() + parameters.items())

    def __unicode__(self):
        return u'<Step: {} - Image: {}, Command: {}, {}i,{}o>'.format(self.name, self.image, self.command, len(self.infiles), len(self.outfiles))

    def __str__(self):
        return unicode(self).encode('utf-8')

    @classmethod
    def from_dict(cls, step_dict):
        step_dict = defaultdict(lambda: None, step_dict)
        step = cls(name=step_dict['name'],
                   image=step_dict['image'],
                   command=step_dict['command'],
                   parameters=step_dict['parameters'],
                   infiles=step_dict['infiles'],
                   outfiles=step_dict['outfiles'])
        return step

    @classmethod
    def from_yaml(cls, file):
        step_dict = None
        with open(file, 'r') as yamlfile:
            step_dict = yaml.load(yamlfile)
        return cls.from_dict(step_dict)

    def get_volumes(self):
        return sorted(self.volumes_dict.keys())

    @classmethod
    def make_dirnames_dict(cls, filenames=[]):
        '''
        Creates a dictionary, which maps file names to their containing directories.

        :param filenames: a list of filenames
        :return: dictionary of filenames, mapping to their directory names
        '''
        dirnames = dict(((filename, os.path.dirname(filename)) for filename in filenames))
        return dirnames

    @classmethod
    def make_volumes_dict(cls, dirnames=set(), prefix='/volume'):
        '''
        Creates a dictionary, mapping directory names to a flat volume listing, using the provided prefix

        :param prefix: A string to prefix the volume name, e.g. '/input' or '/output'
        :param dirnames: Set of unique directory names.
        :return: A dictionary, mapping a directory name to a volume name (e.g. {'/path/to/directory' : '/input_01' }
        '''
        volumes_dict = dict()
        for i, dirname in enumerate(sorted(dirnames)):
            key = '{}_{}'.format(prefix, i)
            volumes_dict[key] = dirname
        return volumes_dict

    @classmethod
    def make_binds_dict(cls, volumes_dict, ro=False):
        binds = dict()
        for k, v in volumes_dict.iteritems():
            binds[v] = {'bind': k, 'ro': ro}
        return binds

    def generate_binds(self):
        '''
        Create a binds dictionary, suitable for passing to container.start()
        :param infiles: a dictionary of PARAM_NAME: /input_file/path for input files, will be annotated as read-only
        :param outfiles: a dictionary of PARAM_NAME: /output_file/path for output files, will be readwrite
        :return: a dictionary of binds. see http://docker-py.readthedocs.org/en/latest/volumes/
        '''

        input_binds = Step.make_binds_dict(self.infiles_volumes_dict, ro=True)
        output_binds = Step.make_binds_dict(self.outfiles_volumes_dict)
        binds = dict(input_binds.items() + output_binds.items())
        return binds

    def translate_local_to_remote(self, local_path):
        '''
        Translates a local file path to its path inside the container
        :param local_path: path to local file
        :param volumes_dict: mapping of remote mount points to local directories
        :param dirnames_dict: mapping of filenames to their dirnames
        :return:
        '''

        dirname = self.dirnames_dict[local_path]
        filename = os.path.basename(local_path)
        remote_path = None
        for remote, local in self.volumes_dict.iteritems():
            if local == dirname:
                remote_path = '{}/{}'.format(remote, filename)
                break
        return remote_path

    def generate_file_parameters(self):
        environment = dict()
        # Input: 'CONT_INPUT_BLAST_DB': '/Users/dcl9/Data/go-blastdb'
        # Output: 'CONT_INPUT_BLAST_DB': '/mnt/input_0/go-blastdb'
        for label, filename in self.allfiles.iteritems():
            environment[label] = self.translate_local_to_remote(filename)
        return environment

    def check_volumes(self):
        print 'checking volumes for {}'.format(self)
        for path, bind_args in self.binds.items():
            if bind_args['ro']:
                perm = 'r'
            else:
                perm = 'w'
            access = can_access(path, perm)
            if not access:
                message = 'ERROR: No {0} access to {1}'.format(perm, path)
                raise Exception(message)

