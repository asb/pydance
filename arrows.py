import os
import random
import pygame

# FIXME: Mark hidden attributes appropriately.

from constants import *

# Base arrow class. Hold arrows and the regular arrows both extend this.
class AbstractArrow(pygame.sprite.Sprite):

  # Assist mode sound samples. FIXME - we need sounds for the other
  # directions.
  samples = {}
  for d in ["u", "d", "l", "r"]:
    samples[d] = pygame.mixer.Sound(os.path.join(sound_path,
                                                 "assist-%s.ogg" % d))

  # arrow is the actual graphical arrow from gfxtheme.py.
  # beat is the beat this arrow is to be "hit" on.
  # secret is the kind of secret arrow this is (if any)
  # player is the Player object this arrow belongs to.
  # song is a SongData object; we only need it to get the 'battle'
  # attribute, which means we should probably merge the player and
  # song-wide configuration options. FIXME
  def __init__(self, arrow, beat, secret, player, song):
    pygame.sprite.Sprite.__init__(self)

    self.dir = arrow.dir
    # Barf. Sometimes beat means 16th notes, for historical
    # reasons. Here it sanely means quarter notes.
    self.endbeat = beat / 4
    self.arrow = arrow

    self.image = self.arrow.get_image(0).convert()
    self.baseimage = self.image
    self.rect = self.image.get_rect()
    self.rect.left = self.arrow.left

    # It's probably possible to make player store this somehow so we
    # can do this much more quickly.
    self.width = player.game.width
    self.battle = song.battle
    self.secret = secret

    # This (mainconfig lookup) is slow.
    if mainconfig['assist'] == 2 and self.dir in ArrowSprite.samples:
      self.sample = ArrowSprite.samples[self.dir]
    elif mainconfig['assist']:
      self.sample = ArrowSprite.samples["d"]
    else: self.sample = None

    if player.scrollstyle == 2:
      self.top = 240 - player.game.width / 2
      self.bottom = random.choice([748, -276])
      if self.top < self.bottom:
        self.vector = 1
        self.suddenzone = 480
        self.hiddenzone = 240 - player.game.width / 2
      else:
        self.vector = -1
        self.suddenzone = -64
        self.hiddenzone = 240 - player.game.width / 2
    elif player.scrollstyle == 1:
      self.vector = -1
      self.top = 352
      self.bottom = -64
      self.suddenzone = -64
      self.hiddenzone = 352
    else:
      self.vector = 1
      self.top = 64
      self.bottom = 480
      self.suddenzone = 480
      self.hiddenzone = 64

    if player.fade & 1: # Sudden, fade in late.
      self.suddenzone -= self.vector * 160
    if player.fade & 2: # Hidden, fade out early.
      self.hiddenzone += self.vector * 160

    self.fade = player.fade

    self.spin = player.spin
    self.scale = player.scale
    if player.target_bpm is None:
      self.speed = player.speed
      self.target_bpm = None
    else:
      self.target_bpm = float(player.target_bpm)

    self.accel = player.accel
    self.battle = song.battle

    self.diff = self.top - self.bottom

    if self.target_bpm is None:
      # NB - Although "beats" refers to 16th notes elsewhere, this refers to
      # "proper" beats, meaning a quarter note.
      self.totalbeats = abs(self.diff) / 64.0
    else:
      self.totaltime = abs(self.diff) / 64.0 / self.target_bpm * 60

    # "goal" locations are used for battle mode (and possibly
    # elsewhere later), meaning the arrow slowly moves towards that
    # location as it also approaches top on the other axis.
    self.goalcenterx = self.rect.centerx
    if self.battle:
      # This expression needs FIXMEing. We should be able to
      # precalcuate this value since it only relies on information in
      # the GameType object.
      self.rect.left = 320 - player.game.battle_lefts[self.dir]
      self.origcenterx = self.centerx = self.rect.centerx
    else: self.centerx = self.rect.centerx = self.goalcenterx

  # Figure out what our alpha channel should be based on where we are
  # on the scrreen.
  def set_alpha(self, curtime, beatsleft, top, factor):
    alp = 256

    # Blinking
    # V*V*(3-V-V), V is a value 0-1, flattens out the curve around 0 and 1
    if self.fade == 4:
      a = abs((beatsleft % 2) - 1) # Python supports % for floats. Crazy.
      alp = int(alp * (a * a * (3 - a - a)))

    # Sudden/hidden checking.
    if self.top < self.bottom: 
      if top > self.suddenzone:
        alp = 256 - 4 * (top - self.suddenzone)
      elif self.rect.top < self.hiddenzone:
        alp = 256 - 4 * (self.hiddenzone - top)
    else:
      if top < self.suddenzone:
        alp = 256 - 4 * (self.suddenzone - top)
      elif top > self.hiddenzone:
        alp = 256 - 4 * (top - self.hiddenzone)

    if alp > 256: alp = 256
    elif alp < 0: alp = 0

    # "Faint" mode. If secret arrows are off or totally hidden,
    # a sprite isn't even initialized for them.
    if self.secret: alp /= 5

    alp = int(alp * factor)

    # NB - Making a new surface, then blitting the image in place, is 20%
    # slower than calling image.convert() (and is longer to type).
    # We should do some real benchmarks later to verify this.
    # Also, once we *have* a converted image, we can do whatever we
    # want to it... there's no reason to convert it again. FIXME
    if alp < 255:
      self.image = self.image.convert()
      self.image.set_alpha(alp)

  def update(self, curtime, curbpm, beat):
    if self.target_bpm is not None:
      self.speed = self.target_bpm / curbpm
    self.image = self.arrow.get_image(beat)
    self.baseimage = self.image
    self.rect = self.image.get_rect()
    self.rect.left = self.arrow.left

    if self.sample and curtime >= self.endtime:
      self.sample.play()
      self.sample = None

  # Depending on our settings, rotate, move, or change the image size
  # appropriately.
  def scale_spin_battle(self, image, top, pct):
    if self.scale != 1:
      if self.scale < 1: # Shrink
        new_size = [max(0, int(pct * i)) for i in image.get_size()]
      else: # Grow
        new_size = [max(0, int(i - pct * i)) for i in image.get_size()]
      image = pygame.transform.scale(image, new_size)
    
    if self.spin:
      image = pygame.transform.rotate(image, top - 64)

    rect = image.get_rect()
    rect.top = top

    if self.battle:
      if pct > 4.5 / 6: rect.centerx = self.origcenterx
      elif pct > 2.0 / 6:
        p = (pct - 2.0/6) / (2.5 / 6)
        rect.centerx = (1 - p) * self.goalcenterx + p * self.origcenterx
      else: rect.centerx = self.goalcenterx
    else: rect.centerx = self.centerx

    # Although the image size can be 0x!0, it can't ever be !0x0,
    # because X >= Y always.
    if image.get_size()[0] != 0:
      image.set_colorkey(image.get_at([0, 0]))

    return rect, image

  def kill(self):
    pygame.sprite.Sprite.kill(self)
    if self.sample: self.sample.play()

