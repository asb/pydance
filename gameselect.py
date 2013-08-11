# The basic game selector.

from constants import *
from interface import *
from pygame.font import Font

import ui
import endless, courseselect, songselect

from fonttheme import FontTheme

from i18n import *

GS_HELP = [
  _("Up / Down: Change game, mode, or interface"),
  _("Enter / Up Right: Advance your choice"),
  _("Escape / Up Left: Back up or exit"),
  _("F11: Toggles fullscreen"),
  _("Enjoy pydance %s!") % VERSION,
  ]

# The game, type, and interfaces available on the screen.
GAMES = [_("4 panel"), _("5 panel"), _("6 panel"), _("8 panel"), _("9 panel"),
         _("Parapara"), _("DMX"), _("EZ2"), _("EZ2 Real"), _("3 panel")]
TYPES = [_("Single"), _("Versus"), _("Double"), _("Couple")]
SS = [_("Normal"), _("Nonstop"), _("Endless")]

VALUES = [GAMES, TYPES, SS]

# Shrink and put two of the same image, staggered .
def make_versus(oldimage):
  surf = pygame.Surface([350, 300], SRCALPHA, 32)
  surf.fill([0, 0, 0, 0])
  newimage = pygame.transform.rotozoom(oldimage, 0, 0.714286)
  surf.blit(newimage, [0, 0])
  surf.blit(newimage, [100, 100])
  return surf

# Shrink and put two of the same image, in a line.
def make_double(oldimage):
  surf = pygame.Surface([350, 300], SRCALPHA, 32)
  surf.fill([0, 0, 0, 0])
  newimage = pygame.transform.rotozoom(oldimage, 0, 0.5)
  surf.blit(newimage, [0, 80])
  surf.blit(newimage, [175, 80])
  return surf

# Put the two images staggered and slightly rotated in different directions.
def make_couple(oldimage):
  surf = pygame.Surface([350, 300], SRCALPHA, 32)
  surf.fill([0, 0, 0, 0])
  image1 = pygame.transform.rotozoom(oldimage, -30, 0.714286)
  image2 = pygame.transform.rotozoom(oldimage, 30, 0.714286)
  surf.blit(image1, [-30, -40])
  surf.blit(image2, [60, 20])
  return surf

# Filenames for each mode, or functions to call with the previous image
# to construct the new image.
IMAGES = {
    _("3 panel"): "select-3p.png",
    _("4 panel"): "select-4p.png",
    _("5 panel"): "select-5p.png",
    _("6 panel"): "select-6p.png",
    _("8 panel"): "select-8p.png",
    _("9 panel"): "select-9p.png",
    _("Parapara"): "select-para.png",
    _("EZ2 Real"): "select-ez2real.png",
    _("EZ2"): "select-ez2.png",
    _("DMX"): "select-dmx.png",
    _("Single"): (lambda x: x),
    _("Versus"): make_versus,
    _("Double"): make_double,
    _("Couple"): make_couple,
    _("Normal"): "select-normal.png",
    _("Nonstop"): "select-nonstop.png",
    _("Endless"): "select-endless.png",
    }

# Constructors for the different interfaces.
SELECTORS = {
  _("Endless"): endless.Endless,
  _("Nonstop"): courseselect.CourseSelector,
  _("Normal"): songselect.SongSelect,
  }

