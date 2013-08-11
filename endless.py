# Support for endless song playing!

import random
import colors
import error
import dance
import util
import options
import sys
from pygame.mixer import music
from interface import *
from constants import *

import ui

from i18n import *
from fonttheme import FontTheme

ENDLESS_HELP = [
  _("Left: Make the songs that will be played easier"),
  _("Right: Make the songs that will be played harder"),
  _("Up: Select difficulty by name"),
  _("Down: Select difficulty by rating"),
  _("Enter / Up Right: Start playing songs until you fail"),
  _("Escape / Up Left: Go back to the game selection screen"),
  _("Start: Go to the options screen / F11: Toggle fullscreen"),
  ]

def check_constraints(constraints, diff):
  for c in constraints:
    if not c.meets(diff): return False
  return True

class EndlessDiffDisplay(pygame.sprite.Sprite):
  def __init__(self, pid, constraint):
    pygame.sprite.Sprite.__init__(self)
    self._c = constraint
    self._ptext = fontfx.shadow(_("Player %d") % (pid + 1), FontTheme.Endless_player, colors.WHITE)
    self._pr = self._ptext.get_rect()
    self._centerx = 160 + 320 * pid
    self._oldval = None
    self.update(0)

  def update(self, time):
    if self._oldval != (self._c.kind, self._c.value):
      if self._c.kind == "name":
        ctext = fontfx.shadow(_("Select by Difficulty"), FontTheme.Endless_filter_by, colors.WHITE)
	i18ndifficulty = _(self._c.value)
	vtext = fontfx.shadow(i18ndifficulty.capitalize(), FontTheme.Endless_filter_range, colors.WHITE)
      elif self._c.kind == "number":
        ctext = fontfx.shadow(_("Select by Rating"), FontTheme.Endless_filter_by, colors.WHITE)
        vtext = fontfx.shadow(_("Between %d and %d") % self._c.value, FontTheme.Endless_filter_range,
                                 colors.WHITE)
      self.image = pygame.Surface([300, 400])
      cr = ctext.get_rect()
      vr = vtext.get_rect()
      self._pr.centerx = cr.centerx = vr.centerx = 150
      self._pr.top = 0
      cr.top = 100
      vr.top = 200
      self.image.blit(self._ptext, self._pr)
      self.image.blit(ctext, cr)
      self.image.blit(vtext, vr)
      self.image.set_colorkey(self.image.get_at([0, 0]))

      self.rect = self.image.get_rect()
      self.rect.center = [self._centerx, 340]

# For selecting songs
class Constraint(object):
  def __init__(self, kind, value):
    self.kind = kind
    self.value = value

  def meets(self, diffs):
    if self.kind == "name":
      if diffs.has_key(self.value): return True
      else: return False
    elif self.kind == "number":
      for k in diffs:
        if diffs[k] in range(self.value[0], self.value[1] + 1): return True
      return False

  def diff(self, diffs):
    if self.kind == "name": return self.value
    elif self.kind == "number":
      for k in diffs:
        if diffs[k] in range(self.value[0], self.value[1] + 1): return k

# Generate a playlist forever
class FakePlaylist(object):
  def __init__(self, songs, constraints, screen, mode):
    self.songs = [s for s in songs if (s.info["valid"] and
                                       check_constraints(constraints,
                                                        s.difficulty[mode]))]
    self.working = []
    self.mode = mode
    self.constraints = constraints
    self.numplayers = len(constraints)
    self.screen = screen

  def __iter__(self):
    return self

  # len(x) returns int(x.__len__()) if x.__len__() > 0 and is numeric,
  # exception otherwise, so returning float("+inf") or None is
  # impossible. Thus, the largest regular integer is returned, which
  # is as close to "infinity" as we can get.
  def __len__(self): return sys.maxint

  def next(self):
    if len(self.songs) == 0:
      error.ErrorMessage(self.screen,
                         _("The difficulty settings you chose result ") +
                         _("in no songs being available to play."))
      raise StopIteration
    elif len(self.working) == 0: self.working = self.songs[:]
    i = random.randint(0, len(self.working) - 1)
    song = self.working[i]
    del(self.working[i])
    return (song.filename,
            [c.diff(song.difficulty[self.mode]) for c in self.constraints])

