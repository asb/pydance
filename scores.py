# Scoring algorithms.

# Data on many algorithms taken from www.aaroninjapan.com/ddr2.html

# N = Number of steps in the song.
# H = Current song number (in a sequence of songs).
# F = Feet rating of the song.
# S(N) = N * (N + 1) / 2.
# n = Current step number.
# L(r) = Lookup function for the current step's rating.
# C = Current combo count.
# V(n) = The point value of the nth step.

import colors
import pygame
import fontfx

from listener import Listener
from constants import *

from i18n import *

from fonttheme import FontTheme

class AbstractScore(Listener, pygame.sprite.Sprite):
  def __init__(self, pid, text, game):
    pygame.sprite.Sprite.__init__(self)
    self.score = 0
    self._set_text(text)
    self.image = pygame.surface.Surface((160, 48))
    self.rect = self.image.get_rect()
    self.rect.bottom = 484
    self.rect.centerx = game.sprite_center + pid * game.player_offset

  def _set_text(self, text):
    tx = FontTheme.Dance_score_display.size(text)[0] + 2
    txt = fontfx.embfade(text, FontTheme.Dance_score_display, 2, (tx, 24), colors.color[_("gray")])
    basemode = pygame.transform.scale(txt, (tx, 48))
    self.baseimage = pygame.surface.Surface((128, 48))
    self.baseimage.blit(basemode, (64 - (tx / 2), 0))
    self.oldscore = -1 # Force a refresh

  def set_song(self, pid, bpm, difficulty, count, holds, feet):
    self._set_text(_(difficulty))

  def update(self, curtime):
    if self.score != self.oldscore:
      self.image.blit(self.baseimage, (0,0))
      scoretext = FontTheme.Dance_score_display.render(str(int(self.score)), 1, (192,192,192))
      self.image.blit(scoretext, (64 - (scoretext.get_rect().size[0] / 2), 13))
      self.image.set_colorkey(self.image.get_at((0, 0)), RLEACCEL)
      self.oldscore = self.score

# This is pydance's custom scoring algorithm. It's designed to make
# scores "fair" between different difficulty modes and game types.

# L(V) = 4, L(P) = 3.5, L(G) = 2.5, L(O) = 0.5
# V(n) = L(r) * 10,000,000 / N + 10,000,000 / S(N) * C
class PydanceScore(AbstractScore):
  def set_song(self, pid, bpm, text, count, hold, feet):
    AbstractScore.set_song(self, pid, bpm, text, count, hold, feet)
    if count == 0: count = 1 # Don't crash on empty songs.

    score_coeff = 10000000.0 / count
    self.combo_coeff = 10000000.0 / (count * (count + 1) / 2.0)
    self.inc = { "V": 4 * score_coeff, "P": 3.5 * score_coeff,
                 "G": 2.5 * score_coeff, "O": 0.5 * score_coeff }

  def stepped(self, pid, dir, cur_time, etime, rating, combo):
    if rating == None: return
    self.score += self.inc.get(rating, 0) + combo * self.combo_coeff

# M = floor(C / 4)
# L(V) = L(P) = M * 300, L(G) = M * 100, L(O) = 100
# V(n) = M * L(r)
class FirstScore(AbstractScore):
  def __init__(self, pid, text, game):
    AbstractScore.__init__(self, pid, text, game)
    self.combo = 0

  def stepped(self, pid, dir, cur_time, etime, rating, combo):
    if rating == None: return
    if self.combo == combo == 0: return # No points when combo is 0.

    self.combo += 1

    if combo == 0: # The rating can't be great or better, since combo == 0.
      if rating == "O": self.score += self.combo / 4 * 100
      self.combo = 0
    else:
      if rating == "G":
        self.score += self.combo * self.combo / 4 * 100
      else: # Must be a better-than-great.
        self.score += self.combo * self.combo / 4 * 300

# L(V) = L(P) = 10, L(G) = 5, L(O) = 1
# V(n) = L(r) * 1,000,000 / S(N) * n

# V(n) = L(r) * K / S(N) * n is common, and so many classes descend from
# this one and override set_song.
class ThirdScore(AbstractScore):
  def set_song(self, pid, bpm, text, count, hold, feet):
    AbstractScore.set_song(self, pid, bpm, text, count, hold, feet)
    if count == 0: count = 1
    self.arrow = 0

    p = 1000000.0 / (count * (count + 1) / 2)
    self.inc = { "V": p * 10, "P": p * 10, "G": p * 5, "O": p }

  def stepped(self, pid, dir, curtime, etime, rating, combo):
    if rating == None: return
    self.arrow += 1
    self.score += self.inc.get(rating, 0) * self.arrow

