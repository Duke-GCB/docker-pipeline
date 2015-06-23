import sys
import os
from parse_docker_args import parse_mount

PERMITTED_PATHS = ('/gpfs/fs0/data/',) # Trailing / is important so that /datafiles doesn't match

def check_permitted_path(path):
  # Paths must resolve to something that starts with a PERMITTED_PATH
  resolved = os.path.realpath(path)
  print 'Resolved path to {0}'.format(resolved)
  valid = False
  for permitted in PERMITTED_PATHS:
    if resolved.startswith(permitted): valid = True
  return valid

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "USAGE: {0} <docker volume spec>".format(sys.argv[0])
    print "e.g. {0} /data/somelab:/input:rw".format(sys.argv[0])
    exit(1)
  volume_spec = sys.argv[1]
  path, perm = parse_mount(volume_spec)
  if check_permitted_path(path):
    print "PASS: {0} mount permitted".format(path)
    exit(0)
  else:
    print "ERROR: {0} mount is not permitted".format(path)
    exit(1)
