import docker # Not yet used
import os

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
        'CONT_INPUT_BLAST_DB': '/Users/dcl9/Data/go-blastdb'
    }
    step['outfiles'] = {
        'CONT_OUTPUT_BLAST_RESULTS': '/Users/dcl9/Data/output/pipelined-blast.csv'
    }
    pipeline['steps'].append(step)
    return pipeline


def run(pipeline):
    for step in pipeline['steps']:
        create_container(step['image'], step['command'], step['infiles'], step['outfiles'])


# To access files from the host, we must provide volumes
# For security/access limitation, we provide access to the containing directory as the
def make_dirnames_dict(filenames=[]):
    '''
    Creates a dictionary, which maps file names to their containing directories.

    :param filenames: a list of filenames
    :return: dictionary of filenames, mapping to their directory names
    '''
    dirnames = dict(((filename, os.path.dirname(filename)) for filename in filenames))
    return dirnames


def make_volumes_dict(dirnames=set(), prefix='/volume'):
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

def make_binds_dict(volumes_dict, ro=False):
    binds = dict()
    for k, v in volumes_dict.iteritems():
        binds[v] = {'bind': k, 'ro': ro}
    return binds

def translate_to_binds(infiles, outfiles):
    '''
    Create a binds dictionary, suitable for passing to container.start()
    :param infiles: a dictionary of PARAM_NAME: /input_file/path for input files, will be annotated as read-only
    :param outfiles: a dictionary of PARAM_NAME: /output_file/path for output files, will be readwrite
    :return: a dictionary of binds. see http://docker-py.readthedocs.org/en/latest/volumes/
    '''
    infiles_dirnames_dict = make_dirnames_dict(infiles.values())
    infiles_dirnames = set(infiles_dirnames_dict.values())
    infiles_volumes_dict = make_volumes_dict(infiles_dirnames, '/mnt/input')

    outfiles_dirnames_dict = make_dirnames_dict(outfiles.values())
    outfiles_dirnames = set(outfiles_dirnames_dict.values())
    outfiles_volumes_dict = make_volumes_dict(outfiles_dirnames, '/mnt/output')

    input_binds = make_binds_dict(infiles_volumes_dict, ro=True)
    output_binds = make_binds_dict(outfiles_volumes_dict)
    binds = dict(input_binds.items() + output_binds.items())
    return binds


def create_container(image_name=None, command=None, infiles={}, outfiles={}):
    print 'creating container for image {}'.format(image_name)

    ## Translate infile and outfile paths to volumes
    binds = translate_to_binds(infiles, outfiles)
    print binds

    # volumes = infiles_volumes_dict.values()
    # c = docker.Client()
    # c.create_container(image_name, command, volumes=volumes)
    # Start the container


if __name__ == '__main__':
    run(make_prototype_pipeline())