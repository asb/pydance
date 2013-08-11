import os, random, dircache
import pygame

from listener import Listener

from constants import *

class Announcer(Listener):

  def themes(cls):
    theme_list = []
    for path in search_paths:
      checkpath = os.path.join(path, "themes", "dj")
      if os.path.isdir(checkpath):
        for name in dircache.listdir(checkpath):
          if os.path.isfile(os.path.join(checkpath, name, "djtheme.cfg")):
            theme_list.append(name)
    return theme_list

  themes = classmethod(themes)

  def __init__(self, name):
    self.sections = {}
    self.name = None
    self.author = None
    self.rev = None
    self.date = None
    filename = None
    for path in search_paths:
      if os.path.isfile(os.path.join(path,"themes","dj",name,"djtheme.cfg")):
        filename = os.path.join(path, "themes", "dj", name)
    if filename == None:
      raise SystemExit(_("E: Cannot load announcer theme '%s'.") % name)

    fi = file(os.path.join(filename, "djtheme.cfg"), "r")
    sec = ""
    self.lasttime = -1000000
    for line in fi:
      if line.isspace() or len(line) == 0 or line[0] == '#': pass
      elif line[0] == "[" and line.strip()[-1] == "]":
        sec = line.strip()[1:-1].lower()
        self.sections[sec] = []
      elif sec == "announcer":
        key, val = line[:line.find(' ')], line[line.find(' ')+1:].strip()
        if key == "name": self.name = val
        elif key == "author": self.author = val
        elif key == "rev": self.rev = val
        elif key == "date": self.date = val
      else:
        self.sections[sec].append(os.path.join(filename, line.strip()))

  def __play(self, filename):
    if not os.path.isfile(filename): return
    if (pygame.time.get_ticks() - self.lasttime > 6000):
      snd = pygame.mixer.Sound(filename)
      snd.play()
    self.lasttime = pygame.time.get_ticks()

  def stepped(self, pid, dir, curtime, etime, rating, combo):
    if random.randrange(15) != 1: return
    rng = { "V": [80, 100], "P": [80, 100],
            "G": [70, 94], "O": [40, 69],
            "B": [20, 30], "M": [0, 19] }.get(rating, [0, 100])
    self.say('ingame', rng)

  def say(self, sec, mood=(0, 100)):
    if not self.sections.has_key(sec) or len(self.sections[sec]) == 0: return
    l = len(self.sections[sec])
    # Normalize mood wrt the number of choices
    try:
      mood = (int(mood[0] / 100.0 * l), min(int(mood[1] / 100.0 * l), l - 1))
    except TypeError:
      # Use a random variance of 10% if a scalar is given
      mood = (int(max(mood / 100.0 - 0.1, 0) * l), # don't < 0
              int(min(mood / 100.0 + 0.1, 0.999) * l)) # don't == l

    self.__play(self.sections[sec][random.randint(mood[0], mood[1])])
