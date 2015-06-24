from distutils.core import setup

setup(
    name='docker-pipeline',
    version='1.0.0',
    packages=[''],
    package_data={'': ['docker-pipeline-wrapper.sh']},
    include_package_data=True,
    url='https://github.com/Duke-GCB/docker-pipeline',
    license='MIT',
    author='dcl9',
    author_email='dan.leehr@duke.edu',
    description='Run docker containers in sequence, for reproducible computational analysis pipelines '
)
