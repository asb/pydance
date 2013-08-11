# A generic configuration file parser

import os

# master vs user:
# the 'user' hash (~/.foorc) overrides the master hash (/etc/foorc),
# if a value is present in the user hash.

# When writing out, only things *not* equal to the master hash (or only
# in the master hash) are written back out. 

class Config(object):
  # Start a config file, based off a hash - this hash is always a master set
  def __init__(self, data = None):
    self.user = {}
    self.master = {}
    if data != None: self.update(data, True)

  # Update with a dict object, instead of a file.
  def update(self, data, master = False):
    if master: self.master.update(data)
    else: self.user.update(data)
        
  def __getitem__(self, key):
    if key in self.user: return self.user[key]
    else: return self.master.get(key)
  
  def __setitem__(self, key, value, master = False):
    if master: self.master[key] = value
    else: self.user[key] = value

  def __delitem__(self, key):
    if key in self.master: del(self.master[key])
    if key in self.user: del(self.user[key])

  def get(self, key, value = None):
    if key in self.user: return self.user[key]
    else: return self.master.get(key, value)

  # Update the config data with a 'key value' filename.
  # If should_exist is true, raise exceptions if the file doesn't exist.
  # Otherwise, we silently ignore it.
  def load(self, filename, master = False, should_exist = False):
    d = self.user
    if master: d = self.master

    if not os.path.isfile(filename) and not should_exist: return

    fi = file(filename, "r")
    for line in fi:
      line = line.strip()
      if not line or line[0] == '#': pass # comment
      else:
        key = line[0:line.find(' ')]
        val = line[line.find(' ') + 1:].strip()
        # Try to cast the input to a nicer type
        try: d[key] = int(val)
        except ValueError:
          try: d[key] = float(val)
          except ValueError: d[key] = val

    fi.close()

  # Write the filename back out to disk.
  def write(self, filename):
    fi = file(filename, "w")
    keys = self.user.keys()
    keys.sort()
    for key in keys:
      if key not in self.master or self.master[key] != self.user[key]:
        fi.write("%s %s\n" % (key, self.user[key]))
    fi.close()
