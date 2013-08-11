# GFXTheme and associated classes.
# These handle loading the various graphics themes for pydance.

import os
import games
import zipfile
import dircache

from cStringIO import StringIO

from listener import Listener

from constants import *

# Wrapper classes for loading files from themes.
# Eventually, we can use ZipFile + StringIO to make it load from zip files.
class ThemeFile(object):
  # The amount of rotation needed, from an arrow pointing left, to
  # make the direction.

  rotate = { "ldur": { "l": 0, "r": 180, "u": -90, "d": 90 },
             "kzwg": { "k": 0, "z": -90, "g": 180, "w": 90 },
             "c": { "c": 0 } }

  # List all themes available for a game type (given as a string)
  def list_themes(cls, gametype):
    w = games.GAMES[gametype].width
    size = "%dx%d" % (w, w)
    theme_list = []
    for path in search_paths:
      check = os.path.join(path, "themes", "gfx", size)
      if os.path.isdir(check):
        for name in dircache.listdir(check):
          if cls.is_theme(os.path.join(check, name), games.GAMES[gametype]):
            theme_list.append(name)
    return theme_list

  list_themes = classmethod(list_themes)

  # Test whether a particular theme will work for a particular game type.
  # Also, whether it's a theme at all, or just some random file.
  def is_theme(cls, filename, game):
    if not os.path.isdir(filename):
      return cls.is_zip_theme(filename, game)
    elif not os.path.exists(os.path.join(filename, "is-theme")):
      return False
    elif (os.path.split(os.path.split(filename)[0])[1] !=
          "%dx%d" % (game.width, game.width)):
      return False
    else:
      for dir in game.dirs:
        found = False
        for dirset in ThemeFile.rotate:
          if dir in dirset:
            for d in dirset:
              possible = "arr_%s_%s_0.png" % ("%s", d)
              if (os.path.exists(os.path.join(filename, possible % "c")) and
                  os.path.exists(os.path.join(filename, possible % "n"))):
                found = True
        if not found: return False
    return True

  is_theme = classmethod(is_theme)

  # Check if a zip file is a theme for a mode.
  def is_zip_theme(cls, filename, game):
    if filename[-3:].lower() != "zip": return False
    else:
      zip = zipfile.ZipFile(filename, "r")
      if zip.testzip():
        zip.close()
        return False
      files = zip.namelist()
      zip.close()
      if "is-theme" not in files: return False
      for dir in game.dirs:
        found = False
        for dirset in ThemeFile.rotate:
          if dir in dirset:
            for d in dirset:
              possible = "arr_%s_%s_0.png" % ("%s", d)
              if  (possible % "c" in files and possible % "n" in files):
                found = True
        if not found: return False
      return True

  is_zip_theme = classmethod(is_zip_theme)

  def __init__(self, filename, size):
    self.path = filename
    self.size = size
    self.zip = None
    if not os.path.isdir(filename):
      self.zip = zipfile.ZipFile(filename)

  # Get an image from the theme.
  def get_image(self, image_name):
    try:
      if self.zip:
        return pygame.image.load(StringIO(self.zip.read(image_name))).convert()
      else:
        return pygame.image.load(os.path.join(self.path, image_name)).convert()
    except:
      raise RuntimeError("E: %s was missing from your theme." % image_name)

  # Check to see if an image is in the theme.
  def has_image(self, image_name):
    if self.zip: return image_name in self.zip.namelist()
    else: return os.path.exists(os.path.join(self.path, image_name))

  # Get an arrow based on its type/direction/color.
  # If the desired arrow coloring wasn't found, fall back to the default
  # coloring (which is_theme makes sure we have).
  # If the desired direction wasn't found, try and make it.
  def get_arrow(self, type, dir, num):
    rotate = 0
    fn = "arr_%s_%s_%d.png" % (type, dir, num)
    realnum = num
    if not self.has_image(fn) and num == 3:
      fn = "arr_%s_%s_%d.png" % (type, dir, 1)
      realnum = 1
    if not self.has_image(fn):
      fn = "arr_%s_%s_%d.png" % (type, dir, 0)
      realnum = 0
    if not self.has_image(fn):
      for dirset in ["ldur", "kzwg", "c"]:
        if dir in dirset:
          for d in dirset:
            rotate = (ThemeFile.rotate[dirset][dir] -
                      ThemeFile.rotate[dirset][d])
            fn = "arr_%s_%s_%d.png" % (type, d, num)
            if self.has_image(fn):
                  realnum = num
                  break
            if num == 3:
              fn = "arr_%s_%s_%d.png" % (type, d, 1)
              if self.has_image(fn):
                realnum = 1
                break
            fn = "arr_%s_%s_%d.png" % (type, d, 0)
            if self.has_image(fn):
              realnum = 0
              break
    return self.get_image(fn), rotate, realnum

