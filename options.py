# ceci n'est e'galement pas un e'cran d'option

import os
import pygame
import fontfx
import math
import colors
import ui
import scores
import combos
import grades
import judge
import lifebars

from constants import *
from interface import *

from i18n import *

ON_OFF = [(0, _("Off"), ""), (1, _("On"), "")]

# Description gets assigned 2 both times.
PP, NAME, DESCRIPTION, VALUES = range(4)
VALUE, NAME, DESCRIPTION = range(3)

OPTIONS = {
  # Option specifier tuple:
  # 0. a boolean indicating whether the option is per-player (True) or not.
  # 1. The name of the option.
  # 2. A description of the option.
  # 3. A list of 3-tuples (a, b, c) where a is the value of the option.
  #    b is the string to display for that value, and c is a string
  #    describing the value.
  "speed": (True, _("Speed"),
            _("Adjust the speed at which the arrows scroll across the screen."),
            zip([0.25, 0.33, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 5, 8, -200, -300, -400, -500, -600, -700, -800],
                ["0.25x", "0.33x", "0.50x", "0.75x", "1.0x", "1.5x", "2.0x", "2.5x",
                 "3.0x", "4.0x", "5.0x", "8.0x", "200bpm", "300bpm", "400bpm", "500bpm", "600bpm", "700bpm", "800bpm"],
                [""] * 12 + [_("Arrows scroll at 200bpm."), _("Arrows scroll at 300bpm."), _("Arrows scroll at 400bpm."), _("Arrows scroll at 500bpm."), _("Arrows scroll at 600bpm."), _("Arrows scroll at 700bpm."), _("Arrows scroll at 800bpm.")])
            ),
  "transform": (True, _("Transform"),
                _("Change the step patterns for the song."),
                zip([0, 1, 2, 3, -1, -2],
                    [_("Normal"), _("Mirror"), _("Left"), _("Right"), _("Shuffle"), _("Random")],
                    ["", _("Rotate the steps 180 degrees."),
                     _("Rotate the steps 90 degrees to the left."),
                     _("Rotate the steps 90 degrees to the right."),
                     _("Swap all arrows from one direction to another."),
                     _("Use totally random directions.")])
                ),
  "size": (True, _("Add/Remove Steps"),
           _("Add or remove arrows from step patterns."),
           zip([1, 2, 0, 3, 4, 5],
               [_("Tiny"), _("Little"), _("Normal"), _("Big"), _("Quick"), _("Skippy")],
               [_("Only dance to on-beat notes."),
                _("Only dance to on-beat and half-beat notes."),
                "", _("Add half-beat steps between on-beat ones."),
                _("Add steps between half-beat ones."),
                _("Add gallops between on-beat steps.")])
           ),
  "fade": (True, _("Fade"),
           _("Fade arrows in or out while they scroll."),
           zip([0, 1, 2, 3, 4, 5],
               [_("Normal"), _("Sudden"), _("Hidden"), _("Peek"), _("Cycle"), _("Stealth")],
               ["", _("Only display arrows near the top."),
                _("Only display arrows near the bottom."),
                _("Only display arrows near the middle."),
                _("Blink arrows in and out."),
                _("No arrows are displayed.")])
           ),
  "accel": (True, _("Acceleration"),
            _("Accelerate or decelerate arrows."),
            zip([2, 0, 1],
                [_("Brake"), _("Normal"), _("Boost")],
                [_("Decelerate near the top"), "", _("Accelerate near the top.")])
            ),
  "scale": (True, _("Size"),
            _("Change arrow sizes."),
            zip([0, 1, 2],
                [_("Shrink"), _("Normal"), _("Grow")],
                [_("Smaller arrows near the top."), "",
                 _("Smaller arrows near the bottom.")])
            ),
  "scrollstyle": (True, _("Direction"),
                  _("Change the direction arrows scroll."),
                  zip([0, 1, 2],
                      [_("Normal"), _("Reverse"), _("Center")],
                      [_("Arrows go from bottom to top."),
                       _("Arrows go from top to bottom."),
                       _("Arrows go from the top and bottom to the center.")])
                  ),
  "jumps": (True, _("Jumps"),
            _("Turn jumps off, or add more."),
            zip([0, 1, 2],
                [_("Off"), _("On"), _("Wide")],
                [_("Remove jumps from the song."), "",
                 _("Add jumps on every on-beat step.")])
            ),
  "spin": (True, _("Spin"),
           _("Rotate arrows as they go up the screen."),
           ON_OFF),
  "colortype": (True, _("Colors"),
                _("Use colors of arrows to indicate the beat."),
                zip([1, 4],
                    [_("Flat"), _("Normal")],
                    [_("All arrows are the same."),
                     _("Different arrows have different colors.")])
                ),
  "dark": (True, _("Dark"),
           _("Don't display the top arrows."),
           ON_OFF),
  "holds": (True, _("Holds"),
            _("Allow hold ('freeze') arrows in songs."),
            ON_OFF),
  "scoring": (False, _("Scoring"),
              _("The scoring algorithm."),
              scores.score_opt),
  "grade": (False, _("Grades"),
            _("The grading algorithm."),
            grades.grade_opt),
  "combo": (False, _("Combos"),
             _("How your combo increases."),
             combos.combo_opt),
  "judge": (False, _("Judging Method"),
            _("How your steps are judged."),
            judge.judge_opt),
  "judgescale": (False, _("Judging Windows"),
                 _("The margin of error for your steps."),
                 zip([2.0 - 0.2 * i for i in range(10)],
                     [str(i) for i in range(10)],
                     [_("Window is twice normal size."),
                      _("Window is 9/5 normal size."),
                      _("Window is 8/5 normal size."),
                      _("Window is 7/5 normal size."),
                      _("Window is 6/5 normal size."), "",
                      _("Window is 4/5 normal size."),
                      _("Window is 3/5 normal size."),
                      _("Window is 2/5 normal size."),
                      _("Window is 1/5 normal size.")])
                 ),

  "life": (False, _("Life"),
                 _("Increase or decrease your amount of (non-battery) life."),
                 [(0.25, _("Undead"), _("Life is 1/4 the usual amount.")),
                  (0.50, _("Very Low"), _("Life is 1/2 the usual amount.")),
                  (0.75, _("Low"), _("Life is 3/4 the usual amount.")),
                  (1, _("Normal"), ""),
                  (1.25, _("High"), _("Life is 5/4 the usual amount.")),
                  (1.50, _("Very High"), _("Life is 3/2 the usual amount.")),
                  (1.75, _("Lazarus"), _("Life is 7/4 the usual amount."))]
                 ),
  "lifebar": (False, _("Lifebar"),
              _("The kind of lifebar used."),
              lifebars.lifebar_opt),
  "onilives": (False, _("Oni Lives"),
               _("The initial / maximum life in Battery mode."),
               [(i, str(i), "") for i in range(1, 9)]),
  "secret": (False, _("Secret Arrows"),
             _("Secret arrow display"),
             [(0, _("Off"), _("Disable secret arrows.")),
              (1, _("Invisible"), _("Enable but don't display them.")),
              (2, _("Faint"), _("Show secret arrows faintly."))]
             ),
  "battle": (False, _("Battle Mode"),
             _("Arrows start in the center and float outwards."),
             ON_OFF),
  }
            
