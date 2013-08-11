# The main grading screen.

import pygame
import announcer
import colors
import fontfx
import ui
import locale

from interface import *
from constants import *

from i18n import *
from fonttheme import FontTheme

# Fade in a 246x80 (not a typo!) graphic in the center of the screen.
class BannerFadeIn(pygame.sprite.Sprite):
  def __init__(self, image, center):
    pygame.sprite.Sprite.__init__(self)
    self._center = center
    self._end = pygame.time.get_ticks() + 3000
    self.image = image.convert()
    self.image = pygame.Surface([246, 80])
    r = image.get_rect()
    r.center = self.image.get_rect().center
    self.image.blit(image, r)
    self.rect = self.image.get_rect()
    self.rect.center = center
    self._image = self.image.convert()
    self.image.set_alpha(0)
    self._idir = 4
    self._i = 128
    self._last_update = pygame.time.get_ticks() - 200

  def update(self, time):
    if time > self._end:
      if time - self._last_update > 100:
        self.image = self._image.convert()
        if self._i < 4: self._idir = 4
        elif self._i > 250: self._idir = -4
        self._i += self._idir
        c = [self._i, 192, 192]
        txt = fontfx.shadow(_("Press Escape/Confirm/Start"), FontTheme.GrScr_tocontinue, c)
        txt_r = txt.get_rect()
        txt_r.center = [123, 70]
        self.image.blit(txt, txt_r)
        self.rect = self.image.get_rect()
        self.rect.center = self._center
        self._last_update = time

    else:
      alp = int(256 * (1 - ((self._end - time) / 3000.0)))
      self.image.set_alpha(alp)

# Display a rotating grade graphic.
class GradeSprite(pygame.sprite.Sprite):
  def __init__(self, center, rating):
    pygame.sprite.Sprite.__init__(self)
    rating = rating.lower()
    if rating == "!!": rating = "ee"
    if rating == "?": rating = "f"
    self._end = pygame.time.get_ticks() + 3000
    fn = os.path.join(image_path, "rating-%s.png" % rating)
    self._image = pygame.image.load(fn).convert()
    self._size = self._image.get_size()
    self._center = center
    self.rect = self._image.get_rect()
    self.rect.center = center

  def update(self, time):
    if time < self._end:
      angle = (self._end - time) / 3.0
      zoom = (1 - (self._end - time) / 3000.0)
      img = pygame.transform.rotozoom(self._image, angle, zoom).convert()
    else:
      img = self._image
    self.image = pygame.Surface(self._size)
    r = img.get_rect()
    r.center = self.image.get_rect().center
    self.image.blit(img, r)
    self.image.set_colorkey(self.image.get_at([0, 0]))
    self.rect = self.image.get_rect()
    self.rect.center = self._center

# And here is where I blatantly steal your idea, Matt. Sorry.
# Display a graph of the player's lifebar over time, scaled to a
# width/height.
class GrooveGaugeSprite(pygame.sprite.Sprite):
  def __init__(self, pos, size, records):
    pygame.sprite.Sprite.__init__(self)
    self._image = pygame.Surface(size)
    self._pos = pos
    self._end = pygame.time.get_ticks() + 3000
    self._size = size

    width = size[0]
    self._image.set_colorkey(self._image.get_at([0, 0]))
    c1 = [0, 190, 0]
    c2 = [190, 190, 0]
    c3 = [190, 0, 0]
    for i in range(width):
      p = (float(i) / float(width))
      plife = records[int(p * len(records))]
      h = size[1] - int(size[1] * plife)
      if plife > 0.5: c = colors.average(c1, c2, abs((plife - 0.5) / 0.5))
      else: c = colors.average(c2, c3, abs(plife / 0.5))
      pygame.draw.line(self._image, c, [i, size[1] - 1], [i, h])
      if plife > 0.999999: self._image.set_at([i, 0], [255, 255, 255])

  def update(self, time):
    if time < self._end:
      p = 1 - ((self._end - time)  / 3000.0)
      self.image = pygame.Surface([int(self._size[0] * p), self._size[1]])
      if self.image.get_size()[0] > 0:
        self.image.set_colorkey(self.image.get_at([0, 0]))
      self.image.blit(self._image, [0, 0])
    else: self.image = self._image
    self.rect = self.image.get_rect()
    self.rect.topleft = self._pos
    self.image.set_alpha(192)

