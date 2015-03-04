from docker.client import Client
from docker.utils import kwargs_from_env
from collections import defaultdict
import os
import yaml


class Pipeline():
    def __init__(self, host=None, steps=[], debug=False):
        self.host = host
        self.steps = steps
        self.debug = debug
        self.client = Pipeline.get_client()
        self.remove_containers = False
        self.result = None

    def __unicode__(self):
        return u'<Pipeline - steps: {} host: {}, debug: {} >'.format(len(self.steps), self.host, self.debug)

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
        host = pipeline_dict['host']
        return cls(host=host, steps=steps, debug=True)

    @classmethod
    def from_yaml(cls, file):
        with open(file, 'r') as yamlfile:
            pipeline_dict = yaml.load(yamlfile)
        return cls.from_dict(pipeline_dict)

    @classmethod
    def get_client(cls):
        # Using boot2docker instructions for now
        # http://docker-py.readthedocs.org/en/latest/boot2docker/
        # Workaround for requests.exceptions.SSLError: hostname '192.168.59.103' doesn't match 'boot2docker'
        client = Client(**kwargs_from_env(assert_hostname=False))
        return client

    def run(self):
        for each_step in self.steps:
            container = self.create_container(each_step)
            self.start_container(container, each_step)
            self.result = self.get_result(container, each_step)
            self.finish_container(container)
            if self.result['code'] != 0:
                # Container exited with nonzero status code
                print "Error: step exited with code {}".format(self.result['code'])
                # Pipeline breaks if nonzero result is encountered
                break
        if self.debug:
            print 'Result: {}'.format(self.result)

    def create_container(self, step):
        if self.debug:
            print 'Creating container for step: {}'.format(self)
            print 'Image: {}'.format(step.image)
            print 'Volumes: {}'.format(step.get_volumes())
            print 'Environment: {}'.format(step.environment)
        container = self.client.create_container(step.image,
                                                 command=step.command,
                                                 environment=step.environment,
                                                 volumes=step.get_volumes())
        return container

    def start_container(self, container, step):
        if self.debug:
            print 'Running container for step {}'.format(self)
            print 'Binds: {}'.format(step.binds)
        # client.start does not return anything
        self.client.start(container, binds=step.binds)

    def get_result(self, container, step):
        logs = self.client.attach(container, stream=True, logs=True)
        result = {'image': step.image}
        all_logs = str()
        for log in logs:
            all_logs = all_logs + log
            if self.debug:
                print log
        # Store the return value
        code = self.client.wait(container)
        result['code'] = code
        return result

    def finish_container(self, container):
        if self.debug:
            print 'Cleaning up container for step {}'.format(self)
        if self.remove_containers:
            self.client.remove_container(container)


class Step():
    def __init__(self, image, command=None, parameters=None, infiles={}, outfiles={}):
        if image is None:
            raise TypeError('Must provide an image name for the step')
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
        return u'<Step - Image: {}, Command: {}, {} in {} out>'.format(self.image, self.command, len(self.infiles), len(self.outfiles))

    def __str__(self):
        return unicode(self).encode('utf-8')

    @classmethod
    def from_dict(cls, step_dict):
        step_dict = defaultdict(lambda: None, step_dict)
        step = cls(image=step_dict['image'],
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


def main(yaml_file):
    p = Pipeline.from_yaml(yaml_file)
    p.run()

if __name__ == '__main__':
    main('mmap.yaml')