# An even higher-level interface than ThemeFile, that sets up the sprites
# for many of the images.
class GFXTheme(object):

  def __init__(self, name, pid, game):
    self.name = name
    self.game = game
    self.path = None
    self.pid = pid
    self.size = game.width
    size = "%dx%d" % (game.width, game.width)
    for path in search_paths:
      if os.path.exists(os.path.join(path, "themes", "gfx", size, name)):
        self.path = os.path.join(path, "themes", "gfx", size, name)

    if self.path == None:
      raise RuntimeError("E: Cannot load theme '%s/%s'." % (size, name))

    self.theme_data = ThemeFile(self.path, self.size)

  # FIXME: Can probably be moved to __init__ and stored as members.
  def arrows(self, pid):
    return ArrowSet(self.theme_data, self.game, pid)

  # FIXME: Can probably be moved to __init__ and stored as members.
  def toparrows(self, ypos, pid):
    arrs = {}
    arrfx = {}
    for d in self.game.dirs:
      arrs[d] = TopArrow(d, ypos, pid, self.theme_data, self.game)
      arrfx[d] = ArrowFX(d, ypos, pid, self.theme_data, self.game)
    return arrs, arrfx

  def get_lifebar(self):
    # Lifebars are 204x28 images.
    try:
      full = self.theme_data.get_image("lifebar-full.png").convert()
      empty = self.theme_data.get_image("lifebar-empty.png").convert()
    except RuntimeError:
      img = self.theme_data.get_image("lifebar.png").convert()
      full = pygame.Surface([204, img.get_height()])
      empty = pygame.Surface([204, img.get_height()])
      full.blit(img, [0, 0])
      empty.blit(img, [-204, 0])

    f = []
    e = []
    for y in range(0, full.get_height(), 28):
      new_f = pygame.Surface([204, 28])
      new_e = pygame.Surface([204, 28])
      new_f.blit(full, [0, -y])
      new_e.blit(empty, [0, -y])
      f.append(new_f)
      e.append(new_e)

    return f, e

# The scrolling arrows for this game mode.
class ArrowSet(object):
  def __init__ (self, theme, game, pid):
    arrows = {}
    base_left = game.left_off(pid) + pid * game.player_offset
    for dir in game.dirs:
      left = base_left + game.width * game.dirs.index(dir)
      for cnum in range(4):
        arrows[dir+repr(cnum)] = Arrow(theme, "c", dir, cnum, left)

    for n in arrows: self.__dict__[n] = arrows[n]
    self.arrows = arrows

  # allow access by instance['l']
  def __getitem__ (self, item):
    return getattr(self, item)

# The basic arrow that animates itself with the beat of the music. It's
# used for displaying the scrolling arrows and the top arrows.
class Arrow(object):
  def __init__(self, theme, type, dir, color, left):
    self.left = left
    self.dir = dir
    self._image, rotate, realnum = theme.get_arrow(type, dir, color)
    # This arrow is animated
    if (self._image.get_width() != theme.size or
        self._image.get_height() != theme.size):
      w = self._image.get_width()
      h = self._image.get_height()
      frames = (h * w) / theme.size
      if w / theme.size * theme.size != w or h / theme.size * theme.size != h:
        raise RuntimeError("Theme image is not evenly divisible: %dx%d."%(w,h))

      # Chop up the image.
      self._images = []
      for i in range(w / theme.size):
        for j in range(h / theme.size):
          s = pygame.Surface([theme.size, theme.size])
          s.blit(self._image, [-i * theme.size, -j * theme.size])
          s = pygame.transform.rotate(s, rotate)
          s.set_colorkey(s.get_at([0, 0]), RLEACCEL)
          self._images.append(s)
      self._beatcount = w / theme.size
      self._fpb = h / theme.size # frames per beat
      self._image = None
    else:
      self._image = pygame.transform.rotate(self._image, rotate)
      self._image.set_colorkey(self._image.get_at([0, 0]), RLEACCEL)

    if not mainconfig["animation"] and not self._image and type == "c":
      self._image = self._images[0]

  def get_images(self):
    if self._image: return [self._image]
    else: return self._images

  def get_image(self, beat):
      if self._image: return self._image
      else:
        beat /= self._beatcount
        pct = beat - int(beat)
        i = int(float(len(self._images)) * pct)
        return self._images[i]