# The basic arrow.
class ArrowSprite(AbstractArrow):
  def __init__ (self, arrow, beat, secret, endtime, player, song):
    AbstractArrow.__init__(self, arrow, beat, secret, player, song)
    self.hold = False
    self.endtime = endtime

  def update(self, curtime, curbpm, curbeat, judge):
    AbstractArrow.update(self, curtime, curbpm, curbeat)

    beatsleft = self.endbeat - curbeat
    
    if self.target_bpm is None:
      if curbeat > self.endbeat + 1:
        self.kill()
        return

      if self.accel == 1:
        p = max(0, -1 / self.totalbeats * (beatsleft * self.speed - self.totalbeats))
        speed = self.speed * (p + 1)
      elif self.accel == 2:
        p = min(1, -1 / self.totalbeats * (beatsleft * self.speed - self.totalbeats))
        speed = self.speed * (p * -0.5 + 1)
      else: speed = self.speed

      # The second term (self.vector * ...) is a simplication of
      # int(beatsleft * speed * self.diff / self.beatsleft).
      top = self.top + self.vector * int(beatsleft * speed * 64)
    else:
      if curtime > self.endtime + 60.0/curbpm:
        self.kill()
        return

      timeleft = self.endtime - curtime
      
      if self.accel == 1:
        p = 1 + max(0, -1 / self.totaltime * (timeleft - self.totaltime))
      elif self.accel == 2:
        p = 1 - 0.5 * min(1, -1 / self.totaltime * (timeleft - self.totaltime))
      else: p = 1

      # The second term (self.vector * ...) is the number of beats
      # corresponding to the amount of time left at the target bpm.
      top = self.top + self.vector * int(p*timeleft*self.target_bpm/60.0 * 64)

    if top > 480: top = 480

    pct = abs(float(top - self.top) / self.diff)

    self.rect, self.image = self.scale_spin_battle(self.baseimage, top, pct)
    self.set_alpha(curtime, beatsleft, top, 1)

