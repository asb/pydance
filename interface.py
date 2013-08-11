# GUI widgets and routines common to several screens.

import os
import math
import pygame
import colors
import fontfx
import random


from constants import *
from fonttheme import FontTheme
from i18n import *

# Make an outlined box. The size is given without the 4 pixel border.
# This usually gets alphaed before stuff gets put in it.
def make_box(color = [111, 255, 148], size = [130, 40]):
  s = pygame.Surface([size[0] + 8, size[1] + 8], SRCALPHA, 32)
  s.fill(color + [100])
  r = s.get_rect()
  for c in [[255, 255, 255, 170], [212, 217, 255, 170],
            [255, 252, 255, 170], [104, 104, 104, 170]]:
    pygame.draw.rect(s, c, r, 1)
    r.width -= 2
    r.height -= 2
    r.top += 1
    r.left += 1
  return s

def folder_name(name, type):
  if type == "mix": return name
  elif type == "bpm": return "%s BPM" % _(name)
  else: 
    return "%s: %s" % (_(type).capitalize(), name)

def load_banner(filename, box = True):
  banner = pygame.image.load(filename)
  size = banner.get_size()
  if size <= (100, 100): # Parapara-style... no idea what to do.
    return banner, None
  elif size == (177, 135): # KSF-style 1
    return banner, None
  elif size == (300, 200): # KSF-style 2
    banner.set_colorkey(banner.get_at([0, 0]), RLEACCEL)
    return banner, None
  elif abs(size[0] - size[1]) < 3: # "Square", need to rotate.
    banner = banner.convert()
    banner.set_colorkey(banner.get_at([0, 0]), RLEACCEL)
    return pygame.transform.rotozoom(banner, -45, 1.0), [51, 50, 256, 80]
  else: # 256x80, standard banner, I hope.
    if size != (256, 80): banner = pygame.transform.scale(banner, [256, 80])
    if box:
      b2 = make_box([0, 0, 0], [256, 80])
      b2.blit(banner, [4, 4])
    else: b2 = banner
    return b2, None

# Just display a text string, within a specific width.
class TextDisplay(pygame.sprite.Sprite):
  def __init__(self, purpose, size, midleft, str = " "):
    pygame.sprite.Sprite.__init__(self)
    self._text = str
    self._purpose = purpose
    self._size = size
    self._midleft = midleft
    self._render()

  def _render(self):
    font = FontTheme.font(self._purpose, self._text, self._size[0])
    img = fontfx.shadow(self._text, font, [255, 255, 255])
    self.image = img
    self.rect = self.image.get_rect()
    self.rect.midleft = self._midleft

  def set_text(self, text):
    self._text = text
    self._render()

# Moving BPM display.
class BPMDisplay(pygame.sprite.Sprite):
  def __init__(self, font, center, song = None):
    pygame.sprite.Sprite.__init__(self)
    self._last_update = pygame.time.get_ticks()
    self._font = font
    self._center = center
    self.set_song(song)
    self._render()
    self._color = [255, 255, 255]
    self._bpm_range = [0, 1] # normally [min, range]

  def _render(self):
    if self._bpm:
      w = 100
      h = self._font.get_linesize() * 2 - self._font.get_descent()
      self.image = pygame.Surface([w, h], SRCALPHA, 32)
      self.image.fill([0, 0, 0, 0])
      t1 = fontfx.shadow("BPM:", self._font, [255, 255, 255])
      t2 = fontfx.shadow("%d" % int(self._bpm), self._font, self._color)
      r1 = t1.get_rect()
      r1.midtop = [50, 0]
      r2 = t2.get_rect()
      r2.midtop = [50, self._font.get_linesize()]
      self.image.blit(t1, r1)
      self.image.blit(t2, r2)
    else: self.image = pygame.Surface([0, 0])
    self.rect = self.image.get_rect()
    self.rect.center = self._center

  def set_song(self, song):
    if song and "bpmdisplay" in song.info:
      bpms = song.info["bpmdisplay"]
      if bpms[0] == -1:
        self._bpm_idx = -1
        self._bpm = 150
        self._bpms = []
      else:
        self._bpm = bpms[0]
        self._bpms = bpms
        self._bpm_idx = 1 % len(self._bpms)
        self._bpm_range = [min(bpms), max(max(bpms) - min(bpms), 0.00001)]
        if len(bpms) > 1:
          p = (self._bpm - self._bpm_range[0]) / self._bpm_range[1]
          self._color = [255 * math.sqrt(p), 255 * math.sqrt(1 - p), 0]
        else:
          self._color = [255, 255, 255]
      self._last_update = pygame.time.get_ticks()
      self._render()
    else:
      self._bpms = []
      self._bpm_idx = 0
      self._bpm = 0
      self._last_update = pygame.time.get_ticks()
      self._render()

  def update(self, time):
    t = time - self._last_update
    if len(self._bpms) == 0:
      if self._bpm_idx and t > 50:
        self._last_update = time
        self._bpm = random.randrange(50, 300)
        self._render()
    elif t > 3000:
      self._bpm_idx = (self._bpm_idx + 1) % len(self._bpms)
      self._bpm = self._bpms[self._bpm_idx - 1]
      self._last_update = time
      self._render()
    elif t > 2000 and len(self._bpms) > 1:
      t -= 2000
      p = t / 1000.0
      self._bpm = (p * self._bpms[self._bpm_idx] +
                   (1 - p) * self._bpms[self._bpm_idx - 1])
      if len(self._bpms) > 1: # and self._bpm_range[0] > 0:
        p = (self._bpm - self._bpm_range[0]) / self._bpm_range[1]
        self._color = [255 * math.sqrt(p), 255 * math.sqrt(1 - p), 0]
      self._render()

