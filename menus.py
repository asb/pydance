import pygame, colors, ui
from constants import *
from fontfx import TextZoomer
from fonttheme import FontTheme

# Hooray! Less magic numbers
LIGHT_GRAY = (128, 128, 128)
TOPLEFT = (0, 0)
BUTTON_SIZE = (192, 48)
BUTTON_WIDTH, BUTTON_HEIGHT = BUTTON_SIZE
BUTTON_PADDING = 8
LEFT_OFFSET, TOP_OFFSET = 425, 100
TRANSPARENT, SOLID = 128, 255
DISPLAYED_ITEMS = 6

CREATE, SELECT, UNSELECT = 1000, 2000, 3000

button_bg = pygame.image.load(os.path.join(image_path, "button.png"))

class MenuItem(object):

  def __init__(self, text, callbacks, args):
    # Dict of callbacks by keycodes, also "initial", "select", "unselect"

    # This looks something like:
    # MenuItem({ 'initial': do_setup, START: do_change,
    #            START: do_change }, (configdata, mystrings))
    # When the button is pressed, do_change(configdata, mystrings) will be
    # called.
    self.callbacks = callbacks
    self.args = args
    self.bg = button_bg
    self.rgb = LIGHT_GRAY
    self.subtext = None
    self.alpha = TRANSPARENT
    self.text = text
    self.render()

  # Call an appropriate callback function, for the event given.
  # The function can return up to three arguments - the new
  # text to display on the button, the new subtext to display, and
  # the RGB value of the text.

  def activate(self, ev): # Note - event ID, not an event tuple
    if ev == SELECT:
      self.rgb = colors.WHITE
      self.alpha = SOLID
      self.render()
    elif ev == UNSELECT:
      self.rgb = LIGHT_GRAY
      self.alpha = TRANSPARENT
      self.render()
    elif self.callbacks == None:
      if ev  in [ui.START, ui.RIGHT, ui.LEFT, ui.CONFIRM]:
        return ui.QUIT # This is a back button
      else: return ev # Shouldn't happen
    elif callable(self.callbacks.get(ev)):
      text, subtext = self.callbacks[ev](*self.args)
      if text != None: self.text = text #str(text)
      if subtext != None: self.subtext = subtext #str(subtext)
      self.render()
      return ev
    else: return ev

  # Render the image. If subtext is present, the main text gets smaller.
  def render(self):
    self.image = pygame.surface.Surface(BUTTON_SIZE)
    self.image.blit(self.bg, (0,0))
    if self.subtext == None:
      text = FontTheme.Menu_button_no_sub.render(self.text, 1, self.rgb)
      self.image.blit(text, (BUTTON_WIDTH/2 - FontTheme.Menu_button_no_sub.size(self.text)[0] / 2,
                             BUTTON_HEIGHT/2 - FontTheme.Menu_button_no_sub.size(self.text)[1]/2))
    else:
      text = FontTheme.Menu_button_if_sub.render(self.text, 1, self.rgb)
      subtext = FontTheme.Menu_button_sub.render(self.subtext, 1, self.rgb)
      self.image.blit(text, (BUTTON_WIDTH/2 - FontTheme.Menu_button_if_sub.size(self.text)[0] / 2,
                             BUTTON_HEIGHT/3 - FontTheme.Menu_button_if_sub.size(self.text)[1]/2))
      self.image.blit(subtext,
                      (BUTTON_WIDTH/2 - FontTheme.Menu_button_sub.size(self.subtext)[0] / 2,
                       2 * BUTTON_HEIGHT/3 - FontTheme.Menu_button_sub.size(self.text)[1] / 2))
    self.image.set_alpha(self.alpha)

