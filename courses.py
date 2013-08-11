# Course loading is structured differently from step file loading. In
# step files, SongItem is instantiated,creates an instance of a
# specific file class, loads it, and pulls the information it needs
# from it. In Courses, CourseFile is just function that returns an
# object of the appropriate type, which inherits from Course.

# I'm not sure which approach is better.

from constants import *

import random
import util
import error
import records
import os

from i18n import *

# The core course class.
class AbstractCourse(object):
  def __init__(self, all_songs, recordkeys):
    self.songs = []
    self.name = _("A Course")
    self.mixname = " "
    self.banner = None
    self.all_songs = all_songs
    self.recordkeys = recordkeys
    self.past_songs = []

  def __len__(self): return len(self.songs)

  # This course has been started. This means we need to set up some
  # appropriate variables with values we can't get elsewhere.
  def setup(self, screen, player_configs, game_config, gametype):
    self.player_configs = player_configs
    self.game_config = game_config
    self.index = 0
    self.gametype = gametype
    self.screen = screen

  # Done playing this course, GC the above.
  def done(self):
    self.screen = self.player_configs = self.game_config = None


  # Sometimes we have a strange difficulty, like player's worst or a
  # range, or totally random. This checks if the song contains the
  # proper difficulty.
  def _find_difficulty(self, song, diff):
    if self.gametype not in song.difficulty: return False
    # diffs can either be an individual string, representing a
    # difficulty directly, a list of strings, representing possible
    # difficulty names, or a list of integers, which is a range of
    # possible ratings to choose.
    elif isinstance(diff, str):
      if diff in song.difficulty[self.gametype]: return diff
      else: return False
    elif isinstance(diff, list):
      possible = []
      if isinstance(diff[0], int):
        for name, rating in song.difficulty[self.gametype].items():
          if rating in diff: possible.append(name)
      elif isinstance(diff[0], str):
        for name in song.difficulty[self.gametype].keys():
          if name in diff: possible.append(name)
      if len(possible) > 0: return random.choice(possible)
    return False

  def __iter__(self): return self

  def next(self):
    # We're done.
    if self.index == len(self.songs): raise StopIteration
    name, diff, mods = self.songs[self.index]
    fullname = None

    a, b = 0, 0
    if isinstance(diff, list): pass
    elif diff.find("..") != -1: a, b = map(int, diff.split(".."))
    elif len(diff) < 3: a, b = int(diff), int(diff)
    if a or b: diff = range(a, b + 1)

    # Check for player's best/worst/likes/dislikes. There are stored
    # as a tuple of (type, number).
    if name[0] == _("BEST"):
      s = self.recordkeys.get(records.best(name[1], diff, self.gametype), None)
      if s:
        fullname = s.filename
        if isinstance(diff, list):
          diff = [d for d in diff if d in s.difficulty[self.gametype]][0]
    elif name[0] == _("WORST"):
      s = self.recordkeys.get(records.worst(name[1], diff, self.gametype),None)
      if s:
        fullname = s.filename
        if isinstance(diff, list):
          diff = [d for d in diff if d in s.difficulty[self.gametype]][0]
    elif name[0] == _("LIKES"):
      s = self.recordkeys.get(records.like(name[1], diff, self.gametype),None)
      if s:
        fullname = s.filename
        if isinstance(diff, list):
          diff = [d for d in diff if d in s.difficulty[self.gametype]][0]
    elif name[0] == _("DISLIKES"):
      s = self.recordkeys.get(records.dislike(name[1], diff, self.gametype),None)
      if s:
        fullname = s.filename
        if isinstance(diff, list):
          diff = [d for d in diff if d in s.difficulty[self.gametype]][0]
          
    elif name[-1] == "*": # A random song
      # First pull out all the songs that we might be acceptable.
      if "/" in name:
        # Random song from a specific mix.
        folder, dummy = name.split("/")
        folder = folder.lower()
        if folder in self.all_songs:
          songs = [s for s in self.all_songs[folder].values() if (s,diff) not in self.past_songs]
        else:
          error.ErrorMessage(self.screen, folder + _(" was not found."))
          raise StopIteration

      else:
        # Any random song.
        songs = []
        for v in self.all_songs.values(): songs.extend(v.values())

      songs = [s for s in songs if (s,diff) not in self.past_songs and self._find_difficulty(s, diff)]

      if len(songs) == 0:
        error.ErrorMessage(self.screen, _("No valid songs were found."))
        raise StopIteration
      else:
        song = random.choice(songs)
        diff = self._find_difficulty(song, diff)
        fullname = song.filename

    # Let's try to find the damned song.
    # Unfortunately, it can be given as just a title(+subtitle), or a
    # mix with a title. Or a filename. That's why we need the
    # all_songs hash.
    else:
      for path in mainconfig["songdir"].split(os.pathsep):
        fn = os.path.join(path, name)
        fn = os.path.expanduser(fn)
        if os.path.isfile(fn): fullname = fn
        elif os.path.isdir(fn):
          file_list = util.find(fn, ["*.sm", "*.dwi"])
          if len(file_list) != 0: fullname = file_list[0]
        if fullname: break

    if not fullname and len(name[0]) == 1: # Still haven't found it...
      folder, song = name.split("/")
      song = self.all_songs.get(folder.lower(), {}).get(song.lower())
      if song: fullname = song.filename

    if not fullname:
      if len(name[0]) > 1:
        name = _("Player's %s #%d") % (name[0].capitalize(), name[1])
      error.ErrorMessage(self.screen, name + _("was not found."))
      raise StopIteration

    self.index += 1
    self.past_songs.append((fullname,diff))
    return (fullname, [diff] * len(self.player_configs))