# Scroll an image looping vertically, from the course selection course list.
class ScrollingImage(pygame.sprite.Sprite):
  def __init__(self, image, topleft, height):
    pygame.sprite.Sprite.__init__(self)
    self._height = height
    self._image = image
    self._topleft = topleft
    self.set_image(image)

  def set_image(self, image):
    if image.get_height() > self._height:
      self._scrolling = True
      self._start = pygame.time.get_ticks() + 2000
      self.image = pygame.Surface([image.get_width(), self._height],
                                  SRCALPHA, 32)
      self._image = image
      self.image.blit(image, [0, 0])
      self.update(pygame.time.get_ticks())
    else:
      self._scrolling = False
      self.image = image
      self._image = None
      self.rect = self.image.get_rect()
      self.rect.topleft = self._topleft

  def update(self, time):
    if self._scrolling and self._start < time:
      self.image.fill([0, 0, 0, 0])
      y = int(30 * ((time - self._start) / 1000.0))
      y %= self._image.get_height()
      self.image.blit(self._image, [0, -y])
      self.image.blit(self._image, [0, self._image.get_height() - y])

# Display an image.
class ImageDisplay(pygame.sprite.Sprite):
  def __init__(self, image, topleft):
    pygame.sprite.Sprite.__init__(self)
    self._topleft = topleft
    self.set_image(image)

  def set_image(self, image):
    self.image = image
    self.rect = image.get_rect()
    self.rect.topleft = self._topleft

# Flip an image around like it's being rotated when it changes, used on
# the gameselect screen.
class FlipImageDisplay(pygame.sprite.Sprite):
  def __init__(self, filename, center):
    pygame.sprite.Sprite.__init__(self)
    self._cache = {None: pygame.Surface([0, 0])}
    self._center = center
    self._image = self._cache[None]
    self._oldimage = self._cache[None]
    self._changed_time = pygame.time.get_ticks() - 200
    self.set_image(filename)

  def set_image(self, filename):
    t = pygame.time.get_ticks()
    if t - self._changed_time < 200:
      self._changed_time = t - (200 - (t - self._changed_time))
    elif t - self._changed_time < 400:
      self._changed_time = t - (400 - (t - self._changed_time))
    else:
      self._changed_time = t

    if isinstance(filename, str) or filename is None:
      if filename in self._cache:
        self._image = self._cache[filename]
      else:
        self._image = pygame.image.load(os.path.join(image_path, filename))
        self._cache[filename] = self._image
    else:
      self._image = filename

  def update(self, time):
    if time - self._changed_time > 400:
      self._oldimage = self._image
      self.image = self._image
    elif time - self._changed_time > 200:
      p = (time - self._changed_time - 200) / 200.0
      x = int(p * self._image.get_width())
      y = self._image.get_height()
      self.image = pygame.transform.scale(self._image, [x, y])
    else:
      p = 1 - (time - self._changed_time) / 200.0
      x = max(0, int(p * self._oldimage.get_width()))
      y = self._oldimage.get_height()
      self.image = pygame.transform.scale(self._oldimage, [x, y])
    self.rect = self.image.get_rect()
    self.rect.center = self._center

