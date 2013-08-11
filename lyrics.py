import pygame
import colors

from constants import *
from fonttheme import FontTheme

class LyricChannel(pygame.sprite.Sprite):
  def __init__(self, top, color):
    pygame.sprite.Sprite.__init__(self)
    self._lyrics = []
    self._times = []
    self._prender = []
    self._lasttime = -1000

    self.image = pygame.surface.Surface([0, 0])

    self._oldlyric = -1
    self._color = color
    self._darkcolor = colors.darken_div(color)
    self._top = top

    self.rect = self.image.get_rect()
    self.rect.top = self._top
    self.rect.centerx = 320
       
  def addlyric(self, time, lyric):
    self._lyrics.append(lyric)
    self._times.append(time)
 
    image1 = FontTheme.Dance_lyrics_display.render(lyric, True, self._darkcolor)
    image2 = FontTheme.Dance_lyrics_display.render(lyric, True, self._color)
    rimage = pygame.Surface(image1.get_size())
    rimage.fill([64, 64, 64])
    rimage.blit(image1, [-2, -2])
    rimage.blit(image1, [2, 2])
    rimage.blit(image2, [0, 0])
    rimage.set_colorkey(rimage.get_at([0, 0]), RLEACCEL)

    self._prender.append(rimage)

  def update(self, curtime):
    current = -1
    timediff = curtime - self._lasttime
    for i in self._times:
      if curtime >= i:
        current = self._times.index(i)
        self._lasttime = i
 
    if current != self._oldlyric:
      self.image = self._prender[current]
      self.rect = self.image.get_rect()
      self.rect.top = self._top
      self.rect.centerx = 320
     
    if current != -1:
      holdtime = len(self._lyrics[current]) * 0.045
      alp = 255
      if timediff > holdtime:
        alp = 255 - (255 * (timediff - holdtime))
        if alp < 0: alp = 0

      self.image.set_alpha(int(alp))

    self._oldlyric = current

class Lyrics(object):
  def __init__(self, clrs):
    self._channels = {}
    self._colors = clrs
    
  def addlyric(self, time, chan, lyric):
    if chan not in self._channels:
      color = self._colors[chan % len(self._colors)]
      self._channels[chan] = LyricChannel(480 - (chan + 1) * 32, color)
    self._channels[chan].addlyric(time, lyric)

  def channels(self): return self._channels.values()
