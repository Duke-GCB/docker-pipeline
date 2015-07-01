import os
import sys
from parse_docker_args import parse_mount

def can_access(path, perm):
  mode = None
  if perm == 'r':
    mode = os.R_OK
  elif perm == 'w':
    mode = os.W_OK
  else:
    return False
  return os.access(path, mode)

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "USAGE: {0} <docker volume spec>".format(sys.argv[0])
    print "e.g. {0} /data/somelab:/input:rw".format(sys.argv[0])
    exit(1)
  volume_spec = sys.argv[1]
  path, perm = parse_mount(volume_spec)
  uid = os.getuid()
  if can_access(path, perm):
    print "PASS: UID {0} has {1} access to {2}".format(uid, perm, path)
    exit(0)
  else:
    print "ERROR: UID {0} has no {1} access to {2}".format(uid, perm, path)
    exit(1)