# Crossfading help text along the top of the screen.
class HelpText(pygame.sprite.Sprite):
  def __init__(self, strs, color, bgcolor, font, center):
    pygame.sprite.Sprite.__init__(self)
    self._idx = -1
    self._strings = [(s, font.render(s, True, color, bgcolor).convert())
                     for s in strs]
    self._center = center
    self._start = pygame.time.get_ticks()
    self._fade = -1
    self._bgcolor = bgcolor
    self._end = -1
    self.update(self._start)

  def update(self, time):
    time -= self._start
    # Time to switch to the next bit of text.
    if time > self._end:
      self._idx = (self._idx + 1) % len(self._strings)
      self.image = self._strings[self._idx][1]
      self.image.set_alpha(255)
      self._fade = time + 100 * len(self._strings[self._idx][0])
      self._end = self._fade + 750

    # There's a .75 second delay during which text crossfades.
    elif time > self._fade:
      p = (time - self._fade) / 750.0
      s1 = self._strings[self._idx][1]
      s1.set_colorkey(s1.get_at([0, 0]))
      s1.set_alpha(int(255 * (1 - p)))
      
      i = (self._idx + 1) % len(self._strings)
      s2 = self._strings[i][1]
      s2.set_colorkey(s2.get_at([0, 0]))
      s2.set_alpha(int(255 * p))

      h = max(s1.get_height(), s2.get_height())
      w = max(s1.get_width(), s2.get_width())
      self.image = pygame.Surface([w, h], 0, 32)
      self.image.fill(self._bgcolor)
      self.image.set_colorkey(self.image.get_at([0, 0]))
      r = s1.get_rect()
      r.center = self.image.get_rect().center
      self.image.blit(s1, r)
      r = s2.get_rect()
      r.center = self.image.get_rect().center
      self.image.blit(s2, r)

    self.image.set_colorkey(self.image.get_at([0, 0]))
    self.rect = self.image.get_rect()
    self.rect.center = self._center

# Flashy indicator for showing current menu position.
class ActiveIndicator(pygame.sprite.Sprite):
  def __init__(self, topleft, width = 220, height = 26):
    pygame.sprite.Sprite.__init__(self)
    img = pygame.image.load(os.path.join(image_path, "indicator.png"))
    img = img.convert()
    img.set_colorkey(img.get_at([0, 0]))

    left, mid, right = self._left_mid_right(img)
    bar = pygame.Surface([width, left.get_height()])
    bar.blit(left, [0, 0])
    bar.blit(pygame.transform.scale(mid, [width - 10, bar.get_height()]),
             [5, 0])
    bar.blit(right, [width - 5, 0])
    bar.set_colorkey(bar.get_at([0, 0]))

    self.image = pygame.Surface([width, height + bar.get_height()])
    self.image.blit(bar, [0, 0])
    self.image.blit(pygame.transform.rotate(bar, 180), [0, height])
    self.image.set_colorkey(self.image.get_at([0, 0]))

    self.rect = self.image.get_rect()
    self.rect.topleft = topleft

  # Extract the left 5px, right 5px, and middle parts of an image.
  def _left_mid_right(self, img):
    left = pygame.Surface([5, img.get_height()])
    left.blit(img, [0, 0])

    right = pygame.Surface([5, img.get_height()])
    right.blit(img, [5 - img.get_width(), 0])

    mid = pygame.Surface([img.get_width() - 10, img.get_height()])
    mid.blit(img, [-5, 0])

    return left, mid, right
                         
  def move(self, pt): self.rect.topleft = pt

  def update(self, time):
    self.image.set_alpha(int(255 * (0.3 + (math.sin(time / 720.0)**2 / 3.0))))