# Hold arrows have a start time and an end time, instead of just a
# "hit" time.
class HoldArrowSprite(AbstractArrow):
  def __init__ (self, arrow, beats, secret, times, player, song):
    AbstractArrow.__init__(self, arrow, beats[1], secret, player, song)
    self.timef1 = self.endtime = times[1]
    self.hold = True
    self.timef2 = times[2]
    self.endbeat1 = beats[0] / 4
    self.endbeat2 = beats[1] / 4
    if self.timef2 is None: self.timef2 = self.timef1 # ?

    self.broken = False
    self._broken_at = -1

  # Mark the time the arrow was broken at.
  def broken_at(self, time, judge):
    if self._broken_at == -1: self._broken_at = time
    elif time - self._broken_at > judge.ok_time: self.broken = True
    return self.broken

  # The arrow is re-held.
  def held(self):
    self._broken_at = -1

  def update(self, curtime, curbpm, beat, judge):
    AbstractArrow.update(self, curtime, curbpm, 0)

    beatsleft_top = self.endbeat1 - beat
    beatsleft_bot = self.endbeat2 - beat

    if self.target_bpm is None:
      if beat > self.endbeat2:
        self.kill()
        return

      c = self.image.get_colorkey()
      self.top_image = pygame.surface.Surface([self.width, self.width / 2])
      self.top_image.fill(c)
      self.top_image.blit(self.image, [0, 0])

      self.bottom_image = pygame.surface.Surface([self.width, self.width / 2])
      self.bottom_image.fill(c)
      self.bottom_image.blit(self.image, [0, -self.width / 2])

      self.center_image = pygame.surface.Surface([self.width, 1]) 
      self.center_image.fill(c)
      self.center_image.blit(self.image, [0, -self.width / 2 + 1])

      if self.accel == 1:
        nootb = -1 / self.totalbeats
        p = max(0, nootb * (beatsleft_top * self.speed - self.totalbeats))
        speed_top = self.speed * (p + 1)
        p = max(0, nootb * (beatsleft_bot * self.speed - self.totalbeats))
        speed_bottom = self.speed * (p + 1)
      elif self.accel == 2:
        nootb = -1 / self.totalbeats
        p = min(1, nootb * (beatsleft_top * self.speed - self.totalbeats))
        speed_top = self.speed * (p * -0.5 + 1)
        p = min(1, nootb * (beatsleft_bot * self.speed - self.totalbeats))
        speed_bottom = self.speed * (p * -0.5 + 1)
      else: speed_top = speed_bottom = self.speed

      # See the notes in ArrowSprite about the derivation of this.
      if self.bottom > self.top:
        top = self.top + self.vector * int(beatsleft_top * speed_top * 64)
        bottom = self.top + self.vector * int(beatsleft_bot * speed_bottom * 64)
      else:
        top = self.top + self.vector * int(beatsleft_bot * speed_bottom * 64)
        bottom = self.top + self.vector * int(beatsleft_top * speed_top * 64)

      if bottom > 480: bottom = 480
      if top > 480: top = 480

      if self.top < self.bottom:
        bottom = max(self.top, bottom)
        top = max(self.top, top)
      else:
        bottom = min(self.top, bottom)
        top = min(self.top, top)
    else:
      if curtime > self.timef2:
        self.kill()
        return

      timeleft_top=self.timef1-curtime
      timeleft_bot=self.timef2-curtime
      
      c = self.image.get_colorkey()
      self.top_image = pygame.surface.Surface([self.width, self.width / 2])
      self.top_image.fill(c)
      self.top_image.blit(self.image, [0, 0])

      self.bottom_image = pygame.surface.Surface([self.width, self.width / 2])
      self.bottom_image.fill(c)
      self.bottom_image.blit(self.image, [0, -self.width / 2])

      self.center_image = pygame.surface.Surface([self.width, 1]) 
      self.center_image.fill(c)
      self.center_image.blit(self.image, [0, -self.width / 2 + 1])

      if self.accel == 1:
        noott = -1 / self.totaltime
        p_top = 1 + max(0, noott * (timeleft_top - self.totaltime))
        p_bottom = 1 + max(0, noott * (timeleft_bot - self.totaltime))
      elif self.accel == 2:
        noott = -1 / self.totaltime
        p_top = 1 + -0.5 * min(1, noott * (timeleft_top - self.totaltime))
        p_bottom = 1 - 0.5 * min(1, noott * (timeleft_bot - self.totaltime))
      else: p_top = p_bottom = 1

      # See the notes in ArrowSprite about the derivation of this.
      if self.bottom > self.top:
        top = self.top + self.vector * int(p_top*timeleft_top * self.target_bpm/60.0 * 64)
        bottom = self.top + self.vector * int(p_bottom*timeleft_bot * self.target_bpm/60.0 * 64)
      else:
        top = self.top + self.vector * int(p_top*timeleft_bot * self.target_bpm/60.0 * 64)
        bottom = self.top + self.vector * int(p_bottom*timeleft_top * self.target_bpm/60.0 * 64)

      if bottom > 480: bottom = 480
      if top > 480: top = 480

      if self.top < self.bottom:
        bottom = max(self.top, bottom)
        top = max(self.top, top)
      else:
        bottom = min(self.top, bottom)
        top = min(self.top, top)
      

    pct = abs(float(top - self.top) / self.diff)
    
    holdsize = abs(bottom - top)
    if holdsize < 0: holdsize = 0
    image = pygame.Surface([self.width, holdsize + self.width])
    h_img = pygame.transform.scale(self.center_image, [self.width, holdsize])
    image.blit(h_img, [0, self.width / 2])
    image.blit(self.top_image, [0, 0])
    image.blit(self.bottom_image, [0, holdsize + self.width / 2])
    image.set_colorkey(c)

    self.rect, self.image = self.scale_spin_battle(image, top, pct)
    if self.broken: f = 0.33
    elif self._broken_at != -1:
      p = (curtime - self._broken_at) / judge.ok_time
      f = 1.0 * (1 - p) + 0.33 * p
    else: f = 1
    if self.top < self.bottom:
      self.set_alpha(curtime, beatsleft_bot, top, f)
    else:
      self.set_alpha(curtime, beatsleft_top, bottom, f)
