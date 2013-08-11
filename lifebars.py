# Different lifebars.

import os, pygame, fontfx

from listener import Listener
from constants import *

from i18n import *
from fonttheme import FontTheme

LIVING, FAILED, WON = range(3)

# The base lifebar class from which most other ones inherit.
class AbstractLifeBar(Listener, pygame.sprite.Sprite):
  def __init__(self, playernum, maxlife, songconf, game):
    pygame.sprite.Sprite.__init__(self)
    self.gameover = LIVING
    self.maxlife = maxlife * songconf["life"]
    self.image = pygame.Surface([204, 28])
    self.deltas = {}
    self.record = []
    self.last_record_update = 0

    self.failtext = fontfx.embfade(_("FAILED"), FontTheme.Dance_lifebar_text, 3, [80, 32], [224, 32, 32])
    self.failtext.set_colorkey(self.failtext.get_at([0, 0]), RLEACCEL)

    self.rect = self.image.get_rect()
    self.rect.top = 30
    self.rect.centerx = game.sprite_center + playernum * game.player_offset

  def set_song(self, *args):
    self.last_record_update = 0

  def stepped(self, pid, dir, curtime, etime, rating, combo):
    if self.life >= 0:
      self.life += self.deltas.get(rating, 0)
      self.life = min(self.life, self.maxlife)

  def update(self, time):
    if self.gameover: return False

    if self.life < 0: self.life = -1
    elif self.life > self.maxlife: self.life = self.maxlife

    if time - self.last_record_update > 0.5 and self.life >= 0:
      self.record.append(float(self.life) / float(self.maxlife))
      self.last_record_update = time

# Regular DDR-style lifebar, life from 0 to 100.
class LifeBarDisp(AbstractLifeBar):
  def __init__(self, playernum, theme, songconf, game):
    AbstractLifeBar.__init__(self, playernum, 1.0, songconf, game)
    self.life = self.maxlife / 2.0
    self.displayed_life = self.life

    self.deltas = {"V": 0.008, "P": 0.008, "G": 0.004, "B": -0.04, "M": -0.08}
    self.full, self.empty = theme.get_lifebar()

  def draw(self, time):
    time = int(1000 * time)
    full = self.full[(time / 33) % len(self.full)]
    empty = self.empty[(time / 33) % len(self.empty)]
    
    self.image.blit(empty, [0, 0])
    self.image.set_clip([0, 0,
                         int(202 * self.displayed_life / self.maxlife), 28])
    self.image.blit(full, [0, 0])
    self.image.set_clip()

  def update(self, time):
    if self.gameover and self.displayed_life <= 0: return

    if self.displayed_life < self.life:  self.displayed_life += 0.01
    elif self.displayed_life > self.life:  self.displayed_life -= 0.01

    if abs(self.displayed_life - self.life) < 0.01:
      self.displayed_life = self.life

    AbstractLifeBar.update(self, time)

    if self.life < 0: self.gameover = FAILED
    if self.displayed_life < 0: self.displayed_life = 0

    self.draw(time)

    if self.gameover: self.image.blit(self.failtext, (70, 2))

# A lifebar that only goes down.
class DropLifeBarDisp(LifeBarDisp):
  def __init__(self, playernum, theme, songconf, game):
    LifeBarDisp.__init__(self, playernum, theme, songconf, game)
    self.life = self.maxlife # Start at full life
    for k in self.deltas:
      if self.deltas[k] > 0: self.deltas[k] = 0

# Only greats make the bar go up.
class GreatAttack(LifeBarDisp):
  def __init__(self, playernum, theme, songconf, game):
    LifeBarDisp.__init__(self, playernum, theme, songconf, game)
    self.deltas = {"V": -0.005, "P": -0.005, "G": 0.008, "O": -0.005,
                   "B": -0.02, "M": -0.06}

