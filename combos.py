# Combo counting.

import pygame

from listener import Listener
from constants import *
from fonttheme import FontTheme

class AbstractCombo(Listener, pygame.sprite.Sprite):

  def __init__(self, playernum, game):
    pygame.sprite.Sprite.__init__(self)
    self._sticky = mainconfig['stickycombo']
    self._lowcombo = mainconfig['lowestcombo']
    self.combo = 0
    self._laststep = 0
    self._centerx = game.sprite_center + (game.player_offset * playernum)
    self._top = 320
    
    fonts = []
    fontfn, basesize = FontTheme.Dance_combo_display
    for x in range(11, 0, -1):
      fonts.append(pygame.font.Font(fontfn, basesize+int(x*1.82/28*basesize)))

    # Store each digit individually, to avoid long text rendering
    # times in the middle of the game. FIXME: This breaks above 9999
    # combo currently; the PCR has code for the same trick that scales
    # infinitely.
    self._words = []
    for f in fonts:
      render = []
      for w in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'x COMBO']:
        img1 = f.render(w, 1, [16, 16, 16])
        img2 = f.render(w, 1, [224, 224, 224])
        img3 = pygame.Surface(img1.get_size())
        img3.blit(img1, [-2, 2])
        img3.blit(img1, [2, -2])
        img3.blit(img2, [0, 0])
        img3.set_colorkey(img3.get_at([0, 0]), RLEACCEL)
        render.append(img3)
      self._words.append(render)
    self._space = pygame.surface.Surface([0, 0])
    self.image = self._space

  def update(self, curtime):
    self._laststep = min(curtime, self._laststep)
    steptimediff = curtime - self._laststep

    if steptimediff < 0.36 or self._sticky:
      self._drawcount = self.combo
      drawsize = min(int(steptimediff * 50), len(self._words) - 1)
      if drawsize < 0: drawsize = 0
    else:
      self._drawcount = 0

    if self._drawcount >= self._lowcombo:
      render = self._words[drawsize]
      width = render[-1].get_width()
      thousands = self._drawcount / 1000
      hundreds = self._drawcount / 100
      tens = self._drawcount / 10
      ones = self._drawcount % 10
      if thousands:
        thousands = render[thousands % 10]
        width += thousands.get_width()      
      if hundreds:
        hundreds = render[hundreds % 10]
        width += hundreds.get_width()
      if tens:
        tens = render[tens % 10]
        width += tens.get_width()
      ones = render[ones]
      width += ones.get_width()
      height = render[-1].get_height()
      self.image = pygame.surface.Surface([width, height])
      self.image.set_colorkey(ones.get_at([0, 0]), RLEACCEL)
      left = 0		      
      if thousands:
        self.image.blit(thousands, [left, 0])
        left+= thousands.get_width()
      if hundreds:
        self.image.blit(hundreds, [left, 0])
        left += hundreds.get_width()
      if tens:
        self.image.blit(tens, [left, 0])
        left += tens.get_width()
      self.image.blit(ones, [left, 0])
      left += ones.get_width()
      r = self.image.blit(render[-1], [left, 0])
    else :
      self.image = self._space

    self.rect = self.image.get_rect()
    self.rect.top = self._top
    self.rect.centerx = self._centerx

# Breaks the combo on anything not a marvelous, perfect, or great.
class NormalCombo(AbstractCombo):
  def stepped(self, pid, dir, curtime, etime, rating, combo):
    if rating is None: return
    self._laststep = curtime
    self.combo += { "V": 1, "P": 1, "G": 1 }.get(rating, -self.combo)

# Breaks the combo on anything less than a great, but also doesn't
# increase it for great.
class OniCombo(AbstractCombo):
  def stepped(self, pid, dir, curtime, etime, rating, combo):
    if rating is None: return
    self._laststep = curtime
    self.combo += { "V": 1, "P": 1, "G": 0 }.get(rating, -self.combo)

# Pump It Up-style combo; okays add to your combo too.
class PumpCombo(AbstractCombo):
  def stepped(self, pid, dir, curtime, etime, rating, combo):
    if rating is None: return
    self._laststep = curtime
    self.combo += { "V": 1, "P": 1, "G": 1, "O": 1 }.get(rating, -self.combo)

combos = [NormalCombo, OniCombo, PumpCombo]
combo_opt = [
  (0, _("Normal"), _("Greats or better increase a combo")),
  (1, _("Oni-style"), _("Greats don't increase a combo, but also don't break it")),
  (2, _("Pump It Up"), _("Okays or better increase a combo"))]
