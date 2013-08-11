import fnmatch
import os
import string

from i18n import *

# This is the standard order to present difficulties in.
# DDR (USA home version) calls "beginner" "standard". Ignore that.
# Beginner, light, basic, another, standard, trick, maniac, heavy, challenge,
# and oni are from DDR. Smaniac is from DWI; s-maniac is a very common typo.
# Hardcore is from pydance. Para and expert are from PPP. Easy, and hard are
# from TM and PIU; medium is from TM; crazy is from PIU.

#We need a dummy difficulty list to include it to .pot file
DIFFICULTY_LIST_I18N = [_("BEGINNER"),_("EASY"),_("LIGHT"),_("BASIC"),_("PARA"),
                   _("ANOTHER"),_("NORMAL"),_("MEDIUM"),_("STANDARD"),
                   _("TRICK"),_("DOUBLE"),_("HARD"),_("MANIAC"),_("HEAVY"),
                   _("HARDCORE"),_("CHALLENGE"),_("ONI"),_("SMANIAC"),
                   _("S-MANIAC"),_("CRAZY"),_("EXPERT")]


DIFFICULTY_LIST = ["BEGINNER","EASY","LIGHT","BASIC","PARA",
                   "ANOTHER","NORMAL","MEDIUM","STANDARD",
                   "TRICK","DOUBLE","HARD","MANIAC","HEAVY",
                   "HARDCORE","CHALLENGE","ONI","SMANIAC",
                   "S-MANIAC","CRAZY","EXPERT"]

def difficulty_sort(a, b):
  if a in DIFFICULTY_LIST and b in DIFFICULTY_LIST:
    return cmp(DIFFICULTY_LIST.index(a), DIFFICULTY_LIST.index(b))
  elif a in DIFFICULTY_LIST: return -1
  elif b in DIFFICULTY_LIST: return 1
  else: return cmp(a, b)

def difficulty_sort_key(k):
  try: return DIFFICULTY_LIST.index(k)
  except ValueError: return len(DIFFICULTY_LIST)

# Return the subtitle of a song...
def find_subtitle(title):
  for pair in [("[", "]"), ("(", ")"), ("~", "~"), ("-", "-")]:
    if pair[0] in title and title[-1] == pair[1]:
      l = title[0:-1].rindex(pair[0])
      if l != 0:
        subtitle = title[l:]
        title = title[:l]
        return title, subtitle
  else: return title, ""

# FIXME: We should inline this. Really.
# Or not, Psyco does it for us, basically.
def toRealTime(bpm, steps):
  return steps*0.25*60.0/bpm

# Search the directory specified by path recursively for files that match
# the shell wildcard pattern. A list of all matching file names is returned,
# with absolute paths.
def find(path, patterns):
  root = os.path.abspath(os.path.expanduser(path))
  matches = []

  for path,dirs,files in os.walk(root):
    for fn in files:
      filepath = os.path.join(path, fn)
      for pattern in patterns:
        if fnmatch.fnmatch(filepath.lower(), pattern):
          matches.append(filepath)
          break

  return matches

# This uses a bunch of heuristics to come up with a good titlecased
# string. Python's titlecase function sucks.
def titlecase(title):
  nonletter = 0
  uncapped = ("in", "a", "the", "is", "for", "to", "by", "of", "de", "la")
  vowels = "aeiouyAEIOUY"
  letters = string.letters + "?!'" # Yeah, those aren't letters, but...

  parts = title.split()
  if len(parts) == 0: return ""

  for i,p in enumerate(parts):
    nonletter = 0
    has_vowels = False
    for l in p:
      if l not in letters: nonletter += 1
      if l in vowels: has_vowels = True
    if float(nonletter) / len(p) < 1.0/3:
      if p == p.upper() and has_vowels:
        p = parts[i] = p.lower()
        if p not in uncapped:
          p = parts[i] = p.capitalize()


  # Capitalize the first and last words in the name, unless they are
  # are "stylistically" lowercase.
  for i in (0, -1):
    if parts[i] != parts[i].lower() or parts[i] in uncapped:
      oldparts = parts[i]
      parts[i] = parts[i][0].capitalize() + oldparts[1:]

  return " ".join(parts)
