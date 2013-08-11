# A bunch of font-related effects routines used all over pydance.

import pygame
import random
from constants import *
from fonttheme import FontTheme

# Text that wraps at a particular width (in pixels), automatically. No
# limit is placed on height.
class WrapFont(object):
  def __init__(self, font, width):
    self._font = font
    self._width = width
    self._ls = self._font.get_linesize()
    self._ds = - self._font.get_descent()

  def get_linesize(self): return self._ls

  # Return the number of lines a bit of text will require. indent lets you
  # set an indent (in characters) that will go before all lines after the
  # first.
  def lines(self, text, indent = ""):
    lines = 1
    words = text.split()
    start = 0
    for i in range(len(words)):
      if start == 0: line = " ".join(words[start:i+1])
      else: line = indent + " ".join(words[start:i+1])
      if self._font.size(line)[0] > self._width:
        lines += 1
        start = i
    return lines

  def size(self, text, indent = ""):
    return [self._width, self.lines(text, indent) * self._ls + self._ds]

  # Render some text, optionally with shadowing, indentation, and centering.
  # Using indentation with centered display is untested.
  def render(self, text, color = [255, 255, 255], shdw = True, indent = "",
             centered = False):
    lines = []
    words = text.split()
    start = 0
    for i in range(len(words)):
      if start == 0: line = " ".join(words[start:i+1])
      else: line = indent + " ".join(words[start:i+1])
      if self._font.size(line)[0] > self._width:
        if start == 0: line = " ".join(words[start:i])
        else: line = indent + " ".join(words[start:i])
        if shdw: t = shadow(line, self._font, color)
        else: t = self._font.render(line, True, color)
        lines.append(t)
        start = i
    if start == 0: line = " ".join(words[start:])
    else: line = indent + " ".join(words[start:])
    if shdw: t = shadow(line, self._font, color)
    else: t = self._font.render(line, True, color)
    lines.append(t)        

    image = pygame.Surface([self._width, len(lines) * self._ls + self._ds],
                           SRCALPHA, 32)
    image.fill([0, 0, 0, 0])
    for i, line in enumerate(lines):
      if centered:
        r = line.get_rect()
        r.centerx = self._width / 2
        r.y = i * self._font.get_linesize()
        image.blit(line, r)
      else:
        image.blit(line, [0, i * self._font.get_linesize()])
    return image

# EMBFADE - does a 3d emboss-like effect
def embfade(textstring, font, amount, displaysize, trgb = [255, 255, 255]):
  displaysurface = pygame.Surface(displaysize)
  for i in range(amount):
    text = font.render(textstring, True, [c / (i + 1) for c in trgb])
    displaysurface.blit(text, [i, i])
  return displaysurface

# Do a simple drop-shadow on text, with a darker color offset by a certain
# number of pixels.
def shadow(text, font, color, offset = 1, color2 = None):
  if color2 == None: color2 = [c / 9 for c in color]
  t1 = font.render(text, True, color)
  t2 = font.render(text, True, color2)
  s = pygame.Surface([i + offset for i in t1.get_size()], SRCALPHA, t1)
  s.blit(t2, [offset, offset])
  s.blit(t1, [0, 0])
  return s

# SHADEFADE - does a 3d dropshadow-like effect
def shadefade(textstring, font, amount, displaysize, trgb=(255,255,255)):
  displaysurface = pygame.Surface(displaysize, SRCALPHA, 32)
  for i in range(amount - 1, 0, -1):
    text = font.render(textstring, True, [c / i for c in trgb])
    displaysurface.blit(text, [i, i])
  return displaysurface

# The rotating text on the main menu screen
class TextZoomer(object):
  def __init__(self, text, font, size, fore, back):
    self.tempsurface = pygame.surface.Surface(size)
    self.back = back
    self.fore = fore
    self.size = size
    self.font = font

    self.reset()
    self.zoomtext = text
    self.textrendered = 0

  def reset(self):
    self.mrangle = 0
    self.textrendered = 0

  def iterate(self):
    self.mrangle += 2

    zoomsurface = pygame.transform.scale(self.tempsurface,
                                         [self.size[0] + 16,
                                          self.size[1] + 16])
    zoomsurface = pygame.transform.rotate(self.tempsurface,self.mrangle)
    zoomsurface.set_alpha(120)
    zsrect = zoomsurface.get_rect()
    zsrect.center = [self.size[0] / 2, self.size[1] / 2]
    self.tempsurface.fill(self.back)
    self.tempsurface.blit(zoomsurface, zsrect)
    text = self.font.render(self.zoomtext, True, self.fore)
    trect = text.get_rect()
    self.tempsurface.blit(text, [320 - (trect.size[0]/2),
                                 32 - (trect.size[1]/2)])