# Tug of war lifebar, increases your lifebar and decreases your opponents'.
class TugLifeBarDisp(LifeBarDisp):

  active_bars = []

  def __init__(self, playernum, theme, songconf, game):
    LifeBarDisp.__init__(self, playernum, theme, songconf, game)

    self.wontext = fontfx.embfade("WON",FontTheme.Dance_lifebar_text,3,(80,32),(224,32,32))
    self.wontext.set_colorkey(self.failtext.get_at((0,0)), RLEACCEL)
    self.deltas = {"V": 0.02, "P": 0.02, "G": 0.01, "B": -0.01, "M": -0.02 }

    # If we're player 1, it's a new game, so delete the old lifebars.
    if playernum == 0: TugLifeBarDisp.active_bars = [self]
    else: TugLifeBarDisp.active_bars.append(self)

  def stepped(self, pid, dir, curtime, etime, rating, combo):
    LifeBarDisp.stepped(self, pid, dir, curtime, etime, rating, combo)
    for bar in TugLifeBarDisp.active_bars:
      if bar != self: bar.update_life_opponent(rating)
    
  def update_life_opponent(self, rating):
    if self.life >= 0: self.life -= self.deltas.get(rating, 0)

  def update(self, time):
    if self.gameover and self.displayed_life <= 0: return

    if self.displayed_life < self.life:  self.displayed_life += 0.01
    elif self.displayed_life > self.life:  self.displayed_life -= 0.01

    if abs(self.displayed_life - self.life) < 0.01:
      self.displayed_life = self.life

    AbstractLifeBar.update(self, time)

    if self.life < 0: self.gameover = FAILED
    if self.displayed_life < 0: self.displayed_life = 0

    self.draw(time)

    if self.gameover == WON:
      self.image.blit(self.wontext, (70, 2))
    elif self.gameover == FAILED:
      self.image.blit(self.failtext, (70, 2))
      for lifebar in TugLifeBarDisp.active_bars:
        if lifebar != self and not lifebar.gameover: lifebar.gameover = WON

# Lifebar where doing too good also fails you.
class MediocreLifeBarDisp(AbstractLifeBar):
  def __init__(self, playernum, theme, songconf, game):
    AbstractLifeBar.__init__(self, playernum, 1.0, songconf, game)
    self.life = self.maxlife / 2

    self.deltas = {"V": 0.04, "P": 0.04, "G": 0.02,
                       "O": -0, "B": -0.02, "M": -0.04 }
    self.image = pygame.surface.Surface([202, 28])
    self.image.fill([255, 255, 255])

  def update(self, time):
    if self.gameover: return

    AbstractLifeBar.update(self, time)

    if self.life < 0 or self.life == self.maxlife: self.gameover = FAILED

    pct = abs(self.life - self.maxlife) / self.maxlife * 2
    if pct > 1: pct = max(2 - pct, 0)
    self.image.fill([int(255 * pct)] * 3)

    if self.gameover: self.image.blit(self.failtext, (70, 2))

# Oni mode lifebar, anything that breaks a combo loses a life.
class OniLifeBarDisp(AbstractLifeBar):

  lose_sound = pygame.mixer.Sound(os.path.join(sound_path, "loselife.ogg"))

  def __init__(self, playernum, theme, songconf, game):
    AbstractLifeBar.__init__(self, playernum, songconf["onilives"],
                             songconf, game)

    # Override the songconf["diff"] stuff.
    self.maxlife = self.life = songconf["onilives"]

    self.deltas = { "O": -1, "B": -1, "M": -1}
    self.empty = theme.theme_data.get_image('oni-empty.png')
    self.bar = theme.theme_data.get_image('oni-bar.png')

    self.width = 192 / self.maxlife
    self.bar = pygame.transform.scale(self.bar, (self.width, 20))

  def set_song(self, pid, bpm, diff, count, hold, feet):
    self.life = min(self.maxlife, self.life + 1)

  def broke_hold(self, pid, time, dir, whichone):
    OniLifeBarDisp.lose_sound.play()
    self.life -= 1
       
  def stepped(self, pid, dir, curtime, etime, rating, combo):
    AbstractLifeBar.stepped(self, pid, dir, curtime, etime, rating, combo)
    if self.deltas.get(rating, 0) < 0: OniLifeBarDisp.lose_sound.play()

  def update(self, time):
    if self.gameover: return

    AbstractLifeBar.update(self, time)

    self.image.blit(self.empty, [0, 0])
    for i in range(self.life):
      self.image.blit(self.bar, [6 + self.width * i, 4])
    if self.life < 0: self.gameover = FAILED

    if self.gameover: self.image.blit(self.failtext, [70, 2])

bars = [LifeBarDisp, OniLifeBarDisp, DropLifeBarDisp, MediocreLifeBarDisp,
        TugLifeBarDisp, GreatAttack]

lifebar_opt = [(0, _("Normal"), ""),
               (1, _("Battery"), _("A few points of life, increasing each song.")),
               (2, _("Power Drop"), _("Like normal, but never goes back up.")),
               (3, _("Mediocre"), _("Fail if you do too poorly or too well.")),
               (4, _("Tug of War"), _("Fight with the other player for life.")),
               (5, _("Great Attack"), _("Only greats make the bar go up."))]
