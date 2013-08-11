# A basic 11 button dance pad

from constants import *
import pygame, os
import cPickle as pickle
from pygame.locals import *
import colors
from fonttheme import FontTheme

(PASS, QUIT, UP, UPLEFT, LEFT, DOWNLEFT, DOWN, DOWNRIGHT,
 RIGHT, UPRIGHT, CENTER, START, SELECT, SCREENSHOT) = range(14)

NAMES = ["", _("quit"), _("up"), _("up-left"), _("left"), _("down-left"),
        _("down"), _("down-right"), _("right"), _("up-right"), _("center"),
        _("start"), _("select")]

KEYS = {
  K_ESCAPE: QUIT,
  K_PRINT: SCREENSHOT,
  K_SYSREQ: SCREENSHOT,
  }

KEY1 = {
  K_KP7: UPLEFT,
  K_KP8: UP,
  K_KP9: UPRIGHT,
  K_KP4: LEFT,
  K_KP5: CENTER,
  K_KP6: RIGHT,
  K_KP1: DOWNLEFT,
  K_KP2: DOWN,
  K_KP3: DOWNRIGHT,
  K_KP_ENTER: START,
  K_KP0: SELECT,
}

KEY2 = {
  K_u: UPLEFT,
  K_i: UP,
  K_o: UPRIGHT,
  K_j: LEFT,
  K_k: CENTER,
  K_l: RIGHT,
  K_m: DOWNLEFT,
  K_COMMA: DOWN,
  K_PERIOD: DOWNRIGHT,
  K_7: SELECT,
  K_9: START,
  }

# 16 buttons, 4 axis
# The EMSUSB2 is one adapter, two joysticks - +16 to get p2, uses this
# too. Apparently, there are two possible start buttons, 9 and 11?

# L1: 4, L2: 6, R1: 7, R2: 5
# Left: 15, Up: 12, Right: 13, Down: 14
# Square: 3, Tri: 0, Circle: 1, X: 2
# Select: 8, start: 9
# Left analog: 10, Right analog: 11

A4B16 = { 0: DOWNLEFT, 1: UPRIGHT, 2: UPLEFT, 3: DOWNRIGHT, 5: CENTER,
          8: SELECT, 9: START, 11: START, 12: UP, 13: RIGHT, 14: DOWN,
          15: LEFT }

# Buy n Shop parallel adapter
A6B12 = { 1: UPRIGHT, 3: UPLEFT, 8: SELECT, 4: LEFT, 5: RIGHT,
          6: DOWN, 7: UP, 9: START }

# Gravis Gamepad Pro USB - Uses axes for directions.
# 0: Square, 1: X, 2: O, 3: Triangle
# 4: L1, 5: R1, 6: L2, 7: R2
# 8: Select, 9: Start
A2B10 = { 0: LEFT, 1: DOWN, 2: RIGHT, 3: UP, 5: UPRIGHT, 7: DOWNRIGHT,
          8: SELECT, 9: START }
  
# This is some sort of natively USB mat
A2B8 = { 4: UP, 6: DOWN,  5: LEFT, 7: RIGHT, 2: START,
         3: DOWNLEFT, 0: UPRIGHT, 1: DOWNRIGHT }

# LevelSix USB pad? I'm not at all sure this is right.
A3B10 = { 0: LEFT, 1: DOWN, 2: RIGHT, 3: UP, 4: UPLEFT, 5: UPRIGHT,
          6: DOWNLEFT, 7: DOWNRIGHT, 8: SELECT, 9: START }
  
# Xbox gamepads, Linux driver
# With joydev module: 8 axes, 10 buttons
# With evdev module: 6 axes, 1 hat, 10 buttons
# B: 1, A: 0, X: 3, Y: 4, White: 5, Black: 2
# Back: 9, Start: 6
# Left analog stick: 7, Right analog stick: 8
A8B10 = { 4: UP, 0: DOWN, 3: LEFT, 1: RIGHT, 6: START, 9: QUIT }

# XBox gamepads, Xbox Linux driver (2.4.25 and 2.6.4 and earlier)
# With joydev module: 14 axes, 10 buttons
# With evdev module: 6 axes, 4 hats, 10 buttons
# B: 1, A: 0, X: 3, Y: 4, White: 5, Black: 2
# Back: 9, Start: 6
# Left analog stick: 7, Right analog stick: 8
A14B10 = { 4: UP, 0: DOWN, 3: LEFT, 1: RIGHT, 6: START, 9: QUIT }

# XBox gamepads, Xbox Linux driver
# With joydev module: 14 axes, 14 buttons
# With evdev module: 6 axes, 4 hats, 14 buttons
# Left: 12, Up: 9, Right: 10, Down: 11
# B: 1, A: 0, X: 3, Y: 4, White: 5, Black: 2
# Back: 13, Start: 6
# Left analog stick: 7, Right analog stick: 8
A14B14 = { 13: QUIT, 9: UP, 1: UPLEFT, 12: LEFT, 4: DOWNLEFT, 11: DOWN,
           3: DOWNRIGHT, 10: RIGHT, 0: UPRIGHT, 6: START }