# From the PCR (http://www.pygame.org/pcr/progress_text/index.php),
# by Pete Shinners.
class TextProgress(object):
  def __init__(self, font, message, color, bgcolor):
    self.font = font
    self.message = message
    self.color = color
    self.bgcolor = bgcolor
    self.offcolor = [c^40 for c in color]
    self.notcolor = [c^0xFF for c in color]
    self.text = font.render(message, False, [255, 0, 0], self.notcolor)
    self.text.set_colorkey(1, RLEACCEL)
    self.outline = self.textHollow(font, message, color)
    self.bar = pygame.Surface(self.text.get_size())
    self.bar.fill(self.offcolor)
    width, height = self.text.get_size()
    stripe = Rect(0, height/2, width, height/4)
    self.bar.fill(color, stripe)
    self.ratio = width / 100.0

  def textHollow(self, font, message, fontcolor):
    base = font.render(message, False, fontcolor, self.notcolor)
    size = base.get_width() + 2, base.get_height() + 2
    img = pygame.Surface(size, 16)
    img.fill(self.notcolor)
    base.set_colorkey(0, RLEACCEL)
    img.blit(base, [0, 0])
    img.blit(base, [2, 0])
    img.blit(base, [0, 2])
    img.blit(base, [2, 2])
    base.set_colorkey(0, RLEACCEL)
    base.set_palette_at(1, self.notcolor)
    img.blit(base, [1, 1])
    img.set_colorkey(self.notcolor, RLEACCEL)
    return img

  def render(self, percent = 50):
    surf = pygame.Surface(self.text.get_size())
    if percent < 100:
      surf.fill(self.bgcolor)
      surf.blit(self.bar, [0, 0], [0, 0, percent * self.ratio, 100])
    else:
      surf.fill(self.color)
    surf.blit(self.text, [0, 0])
    surf.blit(self.outline, [-1, -1])
    surf.set_colorkey(self.notcolor, RLEACCEL)
    return surf

# Replace as much of the middle of the string with "..." as is necessary
# to fit it into width.
def render_outer(string, width, font):
  s = string
  if font.size(string)[0] <= width: return string
  center = len(string) / 2
  remove = 0
  while font.size(s)[0] > width:
    remove += 1
    left = center + (-remove)/2
    right = center + remove/2
    s = string[:left] + "..." + string[right:]
  return s

# Text that zooms in, then out.
# FIXME: Put some timer controls on this
class zztext(pygame.sprite.Sprite):
  def __init__(self, text, x, y, basesize, fontfn=None):
    pygame.sprite.Sprite.__init__(self)
    self.cent = [x, y]
    self.zoom = 0
    self.baseimage = pygame.surface.Surface([320, 24])
    self.rect = self.baseimage.get_rect()
    self.rect.center = self.cent

    for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 15):
      font = pygame.font.Font(fontfn, int((9 + i) / 9.0 * basesize))
      gtext = font.render(text, True, [i * 16] * 3)
      textpos = gtext.get_rect()
      textpos.center = [160, 12]
      self.baseimage.blit(gtext, textpos)

    self.baseimage.set_colorkey(self.baseimage.get_at([0, 0]), RLEACCEL)
    self.image = self.baseimage

  def zin(self):
    self.zoom = 1
    self.zdir = 1
      
  def zout(self):
    self.zoom = 31
    self.zdir = -1
      
  def update(self, time):
    if 32 > self.zoom > 0:
      self.image = pygame.transform.rotozoom(self.baseimage, 0, self.zoom/32.0)
      self.rect = self.image.get_rect()
      self.rect.center = self.cent
      self.zoom += self.zdir
    else:
      self.zdir = 0