# A number (with a label) that counts upwards.
class StatSprite(pygame.sprite.Sprite):
  def __init__(self, pos, title, count, size, delay):
    pygame.sprite.Sprite.__init__(self)
    self._start = pygame.time.get_ticks() + delay
    self._count = count
    self._pos = pos
    self._curcount = 0
    self._size = size
    self._title = fontfx.shadow(title, FontTheme.GrScr_text, colors.WHITE)
    self._render()

  def _render(self):
    self.image = pygame.Surface(self._size, SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])
    rt = self._title.get_rect()
    rt.midleft = [0, self._size[1] / 2]
    self.image.blit(self._title, rt)
    cnt = fontfx.shadow(locale.format("%d", self._curcount, True), FontTheme.GrScr_text,
                        colors.WHITE)
    rc = cnt.get_rect()
    rc.midright = [self._size[0] - 1, self._size[1] / 2]
    self.image.blit(cnt, rc)
    self.rect = self.image.get_rect()
    self.rect.topleft = self._pos

  def update(self, time):
    if time < self._start: return
    elif time - self._start < 2000:
      self._curcount = min(int(self._count * ((time - self._start) / 1000.0)),
                           self._count)
      self._render()
    elif self._curcount != self._count:
      self._curcount = self._count
      self._render()

# Like StatSprite but with two numbers (separated by /).
class HoldStatSprite(pygame.sprite.Sprite):
  def __init__(self, pos, title, goodcount, totalcount, size, delay):
    pygame.sprite.Sprite.__init__(self)
    self._start = pygame.time.get_ticks() + delay
    self._goodcount = goodcount
    self._totalcount = totalcount
    self._pos = pos
    self._curgood = 0
    self._curtotal = 0
    self._size = size
    self._title = fontfx.shadow(title, FontTheme.GrScr_text, colors.WHITE)
    self._render()

  def _render(self):
    self.image = pygame.Surface(self._size, SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])
    rt = self._title.get_rect()
    rt.midleft = [0, self._size[1] / 2]
    self.image.blit(self._title, rt)
    s = "%d / %d" % (self._curgood, self._curtotal)
    cnt = fontfx.shadow(s, FontTheme.GrScr_text, colors.WHITE)
    rc = cnt.get_rect()
    rc.midright = [self._size[0] - 1, self._size[1] / 2]
    self.image.blit(cnt, rc)
    self.rect = self.image.get_rect()
    self.rect.topleft = self._pos

  def update(self, time):
    if time < self._start: return
    elif time - self._start < 2000:
      p = (time - self._start) / 1000.0
      self._curgood = min(int(self._goodcount * p), self._goodcount)
      self._curtotal = min(int(self._totalcount * p), self._totalcount)
      self._render()
    elif self._curgood != self._goodcount:
      self._curgood = self._goodcount
      self._curtotal = self._totalcount
      self._render()