# Box to indicate the current difficulty level and rating.
class DifficultyBox(pygame.sprite.Sprite):
  def __init__(self, center):
    pygame.sprite.Sprite.__init__(self)
    self._topleft = [center[0]-65, center[1]-20]

  def set(self, diff, color, feet, grade):
    f = FontTheme.diffbox
    self.image = make_box(color)

    #diff has to be translated: _( ) (BEGINNER, etc.)
    t1 = fontfx.shadow(_(diff), f, [255, 255, 255])
    r1 = t1.get_rect()
    r1.center = [self.image.get_width()/2, 14]

    t2 = fontfx.shadow("x%d - %s" % (feet, grade), f, [255, 255, 255])
    r2 = t2.get_rect()
    r2.center = [self.image.get_width()/2, 34]

    self.image.blit(t1, r1)
    self.image.blit(t2, r2)

    self.rect = self.image.get_rect()
    self.rect.topleft = self._topleft
    self.image.set_alpha(140)

# Scrolling list. Used all over the place.
class ListBox(pygame.sprite.Sprite):
  def __init__(self, font, color, spacing, count, width, topleft):
    pygame.sprite.Sprite.__init__(self)
    self._h = spacing
    self._count = count
    self._w = width
    self._color = color
    self._font = font
    self._topleft = topleft

    # animation
    self._start = pygame.time.get_ticks()
    self._animate = -1
    self._animate_dir = 0
    self._offset = 0
            
    self.set_items([""])
    self._needs_update = True
    self._render()

  def set_items(self, items):
    c2 = [c / 8 for c in self._color]
    self._items = []

    for i in items:
      txt = fontfx.render_outer(i, self._w - 7, self._font)
      img = fontfx.shadow(txt, self._font, self._color)
      self._items.append(img)
    self._idx = self._oldidx = 0 - self._count / 2 # Reset index to 0.
    self._needs_update = True

  def set_index(self, idx, direction = 1):
    self._animate_dir = direction
    self._oldidx = self._idx
    self._idx = (idx - self._count / 2)
    self._needs_update = True

  def update(self, time):
    time -= self._start

    if self._idx != self._oldidx:
      self._animate = time + 100

    if self._animate > time:
      self._offset = (self._animate - time) / 100.0 # 0.1 seconds
      self._offset *= self._h	                    # percentage of height
      self._offset *= self._animate_dir	            # 1 for up, -1 for down
      self._needs_update = True
    elif self._offset != 0:
      self._offset = 0
      self._needs_update = True
    
    if self._needs_update:
      self._oldidx = self._idx
      self._needs_update = False
      self._render()

  def _render(self):
    self.image = pygame.Surface([self._w, self._h * self._count],
                                SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])
    for i, y in zip(range(self._count + 2),
                    range(-self._h / 2, self._h * (self._count + 1), self._h)):
      idx = (self._idx + i - 1) % len(self._items)
      t = self._items[idx]
      r = t.get_rect()
      r.centery = y + self._offset
      r.left = 5
      self.image.blit(t, r)
    self.rect = self.image.get_rect()
    self.rect.topleft = self._topleft

# Display the whole banner + surrounding text, with the slowly
# rotating color.
class BannerDisplay(pygame.sprite.Sprite):
  def __init__(self, center):
    pygame.sprite.Sprite.__init__(self)
    self.isfolder = False
    self._center = center
    self._clip = None
    self._color = [255, 0, 255]
    self._next_update = -1
    self._delta = 5
    self._idx = 1
    self._bpmdisplay = BPMDisplay(FontTheme.BannerDisp_BPM, [60, 180])

  def set_song(self, song):
    c1 = [255, 255, 255]
    self._bpmdisplay.set_song(song)
    self._next_update = -2 # Magic value

    song.render()

    self._title = fontfx.shadow(song.info["title"],
                                FontTheme.font('BannerDisp_title',song.info["title"],340),
                                c1)
    self._r_t = self._title.get_rect()
    self._r_t.center = [179, 240]
    self._artist = fontfx.shadow(song.info["artist"],
                                 FontTheme.font('BannerDisp_artist',song.info["artist"], 250),
                                 c1)

    self._r_a = self._artist.get_rect()
    self._r_a.center = [179, 320]

    if song.info["subtitle"]:
      self._subtitle = fontfx.shadow(song.info["subtitle"],
                                     FontTheme.font('BannerDisp_subtitle',song.info["subtitle"],300),

                                     c1)
      self._r_s = self._subtitle.get_rect()
      self._r_s.center = [179, 270]
    else: self._subtitle = None
    self._clip = song.clip
    self._banner = song.banner
    self._r_b = self._banner.get_rect()
    self._r_b.center = [179, 100]
    self._cdtitle = song.cdtitle
    self._r_cd = self._cdtitle.get_rect()
    self._r_cd.center = [290, 180]

  def _render(self):
    self.image = make_box(self._color, [350, 350])
    self.image.blit(self._banner, self._r_b)
    self.image.set_clip()

    self.image.blit(self._title, self._r_t)
    self.image.blit(self._artist, self._r_a)
    if self._subtitle: self.image.blit(self._subtitle, self._r_s)
    self.image.blit(self._bpmdisplay.image, self._bpmdisplay.rect)
    self.image.blit(self._cdtitle, self._r_cd)
    self.rect = self.image.get_rect()
    self.rect.center = self._center

  def update(self, time):
    self._bpmdisplay.update(time)
    if self._next_update == -2:
      self._next_update = time + 300
    elif time > self._next_update:
      self._next_update = time + 300
      if ((self._delta > 0 and self._color[self._idx] == 255) or
          (self._delta < 0 and self._color[self._idx] == 0)):
        self._idx = random.choice([i for i in range(3) if i != self._idx])
        if self._color[self._idx]: self._delta = -3
        else: self._delta = 3
      self._color[self._idx] += self._delta
    self._render()