# Map the game and type onto an internal name for SongItem.difficulty.
MODES = {
  (_("4 panel"), _("Single")): "SINGLE",
  (_("4 panel"), _("Versus")): "VERSUS",
  (_("4 panel"), _("Couple")): "COUPLE",
  (_("4 panel"), _("Double")): "DOUBLE",

  (_("3 panel"), _("Single")): "3PANEL",
  (_("3 panel"), _("Versus")): "3VERSUS",
  (_("3 panel"), _("Couple")): "3COUPLE",
  (_("3 panel"), _("Double")): "3DOUBLE",

  (_("5 panel"), _("Single")): "5PANEL",
  (_("5 panel"), _("Versus")): "5VERSUS",
  (_("5 panel"), _("Couple")): "5COUPLE",
  (_("5 panel"), _("Double")): "5DOUBLE",

  (_("6 panel"), _("Single")): "6PANEL",
  (_("6 panel"), _("Versus")): "6VERSUS",
  (_("6 panel"), _("Couple")): "6COUPLE",
  (_("6 panel"), _("Double")): "6DOUBLE",

  (_("8 panel"), _("Single")): "8PANEL",
  (_("8 panel"), _("Versus")): "8VERSUS",
  (_("8 panel"), _("Couple")): "8COUPLE",
  (_("8 panel"), _("Double")): "8DOUBLE",

  (_("9 panel"), _("Single")): "9PANEL",
  (_("9 panel"), _("Versus")): "9VERSUS",
  (_("9 panel"), _("Couple")): "9COUPLE",
  (_("9 panel"), _("Double")): "9DOUBLE",

  (_("Parapara"), _("Single")): "PARAPARA",
  (_("Parapara"), _("Versus")): "PARAVERSUS",
  (_("Parapara"), _("Couple")): "PARACOUPLE",
  (_("Parapara"), _("Double")): "PARADOUBLE",

  (_("DMX"), _("Single")): "DMX",
  (_("DMX"), _("Versus")): "DMXVERSUS",
  (_("DMX"), _("Couple")): "DMXCOUPLE",
  (_("DMX"), _("Double")): "DMXDOUBLE",

  (_("EZ2"), _("Single")): "EZ2SINGLE",
  (_("EZ2"), _("Versus")): "EZ2VERSUS",
  (_("EZ2"), _("Couple")): "EZ2COUPLE",
  (_("EZ2"), _("Double")): "EZ2DOUBLE",

  (_("EZ2 Real"), _("Single")): "EZ2REAL",
  (_("EZ2 Real"), _("Versus")): "REALVERSUS",
  (_("EZ2 Real"), _("Couple")): "REALCOUPLE",
  (_("EZ2 Real"), _("Double")): "REALDOUBLE",
}

DESCRIPTIONS = {
  _("4 panel"): (_("The standard up, down, left and right arrows ") +
              _("(like Dance Dance Revolution)")),
  _("3 panel"): _("Practice using up left and up right with easier steps."),
  _("5 panel"): _("Diagonal arrows and the center (like Pump It Up)"),
  _("6 panel"): _("Four panel plus the upper diagonal arrows (like DDR Solo)"),
  _("8 panel"): _("Everything but the center (like Technomotion)"),
  _("9 panel"): _("Everything! (like Pop'n'Stage)"),
  _("Parapara"): _("Wave your arms (or feet) around"),
  _("DMX"): (_("Crazy kung-fu action (like Dance ManiaX / Freaks). ") +
          _("Use left, up left, up right, and right.")),

  _("EZ2"): _("Three panels, two sensors, using left and right."),
  _("EZ2 Real"): _("Three panels and four sensors."),

  _("Single"): _("Play by yourself."),
  _("Versus"): _("Challenge an opponent to the same steps."),
  _("Couple"): _("Two people dance different steps to the same song."),
  _("Double"): _("Try playing on both sides at once."),

  _("Normal"): _("Play one song at a time."),
  _("Endless"): _("Keep dancing until you fail."),
  _("Nonstop"): _("Play several songs in a row."),
  }

