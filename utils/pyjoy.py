#! /usr/bin/env python

import os, pygame, pygame.font, pygame.image, pygame.mixer, pygame.movie, time, sys
from pygame.locals import *

def main():
  # init
  pygame.init()

  # look for joysticks
  totaljoy = pygame.joystick.get_count()
  print totaljoy,"joysticks total -",

  if totaljoy < 1:
    print "bailing out. Check http://clickass.org/~tgz/pyddr/faq.html"
    sys.exit()

  ddrmat = pygame.joystick.Joystick(totaljoy-1)
  ddrmat.init()
  print "last one is",ddrmat.get_numaxes(),"axes and",ddrmat.get_numbuttons(),"buttons"
  
  # set up the screen and all that stuff
  screen = pygame.display.set_mode((640, 480), HWSURFACE|DOUBLEBUF) 
  pygame.display.set_caption('pyDDR')
  pygame.mouse.set_visible(1)


  while 1: 
    
    event = pygame.event.poll()
    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        break

# event.type ==
# JOYAXISMOTIONjoy, axis, value 
# JOYBALLMOTIONjoy, ball, rel 
# JOYHATMOTIONjoy, hat, value 
# JOYBUTTONUPjoy, button
# JOYBUTTONDOWNjoy, button

    # joystick

    if event.type == JOYBUTTONDOWN:
      print "pressed button",event.button
    if event.type == JOYBUTTONUP:
      print "released button",event.button

    if event.type == JOYAXISMOTION:
      for i in range(8):
        if event.axis == i:
          print "axis",i,"moved to",event.value

    # keyboard

    if event.type == KEYDOWN:
        print "key hit: code", event.key
        if event.key == K_LEFT:
            print "LEFT keypress"
        if event.key == K_DOWN:
            print "DOWN keypress"
        if event.key == K_UP:
            print "UP keypress"
        if event.key == K_RIGHT:
            print "RIGHT keypress"
    if event.type == KEYUP:
        if event.key == K_LEFT:
            print "LEFT unpress"
        if event.key == K_DOWN:
            print "DOWN unpress"
        if event.key == K_UP:
            print "UP unpress"
        if event.key == K_RIGHT:
            print "RIGHT unpress"
                   
#end
    
if __name__ == '__main__': main()
