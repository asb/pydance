#!/usr/bin/env python
# pydance - a dancing game written in Python

import os
import sys
from getopt import getopt

VERSION = "1.1.0"

from i18n import *

# fuck you, Python.
def print_help():
  print
  print _("Usage: %s [options]") % sys.argv[0]
  print _(" -h, --help         display this help text and exit")
  print _(" -v, --version      display the version and exit")
  print _(" -f, --filename     load and play a step file")
  print _(" -m, --mode         the mode to play the file in (default SINGLE)")
  print _(" -d, --difficulty   the difficult to play the file (default BASIC)")
  raise SystemExit

def print_version():
  print _("pydance %s by Joe Wreschnig, Brendan Becker, and others") % VERSION
  print "pyddr-discuss@icculus.org - http://icculus.org/pyddr"
  raise SystemExit

if len(sys.argv) < 2: pass 
elif sys.argv[1] in ["--help", "-h"]: print_help()
elif sys.argv[1] in ["--version", "-v"]: print_version()

# Don't import anything that initializes the joysticks or config until
# after we're (reasonably) sure no one wants --help or --version.
from constants import * # This needs to be here to set sys.path.

import util
import games
import dance
import pygame
import courses
import colors
import records
import menudriver

from fileparsers import SongItem
from pygame.mixer import music
from fontfx import TextProgress
from error import ErrorMessage
from fonttheme import FontTheme

from pad import pad

# Set our required display paramters. Currently, this is nothing
# strange on any platforms, but in the past and likely in the future
# some platforms need other flags.
def set_display_mode():
  try:
    flags = 0
    if mainconfig["fullscreen"]: flags |= FULLSCREEN
    screen = pygame.display.set_mode([640, 480], flags, 16)
  except:
    raise SystemExit(_("E: Can't get a 16 bit display! pydance doesn't work in 8 bit mode."))
  return screen

# Load a single song (given the filename) and then play it on the
# given difficulty.
def play_and_quit(fn, mode, difficulty):
  print _("Entering debug (play-and-quit) mode.")
  screen = set_display_mode()  
  pygame.display.set_caption("pydance " + VERSION)
  pygame.mouse.set_visible(0)
  pc = games.GAMES[mode].players
  dance.play(screen, [(fn, [difficulty] * pc)],
             [player_config] * pc, game_config, mode)
  raise SystemExit

# Pass a list of files to a constructor (Ctr) that takes the filename
# as the first argument, and the args tuple as the rest.
def load_files(screen, files, type, Ctr, args):
  if len(files) == 0: return []

  screen.fill(colors.BLACK)
  pct = 0
  inc = 100.0 / len(files)
  # Remove duplicates
  files = list(dict(map(None, files, [])).keys())
  objects = []
  message = _("Found %d %s. Loading...") % (len(files), _(type))
  pbar = TextProgress(FontTheme.loading_screen, message, colors.WHITE, colors.BLACK)
  r = pbar.render(0).get_rect()
  r.center = [320, 240]
  for f in files:
    try: objects.append(Ctr(*((f,) + args)))
    except RuntimeError, message:
      print _("E:"), f
      print _("E:"), message
      print
    except Exception, message:
      print _("E: Unknown error loading"), f
      print _("E:"), message
      print _("E: Please contact the developers (pyddr-devel@icculus.org).")
      print
    pct += inc
    img = pbar.render(pct)
    pygame.display.update(screen.blit(img, r))

  return objects

# Support fullscreen on Win32 / OS X?
if osname != "posix": pygame.display.toggle_fullscreen = set_display_mode
else: pass

# Actually start the program running.
def main():
  print "pydance", VERSION, "<pyddr-discuss@icculus.org> - irc.freenode.net/#pyddr"

  if mainconfig["usepsyco"]:
    try:
      import psyco
      print _("Psyco optimizing compiler found. Using psyco.full().")
      psyco.full()
    except ImportError: print _("W: Psyco optimizing compiler not found.")

  # default settings for play_and_quit.
  mode = "SINGLE"
  difficulty = "BASIC"
  test_file = None
  for opt, arg in getopt(sys.argv[1:],
                         "hvf:d:m:", ["help", "version", "filename=",
                                      "difficulty=", "mode="])[0]:
    if opt in ["-h", _("--help")]: print_help()
    elif opt in ["-v", _("--version")]: print_version()
    elif opt in ["-f", _("--filename")]: test_file = arg
    elif opt in ["-m", _("--mode")]: mode = arg
    elif opt in ["-d", _("--difficulty")]: difficulty = arg

  if test_file: play_and_quit(test_file, mode, difficulty)

  song_list = []
  course_list = []
  for dir in mainconfig["songdir"].split(os.pathsep):
    print _("Searching for songs in"), dir
    song_list.extend(util.find(dir, ['*.dance', '*.dwi', '*.sm', '*/song.*']))
  for dir in mainconfig["coursedir"].split(os.pathsep):
    print _("Searching for courses in"), dir
    course_list.extend(util.find(dir, ['*.crs']))

  screen = set_display_mode()
  
  pygame.display.set_caption("pydance " + VERSION)
  pygame.mouse.set_visible(False)
  try:
    if os.path.exists("/usr/share/pixmaps/pydance.png"):
      icon = pygame.image.load("/usr/share/pixmaps/pydance.png")
    else: icon = pygame.image.load(os.path.join(pydance_path, "icon.png"))
    pygame.display.set_icon(icon)
  except: pass

  music.load(os.path.join(sound_path, "menu.ogg"))
  music.play(4, 0.0)

  songs = load_files(screen, song_list, _("songs"), SongItem, (False,))

  # Construct the song and record dictionaries for courses. These are
  # necessary because courses identify songs by title and mix, rather
  # than filename. The recordkey dictionary is needed for player's
  # picks courses.
  song_dict = {}
  record_dict = {}
  for song in songs:
    mix = song.info["mix"].lower()
    title = song.info["title"].lower()
    if song.info["subtitle"]: title += " " + song.info["subtitle"].lower()
    if not song_dict.has_key(mix): song_dict[mix] = {}
    song_dict[mix][title] = song
    record_dict[song.info["recordkey"]] = song

  crs = load_files(screen, course_list, _("courses"), courses.CourseFile,
                   (song_dict, record_dict))
  crs.extend(courses.make_players(song_dict, record_dict))
  records.verify(record_dict)

  # Let the GC clean these up if it needs to.
  song_list = None
  course_list = None
  record_dict = None
  pad.empty()

  if len(songs) < 1:
    ErrorMessage(screen,
                 (_("You don't have any songs or step files. Check out "
                  "http://icculus.org/pyddr/get.php#songs "
                  "and download some free ones. "
                  "If you already have some, make sure they're in ")) +
                 mainconfig["songdir"])
    raise SystemExit(_("You don't have any songs. Check http://icculus.org/pyddr/get.php#songs ."))

  menudriver.do(screen, (songs, crs, screen))

  # Clean up shit.
  music.stop()
  pygame.quit()
  mainconfig.write(os.path.join(rc_path, "pydance.cfg"))
  # FIXME -- is this option a good idea?
  if mainconfig["saveinput"]: pad.write(os.path.join(rc_path, "input.cfg"))
  records.write()

if __name__ == '__main__': main()