# FIXME: What follows probably doesn't belong here, but elsewhere. There's
# too much logic for it to be just theming data.

# Sprites for the top flashing arrows.
class TopArrow(Listener, pygame.sprite.Sprite):

  def __init__ (self, direction, ypos, pid, theme, game):
    pygame.sprite.Sprite.__init__(self)
    self.pid = pid
    self.endpresstime = -1
    self._pressed = False
    self.dir = direction
    left = (game.left_off(pid) + game.player_offset * pid +
            game.dirs.index(direction) * game.width)

    # The 'n' state is the normal state for the top arrows. After being
    # pressed, they change to the 's' state images for a short time.
    self.narrow = Arrow(theme, "n", direction, 0, left)
    self.sarrow = Arrow(theme, "s", direction, 4, left)

    self.image = self.narrow.get_image(0)
    self.rect = self.image.get_rect()
    self.rect.top = ypos
    self.rect.left = left

  # The arrow was pressed, so we have to change it for some time (s state).
  def stepped(self, pid, dir, time, etime, rating, combo):
    if self.pid != pid or self.dir != dir or rating == "M": return
    self._pressed = True
    self.endpresstime = time + 0.25 # Number of seconds to change it for.

  def update(self, time, beat):
    if time > self.endpresstime: self._pressed = False
    if self._pressed: self.image = self.sarrow.get_image(beat)
    else: self.image = self.narrow.get_image(beat)

class ArrowFX(Listener, pygame.sprite.Sprite):
  def __init__ (self, direction, ypos, pid, theme, game):
    pygame.sprite.Sprite.__init__(self)
    self.presstime = -1000000
    self.centery = ypos + game.width / 2
    self.centerx = (game.left_off(pid) +
                    game.dirs.index(direction) * game.width + game.width / 2)
    self.pid = pid

    self.dir = direction

    self.baseimg = Arrow(theme, "n", direction, 0, 0).get_images()[-1]
    self.baseimg = self.baseimg.convert()
    self.tintimg = pygame.Surface(self.baseimg.get_size())
    self.tintimg.blit(self.baseimg, [0, 0])

    self.blackbox = pygame.surface.Surface([game.width] * 2)
    self.blackbox.set_colorkey(self.blackbox.get_at([0, 0]))
    self.image = self.blackbox
    self.rect = self.image.get_rect()
    self.displaying = 1
    self.direction = 1
    self.holdtype = 0
    self.colors = { "V": [255, 255, 255],
                    "P": [255, 255, 0],
                    "G": [0, 255, 0] }

    style = mainconfig['explodestyle']
    self.rotating, self.scaling = style & 1, style & 2
    self.stepped(self.pid, self.dir, -1, -1, "V", 0)
    
  def holding(self, yesorno):
    self.holdtype = yesorno
  
  def stepped(self, pid, dir, time, etime, tinttype, combo):
    if pid != self.pid or dir != self.dir: return
    elif tinttype not in self.colors: return

    self.combo = combo
    self.presstime = time
    self.tintimg = pygame.Surface(self.baseimg.get_size(), 0, 16)
    self.tintimg.blit(self.baseimg, [0, 0])
    tinter = pygame.surface.Surface(self.baseimg.get_size())
    tinter.fill(self.colors.get(tinttype, [0, 0, 255]))
    tinter.set_alpha(127)
    self.tintimg.blit(tinter, [0, 0])
    self.tintimg.set_colorkey(self.tintimg.get_at([0, 0]))
    self.tintimg = self.tintimg.convert()
    if self.direction == 1: self.direction = -1
    else: self.direction = 1

  def update(self, time):
    steptimediff = time - self.presstime
    
    if (steptimediff < 0.2) or self.holdtype:
      self.displaying = 1
      self.image = self.tintimg
      if self.scaling:
        if self.holdtype:
          scale = 1.54
        else:
          scale = 1.0 + (steptimediff * 4.0) * (1.0+(self.combo/256.0))
        newsize = [max(0, int(x*scale)) for x in self.image.get_size()]
        self.image = pygame.transform.scale(self.image, newsize)
      if self.rotating:
        angle = steptimediff * 230.0 * self.direction
        self.image = pygame.transform.rotate(self.image, angle)
      if self.holdtype == 0:
        tr = 224-int(1024.0*steptimediff)
      else:
        tr = 112
      self.image.set_alpha(tr)
            
    if self.displaying:
      if steptimediff > 0.2 and (self.holdtype == 0):
        self.image = self.blackbox
        self.displaying = 0
      self.rect = self.image.get_rect()
      self.rect.center = self.centerx, self.centery

      self.rect.left += (320 * self.pid)
