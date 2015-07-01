import os

def parse_mount(volume_spec):
  # Docker volumes may be "/src:dest:ro" or simply "/src"
  components = volume_spec.split(':')
  perm = 'w' # assume write perm if not specified
  src_path = components[0]
  # check if ro specified
  if components[-1] == 'ro':
    perm = 'r'
  return (src_path, perm)