# Wrap some text in a sprite.
class WrapTextDisplay(pygame.sprite.Sprite):
  def __init__(self, font, width, topleft, str = " ", centered = False):
    pygame.sprite.Sprite.__init__(self)
    self._text = str
    self._centered = centered
    self._needs_update = False
    self._font = fontfx.WrapFont(font, width)
    self._topleft = topleft
    self._render()

  def _render(self):
    self.image = self._font.render(self._text, shdw = False,
                                   centered = self._centered)
    self.rect = self.image.get_rect()
    self.rect.topleft = self._topleft

  def set_text(self, text):
    self._text = text
    self._needs_update = True

  def update(self, time):
    if self._needs_update: self._render()

# The base UI screen class. A sprite list, and a background image.
class InterfaceWindow(object):
  def __init__(self, screen, bg_fn):
    self._screen = screen
    self._bg = pygame.image.load(os.path.join(image_path, bg_fn)).convert()
    self._sprites = pygame.sprite.RenderUpdates()
    self._screen.blit(self._bg, [0, 0])
    self._callbacks = {} #FIXME: TODO
    self._clock = pygame.time.Clock()
    self._time_bonus = 0

  def update(self, screenshot = False):
    self._sprites.update(pygame.time.get_ticks() + self._time_bonus)
    pygame.display.update(self._sprites.draw(self._screen))

    if screenshot:
      fn = os.path.join(rc_path, "screenshot.bmp")
      print "Saving a screenshot to", fn
      pygame.image.save(self._screen, fn)

    self._sprites.clear(self._screen, self._bg)
    self._clock.tick(45)
    return False

NO_BANNER = os.path.join(image_path, "no-banner.png")

class AbstractItemDisplay(object):
  no_banner = make_box(size = [256, 80])
  tmp = pygame.image.load(NO_BANNER)
  tmp.set_colorkey(tmp.get_at([0, 0]))
  no_banner.blit(tmp, [4, 4])
  def __init__(self, song): # A SongItem object
    self._song = song
    self.info = song.info
    self.filename = song.filename
    
    self.banner = None
    self.isfolder = False
    self.folder = {}
    self.banner = None
    self.clip = None

  def render(self):
    if self.banner: return
    elif self.info["banner"]:
      self.banner, self.clip = load_banner(self.info["banner"])
    else: self.banner = SongItemDisplay.no_banner

    if self.info["cdtitle"]:
      self.cdtitle = pygame.image.load(self.info["cdtitle"])
    else: self.cdtitle = pygame.Surface([0, 0])

class SongItemDisplay(AbstractItemDisplay):
  def __init__(self, song, game):
    AbstractItemDisplay.__init__(self, song)
    self.difficulty = song.difficulty[game]
    self.diff_list = song.diff_list[game]
    self.danceitems = {}

class DanceItemDisplay(AbstractItemDisplay):
  def __init__(self, song, game, diff):
    AbstractItemDisplay.__init__(self, song)
    self.difficulty = {diff:song.difficulty[game][diff]}
    self.diff_list = [diff]
    self.diff = diff
    self.songitem = None


  