class MainWindow(InterfaceWindow):
  def __init__(self, songs, courses, screen):
    InterfaceWindow.__init__(self, screen, "gameselect-bg.png")
    self._songs = songs
    self._courses = courses
    self._indicator_y = [152, 322, 414]
    # Displayed in the upper right.
    self._message = [_("Select a Game"), _("Select a Mode"), _("Select Type")]

    # Three lists, one for each type of selection.
    self._lists = [ListBox(FontTheme.GameSel_list, [255, 255, 255], 26, 9, 220, [408, 53]),
                   ListBox(FontTheme.GameSel_list, [255, 255, 255], 26, 3, 220, [408, 300]),
                   ListBox(FontTheme.GameSel_list, [255, 255, 255], 26, 3, 220, [408, 393])]
    self._lists[0].set_items(GAMES)
    self._lists[1].set_items(TYPES)
    self._lists[2].set_items(SS)

    # Title in the upper right (from self._message).
    self._title = TextDisplay('GameSel_screen_title', [210, 28], [414, 26])

    # Currently selected object.
    self._selected = TextDisplay('GameSel_selected_title', [400, 28], [15, 380])
    # Description of the currently selected object.
    self._description = WrapTextDisplay(FontTheme.GameSel_description, 360, [25, 396])
    self._title.set_text(self._message[0])
    self._selected.set_text(_("4 panel"))
    self._description.set_text(DESCRIPTIONS[_("4 panel")])
    self._sprites.add([self._title, self._selected, self._description])
    self._indicator = ActiveIndicator([405, 152], width = 230)
    self._sprites.add(self._indicator)
    self._sprites.add(HelpText(GS_HELP, [255, 255, 255], [0, 0, 0],
                               FontTheme.help, [206, 20]))
    self._sprites.add(self._lists)
    # The image displayed on the main part of the screen.
    self._image = FlipImageDisplay(IMAGES.get(_("4 panel")), [200, 200])
    self._sprites.add(self._image)

    self._screen.blit(self._bg, [0, 0])
    self._sprites.update(pygame.time.get_ticks())
    self._sprites.draw(self._screen)
    pygame.display.update()

    self.loop()

  def loop(self):
    active = 0 # 0 = game select, 1 = type select, 2 = ui select
    indices = [0, 0, 0] # currently selected indices
    pid, ev = ui.ui.poll()
    
    while not (ev == ui.CANCEL and active == 0):

      if ev == ui.UP: indices[active] -= 1
      elif ev == ui.DOWN: indices[active] += 1

      elif ev == ui.FULLSCREEN:
        mainconfig["fullscreen"] ^= 1
        pygame.display.toggle_fullscreen()

      elif ev == ui.CANCEL:
        active -= 1
      elif ev in [ui.CONFIRM, ui.START]:
        if active == 2:
          # Start the selected UI, and clean up afterwards
          SELECTORS[SS[indices[2]]](self._songs, self._courses, self._screen,
                                    MODES.get((VALUES[0][indices[0]],
                                               VALUES[1][indices[1]])))
          active = 0
          self._screen.blit(self._bg, [0, 0])
          pygame.display.update()
        else:
          active += 1
          if active == 1: self._oldimage = self._image._image # FIXME

      indices[active] %= len(VALUES[active])

      if ev in [ui.UP, ui.DOWN]:
        if ev == ui.UP: self._lists[active].set_index(indices[active], -1)
        else: self._lists[active].set_index(indices[active], 1)
        text = VALUES[active][indices[active]]
        self._selected.set_text(text)
        self._description.set_text(DESCRIPTIONS[text])
        img = IMAGES.get(text)
        if callable(img): self._image.set_image(img(self._oldimage))
        else: self._image.set_image(IMAGES.get(text))

      if ev in [ui.CONFIRM, ui.START, ui.CANCEL]:
        self._indicator.move([405, self._indicator_y[active]])
        self._title.set_text(self._message[active])
        text = VALUES[active][indices[active]]
        self._selected.set_text(text)
        self._description.set_text(DESCRIPTIONS[text])
        img = IMAGES.get(text)
        if callable(img): self._image.set_image(img(self._oldimage))
        else: self._image.set_image(IMAGES.get(text))

      self.update()
      pid, ev = ui.ui.poll()