MATS = { (6, 12): A6B12, (14, 10): A14B10, (2, 10): A2B10, (2, 8): A2B8,
         (8, 10): A8B10, (14, 14): A14B14 }

class Pad(object):

  (PASS, QUIT, UP, UPLEFT, LEFT, DOWNLEFT, DOWN, DOWNRIGHT,
   RIGHT, UPRIGHT, CENTER, START, SELECT, SCREENSHOT) = range(14)

  def __init__(self, handler = pygame.event):
    self.handler = handler
    self.handler.set_blocked(range(NUMEVENTS))
    self.handler.set_allowed((KEYUP, KEYDOWN, JOYBUTTONUP, JOYBUTTONDOWN))

    self.states = {}
    self.events = {}

    mat = mat2 = emsusb2 = None

    try: totaljoy = pygame.joystick.get_count()
    except: totaljoy = 0

    print totaljoy, _("joystick(s) found.")

    # Initialize all the joysticks, print diagnostics.
    for i in range(totaljoy):
      m = pygame.joystick.Joystick(i)
      m.init()
      args = (i, m.get_numaxes(), m.get_numbuttons())
      # One hat is two axes.
      args = (i, m.get_numaxes() + 2 * m.get_numhats(), m.get_numbuttons())
      print _("Joystick %d initialized: %d axes, %d buttons.") % args

      if args[2] == 32: emsusb2 = i
      elif mat == None and (args[1], args[2]) in MATS: mat = i
      elif mat2 == None and (args[1], args[2]) in MATS: mat2 = i

    self.merge_events(0, -1, KEY1)
    self.merge_events(1, -1, KEY2)

    loaded_input = False
    if os.path.exists(os.path.join(rc_path, "input.cfg")):
      try:
        fn = os.path.join(rc_path, "input.cfg")
        self.events = pickle.load(file(fn, "r"))
        for ev in self.events.values(): self.states[ev] = False
        loaded_input = True
      except:
        print _("W: Unable to load input configuration file.")
        loaded_input = False

    if loaded_input:
      print _("Loaded input configuration.")
    elif emsusb2 != None:
      self.merge_events(0, emsusb2, A4B16) 
      self.merge_events(1, emsusb2, dict([(k + 16, v) for (k, v) in A4B16.items()]))
      print _("EMSUSB2 found. Using preset EMSUSB2 config.")
    elif mat != None:
      joy = pygame.joystick.Joystick(mat)
      axes, but = joy.get_numaxes() + 2 * joy.get_numhats(), joy.get_numbuttons()
      print _("Initializing player 1 using js%d.") % mat
      self.merge_events(0, mat, MATS[(axes, but)])

      if mat2:
        joy = pygame.joystick.Joystick(mat2)
        axes, but = joy.get_numaxes() + 2 * joy.get_numhats(), joy.get_numbuttons()
        print _("Initializing player 2 using js%d.") % mat2
        self.merge_events(1, mat2, MATS[(axes, but)])
    elif totaljoy > 0:
      print _("No known joysticks found! If you want to use yours,")
      print _("you'll have to map its button manually once to use it.")

    self.merge_events(-1, -1, KEYS)

  def reinit_pads(self):
    pygame.joystick.init()
    try: totaljoy = pygame.joystick.get_count()
    except: totaljoy = 0
    print totaljoy, _("joystick(s) found.")
    for i in range(totaljoy): pygame.joystick.Joystick(i).init()

  def add_event(self, device, key, pid, event):
    self.events[(device, key)] = (pid, event)
    self.states[(pid, event)] = False

  def merge_events(self, pid, device, events):
    for key, event in events.items():
      self.add_event(device, key, pid, event)

  def device_key_for(self, keyboard, pid, event):
    for (device, key), (p, e) in self.events.items():
      if p == pid and e == event:
        if keyboard and device == -1: return pygame.key.name(key)
        elif not keyboard and device != -1: return "%d:%d" % (device, key)
    return "---"

  def delete_event(self, pid, keyb, event):
    for (d, k), (p, e) in self.events.items():
      if (p == pid and e == event and
          ((d == -1 and keyb) or (d != -1 and not keyb))):
        del(self.events[(d, k)])
        self.states[(d, k)] = False

  def delete_events(self, pid):
    for k, v in self.events.items():
      if v[0] == pid: del(self.events[k])
      self.states[v] == False

  # Poll the event handler and normalize the result. If we don't know
  # about the event but the device is the keyboard, return (-2, key).
  # Otherwise, return pass.
  def poll(self):
    ev = self.handler.poll()
    t = -1
    v = 0
    if ev.type == JOYBUTTONDOWN or ev.type == JOYBUTTONUP:
      t, v = ev.joy, ev.button
    elif ev.type == KEYDOWN or ev.type == KEYUP:
      t, v = -1, ev.key
    else:
      return (-1, PASS)

    # Pass in all keyboard keys pressed, so the ui handler can get them.
    # Also, if arrow keys are pressed return their direction even if they're
    # not mapped.
    if ((ev.type == KEYDOWN or ev.type == KEYUP) and
        (ev.key == K_LEFT or ev.key == K_RIGHT or ev.key == K_UP or
         ev.key == K_DOWN)):
      default = (0, {K_LEFT: LEFT, K_RIGHT: RIGHT,
                     K_UP: UP, K_DOWN: DOWN}[ev.key])
    elif (ev.type == KEYUP or ev.type == KEYDOWN):
      default = (-2, ev.key * 100)
    else: default = (-1, PASS)

    ret = self.events.get((t, v), default)

    if ev.type == JOYBUTTONUP or ev.type == KEYUP:
      if ret[0] != -2: self.states[ret] = False
      ret = (ret[0], -ret[1])
    elif ev.type == JOYBUTTONDOWN or ev.type == KEYDOWN:
      if ret[0] != -2: self.states[ret] = True

    return ret

  def wait(self, delay = 20):
    ev = (-1, PASS)
    while ev[1] == PASS:
      ev = self.poll()
      pygame.time.wait(delay)
    return ev

  def empty(self):
    ev = (0, QUIT)
    while ev[1] != PASS: ev = self.poll()

  def write(self, fn):
    pickle.dump(self.events, file(fn, "w"), 2)

  def set_repeat(*args): pass