OPTS = [ "speed", "transform", "size", "fade", "accel", "scale",
         "scrollstyle", "jumps", "spin", "colortype", "dark", "holds",
         "scoring", "combo", "grade", "judge", "lifebar", "judgescale",
         "life", "onilives", "secret", "battle"
         ]

O_HELP = [
  _("Up / Down: Select option"),
  _("Left / Right: Change value"),
  _("Start: Return to song selector"),
  _("F11: Toggle fullscreen")
  ]

def index_of(value, name):
  values = OPTIONS[name][VALUES]
  for i, v in enumerate(values):
    if v[VALUE] == value: return i
  return None

def value_of(index, name):
  return OPTIONS[name][VALUES][index][VALUE]

class OptionSelect(pygame.sprite.Sprite):
  def __init__(self, possible, center, index):
    pygame.sprite.Sprite.__init__(self)
    self._index = self._oldindex = index
    self._possible = possible
    self._center = center
    self._end_time = pygame.time.get_ticks()
    self._needs_update = True
    self._font = FontTheme.Opts_choices
    self._render(pygame.time.get_ticks())

  def update(self, time):
    if self._needs_update:
      self._render((self._end_time - time) / 200.0)

  def set_possible(self, possible, index = -1):
    self._possible = possible
    self._oldindex = self._index = index
    self._end_time = pygame.time.get_ticks()

    self._needs_update = True

  def set_index(self, index):
    self._oldindex = self._index
    self._index = index
    if self._oldindex == -1: self._oldindex = self._index
    self._end_time = pygame.time.get_ticks() + 200
    self._needs_update = True

  def _render(self, pct):
    self.image = pygame.Surface([430, 40], SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])
    self.rect = self.image.get_rect()
    self.rect.center = self._center

    if pct <= 0:
      self._needs_update = False
      offset = 0
      pct = 1
    elif self._oldindex != self._index:
      offset = (self._font.size(self._possible[self._oldindex])[0]/2 +
                self._font.size(self._possible[self._index])[0]/2 + 30)
      offset = int(pct * offset)
      if self._oldindex > self._index: offset = -offset
    else: offset = 0

    t = fontfx.shadow(self._possible[self._index],
                      FontTheme.Opts_choices, [255, 255, 255])
    r = t.get_rect()
    r.center = [215 + offset, 20]
    self.image.blit(t, r)
    old_r = Rect(r)
    
    idx = self._index - 1
    while idx >= 0 and r.left > 0:
      t = fontfx.shadow(self._possible[idx],
                        FontTheme.Opts_choices, [255, 255, 255])
      t2 = pygame.Surface(t.get_size())
      t2.blit(t, [0, 0])
      t2.set_colorkey(t2.get_at([0, 0]))
      r2 = t2.get_rect()
      r2.centery = 20
      r2.right = r.left - 30
      t2.set_alpha(int(200 * (r2.centerx / 215.0)))
      self.image.blit(t2, r2)
      idx -= 1
      r = r2

    idx = self._index + 1
    r = old_r
    while idx < len(self._possible) and r.right < 430:
      t = fontfx.shadow(self._possible[idx],
                        FontTheme.Opts_choices, [255, 255, 255])
      t2 = pygame.Surface(t.get_size())
      t2.blit(t, [0, 0])
      t2.set_colorkey(t2.get_at([0, 0]))
      r2 = t2.get_rect()
      r2.centery = 20
      r2.left = r.right + 30
      t2.set_alpha(int(200 * ((430 - r2.centerx) / 215.0)))
      self.image.blit(t2, r2)
      idx += 1
      r = r2