class Menu(object):

  bgimage = pygame.image.load(os.path.join(image_path, "menu-bg.png"))
  try:
    click_sound = pygame.mixer.Sound(os.path.join(sound_path, "clicked.ogg"))
    click_sound.set_volume(0.45)
  except pygame.error:
    raise SystemExit("You need SDL_mixer 1.2.5 with Vorbis support.")
  move_sound = pygame.mixer.Sound(os.path.join(sound_path, "move.ogg"))
  back_sound = pygame.mixer.Sound(os.path.join(sound_path, "back.ogg"))

  # Menus are defined based on a tree of tuples (submenus) ending
  # in a list (the final item). The first item of the tuple is
  # a string of text which gets displayed.
  def __init__(self, name, itemlist, screen, sprites):
    self.items = []
    self.sprites = sprites
    self.text = name
    self.rgb = LIGHT_GRAY
    self.bg = button_bg
    self.alpha = TRANSPARENT
    self.screen = screen
    self.render()
    for i in itemlist:
      if type(i) == type([]): # Menuitems are lists
        self.items.append(MenuItem(i[0], i[1], i[2]))
        self.items[-1].activate(CREATE)
      elif type(i) == type((0,0)): # New submenus are tuples
        self.items.append(Menu(i[0], i[1:], screen, sprites))

  # Menu rendering is tons easier, since it never changes.
  def render(self):
    self.image = pygame.surface.Surface(BUTTON_SIZE)
    self.image.blit(self.bg, (0,0))
    text = FontTheme.Menu_button_no_sub.render(self.text, 1, self.rgb)
    self.image.blit(text, (BUTTON_WIDTH/2 - FontTheme.Menu_button_no_sub.size(self.text)[0] / 2,
                           BUTTON_HEIGHT/2 - FontTheme.Menu_button_no_sub.size(self.text)[1] / 2))
    self.image.set_alpha(self.alpha)

  def activate(self, ev):
    if ev  in [ui.START, ui.CONFIRM, ui.RIGHT]:
      self.display()
    elif ev == SELECT:
      self.rgb = colors.WHITE
      self.alpha = SOLID
      self.render()
    elif ev == UNSELECT:
      self.rgb = LIGHT_GRAY
      self.alpha = TRANSPARENT
      self.render()

  # Render and start navigating the menu.
  # Postcondition: Screen buffer is in an unknown state!
  def display(self):
    screen = self.screen
    clock = pygame.time.Clock()
    Menu.bgimage.set_alpha(256)
    pygame.display.update(screen.blit(Menu.bgimage, TOPLEFT))
    curitem = 0
    topitem = 0
    changed = False
    toprotater = TextZoomer(self.text, FontTheme.Menu_rotating_top, (640, 64),
                            (178, 110, 0), colors.WHITE)

    self.items[curitem].activate(SELECT)

    ev = ui.PASS
    while ev != ui.QUIT:
      r = []
      ev = ui.ui.poll()[1]

      # Scroll down through the menu
      if ev == ui.DOWN:
        Menu.move_sound.play()
        ev = self.items[curitem].activate(UNSELECT)
        curitem += 1
        if curitem == len(self.items): # Loop at the bottom
          curitem = 0
          topitem = 0
        elif curitem >= topitem + DISPLAYED_ITEMS: # Advance the menu
          topitem += 1
        ev = self.items[curitem].activate(SELECT)

      # Same as above, but up
      elif ev == ui.UP:
        Menu.move_sound.play()
        ev = self.items[curitem].activate(UNSELECT)
        curitem -= 1
        if curitem < 0:
          curitem = len(self.items) - 1
          topitem = max(0, curitem - DISPLAYED_ITEMS + 1)
        elif curitem < topitem:
          topitem = curitem
        ev = self.items[curitem].activate(SELECT)

      elif ev == ui.FULLSCREEN:
        mainconfig["fullscreen"] ^= 1
        pygame.display.toggle_fullscreen()

      # Otherwise, if the event actually happened, pass it on to the button.
      elif ev != ui.PASS and ev != ui.QUIT:
        if ev in [ui.START, ui.CONFIRM]: Menu.click_sound.play()
        ev = self.items[curitem].activate(ev)
        ui.ui.clear()
        changed = True

      toprotater.iterate()
      if changed: r.append(screen.blit(Menu.bgimage, TOPLEFT))
      else: screen.blit(Menu.bgimage, TOPLEFT)
      r.append(screen.blit(toprotater.tempsurface, TOPLEFT))
      for i in range(DISPLAYED_ITEMS):
        if i + topitem < len(self.items):
          r.append(screen.blit(self.items[i + topitem].image,
                               (LEFT_OFFSET,
                                TOP_OFFSET + i * (BUTTON_HEIGHT +
                                                  BUTTON_PADDING))))

      self.sprites.update()
      r.extend(self.sprites.draw(screen))
      pygame.display.update(r)
      #self.sprites.clear(screen, Menu.bgimage)
      clock.tick(30)

    if ev == ui.QUIT:
      Menu.back_sound.play()
      self.items[curitem].activate(UNSELECT)
