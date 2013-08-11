#!/usr/bin/env python
# This is a little utility program to find the BPM for a song.
# It uses least squares estimation to fit a BPM and offset to
# beats tapped in by a key

import getopt
import sys
import os
import pygame, pygame.font, pygame.image, pygame.mixer
from pygame.locals import *

VERSION = "0.20"

def usage():
  print "findbpm %s - find the bpm of a song" % VERSION
  print "Usage: %s songfile.ogg" % sys.argv[0]
  print
  print """\
Press a key on time with the beat. An average BPM (for as long as you keep
tapping) will be calculated."""

def show_message(t):
  screen.fill((0,0,0))
  #text = font.render(t, 1, (250, 80, 80))
  text = font.render(t, 1, (255, 255, 255))
  textpos = text.get_rect()
  textpos.centerx = screen.get_rect().centerx
  textpos.centery = screen.get_rect().centery
  screen.blit(text, textpos)
  pygame.display.flip()

def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "vh", ["help", "version"])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  # FIXME: interpret opts...
    
  if len(args) != 1:
    usage()
    sys.exit(2)

  try: pygame.mixer.pre_init(44100, -16, 2)
  except: pygame.mixer.pre_init()

  global screen, font
  pygame.init()
  screen = pygame.display.set_mode((400, 48), HWSURFACE|DOUBLEBUF)
  pygame.display.set_caption('Tap to find Start, BPM')
  font = pygame.font.Font(None, 32)
  show_message('Tap to start music playing')

  playing = 0

  pygame.mixer.music.load(args[0])
  
  while 1:
    event = pygame.event.wait()

    if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
      break

    elif event.type == KEYDOWN:
      now = pygame.time.get_ticks()

      if not playing:
        pygame.mixer.music.play()
        music_start = now
        n = 0
        xsum = 0
        ysum = 0
        xxsum = 0
        xysum = 0
        show_message('Tap on each beat')
        playing = 1
        continue

      if n < 4:
        x = n
      else:
        # Forgive user skipping a beat
        x = int(0.5 + ((now - offset) * 1.0 / perbeat))
      xsum += x
      xxsum += x * x
      ysum += now
      xysum += x * now
      n += 1
      if n < 2:
        show_message('%d' % x)
        continue
      denom = xsum * xsum - n * xxsum
      offset = (xsum * xysum - xxsum * ysum) * 1.0 / denom
      perbeat = (xsum * ysum - n * xysum) * 1.0 / denom
      bpm = 60 * 1000.0 / perbeat
      moffset = offset - music_start
      show_message('%0.6s BPM offset %d ms beat %d' % (bpm,
                                                       int(moffset + 0.5),
                                                       x))

  if n >= 2:
    print 'bpm %0.6f' %  bpm
    print 'offset %d' % int(-moffset + 0.5)

if __name__ == '__main__':
    main()