class OptionScreen(InterfaceWindow):
  def __init__(self, player_configs, game_config, screen, whitelist=None):
    InterfaceWindow.__init__(self, screen, "option-bg.png")

    if whitelist is None:
      self.optlist = OPTS
    else:
      self.optlist = [opt for opt in OPTS if opt in whitelist]

    self._configs = player_configs
    self._config = game_config
    self._players = len(self._configs)

    self._lists = [ListBox(FontTheme.Opts_list, [255, 255, 255],
                           25, 9, 176, [10, 10])]
    self._text = [WrapTextDisplay(FontTheme.Opts_description, 430, [198, 165], centered = True,
                                  str = OPTIONS[self.optlist[0]][DESCRIPTION])]    
    val = self._configs[0][self.optlist[0]]
    names = [v[NAME] for v in OPTIONS[self.optlist[0]][VALUES]]
    desc = OPTIONS[self.optlist[0]][VALUES][index_of(val, self.optlist[0])][DESCRIPTION]
    self._text2 = [WrapTextDisplay(FontTheme.Opts_choice_description, 430, [198, 105], centered = True,
                                  str = desc)]
    self._displayers = [OptionSelect(names, [415, 40],
                                     index_of(val, self.optlist[0]))]
    self._index = [0]
    ActiveIndicator([5, 106], height = 25, width = 185).add(self._sprites)
    if self._players == 2:
      self._lists.append(ListBox(FontTheme.Opts_list, [255, 255, 255],
                                 25, 9, 176, [453, 246]))
      self._index.append(0)
      self._text.append(WrapTextDisplay(FontTheme.Opts_description, 430, [10, 275], centered = True,
                                        str = OPTIONS[self.optlist[0]][DESCRIPTION]))
      ActiveIndicator([448, 341], height = 25, width = 185).add(self._sprites)
      val = self._configs[1][self.optlist[0]]
      desc = OPTIONS[self.optlist[0]][VALUES][index_of(val, self.optlist[0])][DESCRIPTION]
      self._text2.append(WrapTextDisplay(FontTheme.Opts_choice_description, 430, [10, 350], centered = True,
                                         str = desc))
      self._displayers.append(OptionSelect(names, [220, 440],
                                           index_of(val, self.optlist[0])))

    HelpText(O_HELP, [255, 255, 255], [0, 0, 0],
             FontTheme.help, [320, 241]).add(self._sprites)
    self._sprites.add(self._lists + self._displayers + self._text +
                      self._text2)

    for l in self._lists: l.set_items([OPTIONS[k][1] for k in self.optlist])
    self._screen.blit(self._bg, [0, 0])

    pygame.display.update()
    self.loop()

  def loop(self):
    pid, ev = ui.ui.poll()
    for i, l in enumerate(self._lists): l.set_index(self._index[i])
    for i in range(self._players):
      opt = self.optlist[self._index[i]]
      self._displayers[i].set_index(index_of(self._configs[i][opt], opt))

    while ev not in [ui.START, ui.CANCEL, ui.CONFIRM]:
      if pid >= self._players: pass

      elif ev == ui.UP:
        self._index[pid] = (self._index[pid] - 1) % len(self.optlist)
        self._lists[pid].set_index(self._index[pid], -1)
      elif ev == ui.DOWN:
        self._index[pid] = (self._index[pid] + 1) % len(self.optlist)
        self._lists[pid].set_index(self._index[pid], 1)

      elif ev == ui.LEFT:
        opt = self.optlist[self._index[pid]]
        if OPTIONS[opt][PP]: index = index_of(self._configs[pid][opt], opt)
        else: index = index_of(self._config[opt], opt)
        if index > 0: index -= 1
        if OPTIONS[opt][PP]: self._configs[pid][opt] = value_of(index, opt)
        else: self._config[opt] = value_of(index, opt)
      elif ev == ui.RIGHT:
        opt = self.optlist[self._index[pid]]
        if OPTIONS[opt][PP]: index = index_of(self._configs[pid][opt], opt)
        else: index = index_of(self._config[opt], opt)
        if index != len(OPTIONS[opt][VALUES]) - 1: index += 1
        if OPTIONS[opt][PP]: self._configs[pid][opt] = value_of(index, opt)
        else: self._config[opt] = value_of(index, opt)
          
      elif ev == ui.FULLSCREEN:
        mainconfig["fullscreen"] ^= 1
        pygame.display.toggle_fullscreen()

      if ev in [ui.UP, ui.DOWN]:
        values = OPTIONS[self.optlist[self._index[pid]]][VALUES]
        names = [v[NAME] for v in values]
        self._displayers[pid].set_possible(names)
        self._text[pid].set_text(OPTIONS[self.optlist[self._index[pid]]][DESCRIPTION])

      if ev in [ui.LEFT, ui.RIGHT, ui.UP, ui.DOWN]:
        opt = self.optlist[self._index[pid]]
        if OPTIONS[opt][PP]:
          val = self._configs[pid][opt]
          idx = index_of(val, opt)
          self._displayers[pid].set_index(index_of(val, opt))
          self._text2[pid].set_text(OPTIONS[opt][VALUES][idx][DESCRIPTION])
        elif self._players > 1 and self._index[0] == self._index[1]:
          # If both players have the same non-per-player option
          # selected, we need to update both displayers.
          val = self._config[opt]
          idx = index_of(val, opt)
          for i in range(self._players):
            self._displayers[i].set_index(idx)
            self._text2[pid].set_text(OPTIONS[opt][VALUES][idx][DESCRIPTION])
        else:
          val = self._config[opt]
          idx = index_of(val, opt)
          self._displayers[pid].set_index(idx)
          self._text2[pid].set_text(OPTIONS[opt][VALUES][idx][DESCRIPTION])
      self.update()
      pid, ev = ui.ui.poll()