# L(V) = L(P) = 777, L(G) = 555
# V(n) = L(r) + C * 333
class FourthScore(AbstractScore):
  def stepped(self, pid, dir, cur_time, etime, rating, combo):
    if rating == None: return
    base = {"V": 777, "P": 777, "G": 555 }
    self.score += base.get(rating, 0) + combo * 333

# L(V) = L(P) = 10, L(G) = 5
# V(n) = L(r) * 500,000 * (F + 1) / S(N) * n

# The bonus for your combo or final grade is not implemented yet.
# This would require a Listener event for the end of the song.
class FifthScore(ThirdScore):
  def set_song(self, pid, bpm, text, count, hold, feet):
    AbstractScore.set_song(self, pid, bpm, text, count, hold, feet)
    self.arrow = 0
    s = 500000.0 * (feet + 1) / float((count * (count + 1)) / 2)
    self.inc = { "V": 10 * s, "P": 10 * s, "G": 5 * s }

# Max's score algorithm relys on calculating the "groove radar" values,
# which we don't do. So, it stays unimplemented.

# L(V) = L(P) = 10, L(G) = 5
# V(n) = L(r) * 1,000,000 * F / S(N) * n

# In pydance's implementation, jumps are counted as two arrows; in
# 8rd, they aren't.
class ExtremeScore(ThirdScore):
  def set_song(self, pid, bpm, text, count, hold, feet):
    AbstractScore.set_song(self, pid, bpm, text, count, hold, feet)
    if count == 0: count = 1 # Don't crash on empty songs.

    self.arrow = 0
    score_coeff = (1000000.0 * feet) / ((count * (count + 1.0)) / 2.0)
    self.inc = { "V": 10 * score_coeff, "P": 10 * score_coeff,
                 "G": 5 * score_coeff }

# This is closer to the grading algorithm than to a scoring algorithm.
class ExtremeOniScore(AbstractScore):
  def stepped(self, pid, dir, cur_time, etime, rating, combo):
    self.score += {"V": 3, "P": 2, "G": 1}.get(rating, 0)

  def ok_hold(self, pid, time, dir, whichone): self.score += 3

# L(V) = 10, L(P) = 9, L(G) = 5
# V(n) = L(r) * 1,000,000 * H / S(N) * n
class ExtremeNonstopScore(ThirdScore):
  def __init__(self, pid, text, game):
    AbstractScore.__init__(self, pid, text, game)
    self.song = 0
  
  def set_song(self, pid, bpm, text, count, hold, feet):
    AbstractScore.set_song(self, pid, bpm, text, count, hold, feet)
    if count == 0: count = 1 # Don't crash on empty songs.
    self.song += 1

    self.arrow = 0
    score_coeff = (1000000.0 * self.song) / ((count * (count + 1.0)) / 2.0)
    self.inc = { "V": 10 * score_coeff, "P": 9 * score_coeff,
                 "G": 5 * score_coeff }

# EZ2Dancer scoring algorithm.
# http://www.annie.ne.jp/~ken/S3C21/ez2d_score.html
class EZ2DancerScore(ThirdScore):
  def set_song(self, pid, bpm, text, count, hold, feet):
    AbstractScore.set_song(self, pid, bpm, text, count, hold, feet)
    if count == 0: count = 1
    self.arrow = 0
    self.inc = { "V": 21, "P": 9, "G": 3 }

scores = [PydanceScore, FirstScore, ThirdScore, FourthScore,
          FifthScore, ExtremeScore, ExtremeOniScore, ExtremeNonstopScore,
          EZ2DancerScore]
score_opt = [(0, _("pydance"), ""), (1, _("DDR 1st/2nd Mix"), ""),
             (2, _("DDR 3rd Mix"), ""), (3, _("DDR 4th Mix"), ""),
             (4, _("DDR 5th Mix"), ""), (5, _("DDR 7th/8th"), ""),
             (6, _("DDR 8th Oni"), ""), (7, _("DDR 8th Nonstop"), ""),
             (8, _("EZ2 Dancer"), "")]
