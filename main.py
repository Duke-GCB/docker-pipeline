from docker.client import Client
from docker.utils import kwargs_from_env
import os
import sys


def make_prototype_pipeline():
    '''
    A sample pipeline with one step
    :return: dictionary constituting a pipeline
    '''
    pipeline = dict()
    pipeline['host'] = ''
    pipeline['steps'] = list()
    step = dict()
    step['image'] = 'dleehr/go-blast'
    step['command'] = None
    step['infiles'] = {
        'CONT_INPUT_ORFS_FILE': '/Users/dcl9/Data/mmap/example/MMAP_example.glimmer',
        'CONT_INPUT_BLAST_DB': '/Users/dcl9/Data/go-blastdb/go-seqdb'
    }
    step['outfiles'] = {
        'CONT_OUTPUT_BLAST_RESULTS': '/Users/dcl9/Data/output/pipelined-blast.csv'
    }
    pipeline['steps'].append(step)
    return pipeline


class Pipeline():
    def __init__(self, host=None, steps=[], debug=False):
        self.host = host
        self.steps = steps
        self.debug = debug
        self.client = Pipeline.get_client()

    @classmethod
    def get_client(cls):
        # Using boot2docker instructions for now
        # http://docker-py.readthedocs.org/en/latest/boot2docker/
        # Workaround for requests.exceptions.SSLError: hostname '192.168.59.103' doesn't match 'boot2docker'
        client = Client(**kwargs_from_env(assert_hostname=False))
        return client

    def run(self):
        self.results = list()
        for each_step in self.steps:
            container = self.create_container(each_step)
            self.start_container(container, step)
            self.save_results(container, step)
            self.remove_container(container)
        if self.debug:
            print self.results

    def create_container(self, step):
        if self.debug:
            print 'Creating container for step'
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
            print 'Running container for step'
            print 'Binds: {}'.format(step.binds)
        # client.start does not return anything
        self.client.start(container, binds=step.binds)

    def save_results(self, container, step):
        # Get events?
        # Get logs
        logs = self.client.logs(container)
        self.results.append({'image': step.image, 'logs': logs})

    def remove_container(self, container):
        self.client.wait(container)
        self.client.remove_container(container)
class Step():
    def __init__(self, image, command=None, infiles={}, outfiles={}):
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

        self.environment = self.generate_environment()

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

    def generate_environment(self):
        environment = dict()
        # Input: 'CONT_INPUT_BLAST_DB': '/Users/dcl9/Data/go-blastdb'
        # Output: 'CONT_INPUT_BLAST_DB': '/mnt/input_0/go-blastdb'
        for label, filename in self.allfiles.iteritems():
            environment[label] = self.translate_local_to_remote(filename)

        # Need a mapping of local file to volume file
        return environment


if __name__ == '__main__':
    pipeline_dict = make_prototype_pipeline()
    step_dicts = pipeline_dict['steps']
    steps = list()
    for step_dict in step_dicts:
        # self, image, command=None, infiles={}, outfiles={}):
        step = Step(image=step_dict['image'], command=step_dict['command'], infiles=step_dict['infiles'],
                    outfiles=step_dict['outfiles'])
        steps.append(step)

    pipeline = Pipeline(None, steps=steps, debug=True)
    pipeline.run()