def CourseFile(*args):
  if args[0].lower().endswith(".crs"): return CRSFile(*args)
  else: raise RuntimeError(filename + _(" is an unsupported format."))

# Like DWI and SM files, CRS files are a variant of the MSD format.
# This is the DWI variant of .crs. Stepmania's (incompatible) course
# file format is also called .crs.
class CRSFile(AbstractCourse):
  # Map modifier names to internal pydance names.
  modifier_map = { "0.5x" : ("speed", 0.5),
                   "0.75x" : ("speed", 0.75),
                   "1.5x" : ("speed", 1.5),
                   "2.0x" : ("speed", 2.0),
                   "3.0x" : ("speed", 3.0),
                   "4.0x" : ("speed", 4.0),
                   "5.0x" : ("speed", 5.0),
                   "8.0x" : ("speed", 8.0),
                   "boost": ("accel", 1),
                   "break": ("accel", 2),
                   "sudden": ("fade", 1),
                   "hidden": ("fade", 2),
                   "cycle": ("fade", 4),
                   "stealth": ("fade", 5),
                   "mirror": ("transform", 1),
                   "left": ("transform", 2),
                   "right": ("transform", 3),
                   "shuffle": ("transform", -1),
                   "random": ("transform", -2),
                   "little": ("size", 2),
                   "reverse": ("scrollstyle", 1),
                   "noholds": ("holds", 0),
                   "dark": ("dark", 1),
                   }

  def __init__(self, filename, all_songs, recordkeys):
    AbstractCourse.__init__(self, all_songs, recordkeys)
    self.filename = filename
    # I'm not really sure if this is guaranteed or not, but the DDRUK
    # courses match it.
    self.banner = filename[:-3] + "png"
    lines = []
    f = file(filename)
    for line in f:
      if line.find("//") != -1: line = line[:line.find("//")]
      line = line.strip()

      if len(line) == 0: continue
      elif line[0] == "#": lines.append(line[1:]) # A new tag
      else: lines[-1] += line

    for i, line in enumerate(lines):
      while line[-1] == ";": line = line[:-1] # Some lines have two ;s.
      lines[i] = line.split(":")

    if os.path.split(self.filename)[0][-7:] != "courses":
      self.mixname = os.path.split(os.path.split(self.filename)[0])[1]

    for line in lines:
      if line[0] == "COURSE": self.name = ":".join(line[1:])
      elif line[0] == "SONG":
        if len(line) == 3:
          name, diff = line[1:]
          modifiers = []
        elif len(line) == 4:
          name, diff, modifiers = line[1:]
          modifiers = modifiers.split(",")
        else: continue

        if name[0:4] == _("BEST"): name = (_("BEST"), int(name[4:]))
        elif name[0:5] == _("WORST"): name = (_("WORST"), int(name[5:]))
        else: name = name.replace("\\", "/") # DWI uses Windows-style

        # FIXME: This doesn't actually work yet. Modifier application
        # is tricky because we don't have a way to 'reset' the
        # player's objects to the new settings.
        mods = {}
        for mod in modifiers:
          if mod in CRSFile.modifier_map:
            key, value = CRSFile.modifier_map[mod]
            mods[key] = value
        
        self.songs.append((name, diff, mods))