pad = Pad()

class PadConfig(object):

  bg = pygame.image.load(os.path.join(image_path, "bg.png"))

  directions = range(2, 13)

  def __init__(self, screen):
    self.screen = screen
    pad.reinit_pads()
    clock = pygame.time.Clock()
    self.loc = [0, 0]
    self.width = [4, 11]

    ev = pygame.event.poll()
    while ev.type != KEYDOWN or ev.key != K_ESCAPE:
      self.render()
      ev = pygame.event.poll()

      if ev.type == KEYDOWN:
        if ev.key in [K_LEFT, K_KP4]: self.loc[0] -= 1
        elif ev.key in [K_RIGHT, K_KP6]: self.loc[0] += 1
        elif ev.key in [K_UP, K_KP8]: self.loc[1] -= 1
        elif ev.key in [K_DOWN, K_KP2]: self.loc[1] += 1
        elif ev.key in [K_RETURN, K_KP_ENTER]: self.map_key()

      self.loc[0] %= 4
      self.loc[1] %= 11

      clock.tick(30)

  def map_key(self):
    dir = self.loc[1] + 2
    if self.loc[0] % 2 == 0: keyb = True
    else: keyb = False
    if self.loc[0] > 1: pid = 1
    else: pid = 0

    if keyb:
      wanted_type = KEYDOWN
      text = _("Press a key for %s (escape to cancel)") % NAMES[dir]
    else:
      wanted_type = JOYBUTTONDOWN
      text = _("Press a button for %s (escape to cancel)") % NAMES[dir]

    img = FontTheme.MapKeys_message.render(text, True, colors.BLACK)
    r = img.get_rect()
    r.midbottom = [320, 460]
    self.screen.blit(img, r)
    pygame.display.update()

    ev = pygame.event.wait()
    while (ev.type != wanted_type and
           (ev.type != KEYDOWN or ev.key != K_ESCAPE)):
      ev = pygame.event.wait()
    if ev.type != KEYDOWN or ev.key != K_ESCAPE:
      if keyb: dev, but = -1, ev.key
      else: dev, but = ev.joy, ev.button
      pad.delete_event(pid, keyb, dir)
      pad.add_event(dev, but, pid, dir)

  def render(self):
    offset = 640 / 5
    cent = offset / 2

    self.screen.blit(PadConfig.bg, [0, 0])

    text = [_("Player 1"), _("Player 2")]
    text2 = [_("Keyboard"), _("Joystick")]

    for t in text:
      img = FontTheme.MapKeys_player.render(t, True, colors.BLACK)
      r = img.get_rect()
      r.midtop = [160 + 320 * text.index(t), 15]
      self.screen.blit(img, r)

      for t2 in text2:
        img = FontTheme.MapKeys_input_type.render(t2, True, colors.BLACK)
        r = img.get_rect()
        r.midtop = [cent + offset * text2.index(t2) +
                    (offset * 3) * text.index(t), 50]
        self.screen.blit(img, r)

    
    for dir in PadConfig.directions:
      p1_key = pad.device_key_for(True, 0, dir)
      p1_joy = pad.device_key_for(False, 0, dir)
      p2_key = pad.device_key_for(True, 1, dir)
      p2_joy = pad.device_key_for(False, 1, dir)

      order = [p1_key, p1_joy, NAMES[dir], p2_key, p2_joy]
      for i,o in enumerate(order):
        if (dir == self.loc[1] + 2 and
            ((i < 2 and i == self.loc[0]) or
             (i > 2 and i == self.loc[0] + 1))):

          img = FontTheme.MapKeys_entries.render(_(o), True, colors.WHITE) 
        else: img = FontTheme.MapKeys_entries.render(_(o), True, colors.BLACK)
        r = img.get_rect()
        r.center = [cent + offset * i, 60 + 26 * dir]
        self.screen.blit(img, r)

    pygame.display.update()