class GradingScreen(InterfaceWindow):
  def __init__(self, screen, players, banner_fn):
    self.players = players
    for p in players:
      if p == None: continue
      print "Player %d:" % (p.pid + 1)
      grade = p.grade.grade(p.failed)
      stepcount = p.stats.arrow_count
      steps = (grade, p.difficulty, stepcount, p.stats.maxcombo)
      ratings = (p.stats["V"], p.stats["P"], p.stats["G"],
                 p.stats["O"], p.stats["B"], p.stats["M"],
                 p.stats.good_holds, p.stats.hold_count)
      print _("GRADE: %s (%s) - total steps: %d; best combo: %d") % steps
      print _("V: %d P: %d G: %d O: %d B: %d M: %d - %d/%d holds") % ratings
      try:
        print _("Average off: %0.3f, standard deviation %0.2f") % p.stats.times()
      except: pass # Python 2.2
      print

    if self.players[0] == None: return None
    elif self.players[0].stats.arrow_count == 0: return None
    InterfaceWindow.__init__(self, screen, "grade-bg.png")
    pygame.display.update()

    if banner_fn is None:
      banner_fn = os.path.join(image_path, "no-banner.png")
    banner, dummy_rect = load_banner(banner_fn, False)
    banner = pygame.transform.rotozoom(banner, 0, (246.0 / banner.get_width()))
    self._sprites.add(BannerFadeIn(banner, [320, 241]))

    plr = self.players[0]

    s = [180, 34]
    # FIXME: There is probably a shorter way to do this.
    self._sprites.add([
      StatSprite([200, 10], _("MARVEL.:"), plr.stats["V"], s, 0),
      StatSprite([200, 39], _("PERFECT:"), plr.stats["P"], s, 333),
      StatSprite([200, 68], _("GREAT:"), plr.stats["G"], s, 666),
      StatSprite([200, 97], _("OKAY:"), plr.stats["O"], s, 1000),
      StatSprite([200, 126], _("BOO:"), plr.stats["B"], s, 1333),
      StatSprite([200, 155], _("MISS:"), plr.stats["M"], s, 1333),
      StatSprite([400, 10], _("Score:"), int(plr.score.score), s, 666),
      HoldStatSprite([400, 39], _("Holds:"), plr.stats.good_holds,
                     plr.stats.hold_count, s, 1000),
      StatSprite([400, 68], _("Max Combo:"), plr.stats.maxcombo, s, 1333),
      StatSprite([400, 97], _("Early:"), plr.stats.early, s, 1666),
      StatSprite([400, 126], _("Late:"), plr.stats.late, s, 2000),
      StatSprite([400, 155], _("TOTAL:"), plr.stats.arrow_count, s, 2333)
      ])
    plr.announcer.say(_("rating-") + p.grade.grade(p.failed).lower())
    self._sprites.add(GradeSprite([98, 183], plr.grade.grade(plr.failed)))
    self._sprites.add(GrooveGaugeSprite([10, 22], [176, 100],
                                        plr.lifebar.record))

    if len(self.players) == 2:
      plr = self.players[1]
      self._sprites.add([
        StatSprite([15, 290], _("MARVEL.:"), plr.stats["V"], s, 0),
        StatSprite([15, 319], _("PERFECT:"), plr.stats["P"], s, 333),
        StatSprite([15, 348], _("GREAT:"), plr.stats["G"], s, 666),
        StatSprite([15, 377], _("OKAY:"), plr.stats["O"], s, 1000),
        StatSprite([15, 406], _("BOO:"), plr.stats["B"], s, 1333),
        StatSprite([15, 435], _("MISS:"), plr.stats["M"], s, 1666),
        StatSprite([215, 290], _("Score:"), int(plr.score.score), s, 666),
        HoldStatSprite([215, 319], _("Holds:"), plr.stats.good_holds,
                   plr.stats.hold_count, s, 1000),
        StatSprite([215, 348], _("Max Combo:"), plr.stats.maxcombo, s, 1333),
        StatSprite([215, 377], _("Early:"), plr.stats.early, s, 1666),
        StatSprite([215, 406], _("Late:"), plr.stats.late, s, 2000),
        StatSprite([215, 435], _("TOTAL:"), plr.stats.arrow_count, s, 2333),
        ])
      self._sprites.add(GradeSprite([541, 294], plr.grade.grade(plr.failed)))
      self._sprites.add(GrooveGaugeSprite([453, 370], [176, 100],
                                          plr.lifebar.record))

    ui.ui.clear()
    screenshot = False
    pid, ev = ui.ui.poll()
    clock = pygame.time.Clock()
    exits = [ui.QUIT]
    start = pygame.time.get_ticks()
    
    while ev not in exits:
      if ev == ui.FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1
      elif ev == ui.SCREENSHOT:
        screenshot = True
      # The first time we hit start, advance the time counter to stop
      # all the animations.
      elif (ev == ui.CONFIRM or ev == ui.START or
            (pygame.time.get_ticks() - start > 3333 and not self._time_bonus)):
        exits.extend([ui.CONFIRM, ui.START])
        ev = ui.PASS
        self._time_bonus = 3333

      screenshot = self.update(screenshot)
      if self._time_bonus:
        pid, ev = ui.ui.poll()
        pygame.time.delay(100)
      else: pid, ev = ui.ui.poll()

      self.update()