# A course we can easily initialize manually.
class CodedCourse(AbstractCourse):
  def __init__(self, all_songs, recordkeys, title, mix, songs):
    AbstractCourse.__init__(self, all_songs, recordkeys)
    self.name = title
    self.mixname = mix
    self.songs = songs

# And then, initialize some of those courses manually.
def make_players(all_songs, recordkeys):
  courses = []
  for start, end in [(1, 5), (5, 9), (1, 9)]:
    for diff_name, diffs in [(_("(Easy)"), ["BASIC", "LIGHT", "EASY"]),
                             (_("(Normal)"), ["ANOTHER", "STANDARD", "NORMAL",
                                           "TRICK", "MEDIUM"]),
                             (_("(Hard)"), ["MANIAC", "HEAVY", "HARD"]),
                             (_("(Expert)"), ["HARDCORE", "CRAZY", "SMANIAC",
                                           "EXPERT"])]:
      # Player's best, worst, likes, and dislikes
      for name, type in ([_("Best"), _("BEST")],
                         [_("Worst"), _("WORST")],
                         [_("Likes"), _("LIKES")],
                         [_("Dislikes"), _("DISLIKES")]):
        realname = "%s %d-%d %s" % (name, start, end - 1, diff_name)
        songs = [((type, i), diffs, {}) for i in range(start, end)]
        courses.append(CodedCourse(all_songs, recordkeys, realname,
                                   _("Player's Picks"), songs))

  # Random courses.
  for i in [4, 8, 12]:
    for diff_name, diffs in [(_("(Easy)"), ["BASIC", "LIGHT", "EASY"]),
                             (_("(Normal)"), ["ANOTHER", "STANDARD", "NORMAL",
                                           "TRICK", "MEDIUM"]),
                             (_("(Hard)"), ["MANIAC", "HEAVY", "HARD"]),
                             (_("(Expert)"), ["HARDCORE", "CRAZY", "SMANIAC",
                                           "EXPERT"])]:
      randname = _("Random %d %s") % (i, diff_name)
      randsongs = [("*", diffs, {})] * i
      courses.append(CodedCourse(all_songs, recordkeys, randname,
                                 _("random.choose(songs)"), randsongs))

    # ... with random difficulties.
    randname = _("All Random %d") % i
    randsongs = [("*", "0..10", {})] * i
    courses.append(CodedCourse(all_songs, recordkeys, randname,
                               _("random.choose(songs)"), randsongs))

  # I like this course.
  d1 = ["MANIAC", "HEAVY", "HARD"]
  d2 = ["HARDCORE", "CRAZY", "SMANIAC", "EXPERT"]
  songs1 = []
  songs2 = []
  for i in [29, 23, 19, 17, 13, 11, 7, 5, 3, 2]:
    songs1.append(((_("WORST"), i), d1, {}))
    songs2.append(((_("WORST"), i), d2, {}))

  courses.append(CodedCourse(all_songs, recordkeys, _("Primal Fear (Easy)"),
                              _("Player's Picks"), songs1))
  courses.append(CodedCourse(all_songs, recordkeys, _("Primal Fear (Hard)"),
                              _("Player's Picks"), songs2))
  return courses
