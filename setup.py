#!/usr/bin/env python
# Set up the appropriate pydance installation makefiles.

import os, sys

# Check for the presence of appropriate Python and Pygame versions.
def sanity_check():
  print "Checking for appropriate libraries."
  print "Checking Python version... ",
  print sys.version[:5] + "."
  if sys.version_info < (2, 4):
    print "Versions of Python less than 2.4 are not supported by pydance."
    print "Visit http://www.python.org to upgrade."
    sys.exit(1)

  try:
    print "Checking for Pygame... ",
    import pygame
    print pygame.version.ver + "."
    if pygame.version.vernum < (1, 8):
      print "You have pygame, but a version less than 1.8."
      print "Visit http://www.pygame.org to upgrade."
      sys.exit(1)
  except ImportError:
    print "You don't seem to have pygame installed."
    print "Visit http://www.pygame.org to install it."

def detect_real_os():
  print "Detecting your operating system... ",
  if os.name == "nt":
    print "Windows."
    return "win32"
  elif os.name == "posix":
    print "POSIX -",
    if os.path.islink("/System/Library/CoreServices/WindowServer"):
      print "MacOS X."
      return "macosx"
    elif os.environ.has_key("HOME") and os.path.isdir("/etc"):
      print "UNIX-like."
      return "posix"
    else:
      print "Unknown!"
      print "I'm all confused as to your OS. pydance will run pretending that you're"
      print "UNIX, but you'll have to force this setup step if you really want to."
      sys.exit(1)
  else:
    print "Unknown"
    print "Your platform isn't supported with this install system (yet)."
    sys.exit(1)

sanity_check()
osname = detect_real_os()

print

if os.path.isfile("pydance." + osname + ".cfg"):
  fin = open("pydance." + osname + ".cfg")
  fout = open("pydance.cfg", "w")
  for line in fin: fout.write(line)
  fout.close()
  fin.close()

if os.path.isfile("Makefile." + osname):
  fin = open("Makefile." + osname)
  fout = open("Makefile", "w")
  for line in fin: fout.write(line)
  fout.close()
  fin.close()  

if osname == "win32":
  print "Configuration for Win32 systems complete. No installation is needed."
  print "Make sure your pydance.cfg file points to your song directory."
elif osname == "macosx":
  print "You're on your own, for now."
elif osname == "posix":
  print "Configuration for UNIX-like systems complete. 'make install' should"
  print "properly install pydance, by default into /usr/local. You can override"
  print "this by setting $PREFIX. You can also set $DESTDIR, which will be"
  print "prepended to all installation paths."