class Endless(InterfaceWindow):
  def __init__(self, songitems, courses, screen, gametype):
    InterfaceWindow.__init__(self, screen, "endless-bg.png");
    pygame.display.update()

    self.player_configs = [dict(player_config)]

    if games.GAMES[gametype].players == 2:
      self.player_configs.append(dict(player_config))

    self.game_config = dict(game_config)
    songitems = [s for s in songitems if s.difficulty.has_key(gametype)]
    # Autofail always has to be on for endless, so back up the old value.
    oldaf = mainconfig["autofail"]
    diffs = []
    diff_count = {} # if we see a difficulty 2 times or more, use it
    for song in songitems:
      if song.difficulty.has_key(gametype):
        for d in song.difficulty[gametype]:
          if diff_count.has_key(d) and d not in diffs : diffs.append(d)
          else: diff_count[d] = True

    diffs.sort(util.difficulty_sort)

    if len(diffs) == 0:
      error.ErrorMessage(screen, _("You need more songs to play Endless Mode. ") +
                         _("Otherwise, it's just really boring."))
      return

    mainconfig["autofail"] = 1

    self.constraints = [Constraint("name", songitems[0].difficulty[gametype].keys()[0])]

    if games.GAMES[gametype].players == 2:
      if games.GAMES[gametype].couple == True:
        # Lock both players to the same constraints in couple modes.
        self.constraints.append(self.constraints[0])
      else:
        c = Constraint("name", songitems[0].difficulty[gametype].keys()[0])
        self.constraints.append(c)

    for i, c in enumerate(self.constraints):
      EndlessDiffDisplay(i, c).add(self._sprites)

    self._sprites.add(HelpText(ENDLESS_HELP, [255, 255, 255], [0, 0, 0],
                               FontTheme.help, [320, 20]))

    music.load(os.path.join(sound_path, "menu.ogg"))
    music.play(4, 0.0)

    pid, ev = 0, ui.PASS

    while ev != ui.QUIT:
      pid, ev = ui.ui.poll()

      if ev == ui.START:
        options.OptionScreen(self.player_configs, self.game_config, screen)
        self._screen.blit(self._bg, [0, 0])
        pygame.display.update()

      # Start game
      elif ev == ui.CONFIRM:
        dance.play(screen, FakePlaylist(songitems, self.constraints,
                                        screen, gametype),
                   self.player_configs, self.game_config, gametype)

        self._screen.blit(self._bg, [0, 0])
        pygame.display.update()
        music.load(os.path.join(sound_path, "menu.ogg"))
        music.play(4, 0.0)
        ui.ui.clear()

      # Ignore unknown events
      elif pid >= len(self.constraints): pass

      elif ev == ui.DOWN and self.constraints[pid].kind != "name":
        self.constraints[pid].kind = "name"
        self.constraints[pid].value = diffs[0]
      elif ev == ui.UP and self.constraints[pid].kind != "number":
        self.constraints[pid].kind = "number"
        self.constraints[pid].value = (1, 3)
      elif ev == ui.LEFT: # easier
        if self.constraints[pid].kind == "name":
          newi = max(0, diffs.index(self.constraints[pid].value) - 1)
          self.constraints[pid].value = diffs[newi]
        elif self.constraints[pid].kind == "number":
          newmin = max(self.constraints[pid].value[0] - 1, 1)
          self.constraints[pid].value = (newmin, newmin + 2)

      elif ev == ui.RIGHT: # harder
        if self.constraints[pid].kind == "name":
          newi = min(len(diffs) - 1,
                     diffs.index(self.constraints[pid].value) + 1)
          self.constraints[pid].value = diffs[newi]
        elif self.constraints[pid].kind == "number":
          newmin = min(self.constraints[pid].value[0] + 1, 9)
          self.constraints[pid].value = (newmin, newmin + 2)

      elif ev == ui.FULLSCREEN:
        mainconfig["fullscreen"] ^= 1
        pygame.display.toggle_fullscreen()

      self.update()

    mainconfig["autofail"] = oldaf
    player_config.update(self.player_configs[0])
