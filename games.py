# This contains a bunch of information describing the different
# game types pydance supports.

class GameType(object):
  def __init__(self, **args):
    # The width in pixels of the arrows. FIXME: Height should also be
    # dependent on this, or separate variable; currently it's hardcoded
    # to 64
    self.width = 64

    # The directions to be displayed for each player.
    self.dirs = "ldur"

    # This maps certain directions to others, in case two directions (in
    # the button sense) trigger the same direction (in the game sense).
    # Think IIDX scratching.
    self.dirmap = {}

    # The maximum number of players for this game mode.
    self.players = 2

    self.centered = False
    self.theme_default = "default"

    #  Whether or not to parse the step data in coupled format, that is
    # as different steps depending on player ID.
    self.couple = False

    # Whether or not we should map input for two joysticks to one player
    # This also affects how the arrows are laid out.
    self.double = False

    # 'theme' is used as a theme identifier, so people don't have to set
    # a separate theme for each mode.

    self.__dict__.update(args)

    self.dirs = list(self.dirs)

    # The spacing between each field's edge; therefore, the width of
    # each player's field as well.
    if self.double: self.player_offset = 640 / (2 * self.players)
    else: self.player_offset = 640 / self.players

    # There isn't a double mode that we shouldn't parse as a coupled mode...
    if self.double: self.couple = True

    # The offset to start drawing the arrows at, centered within the field
    # (Unless the mode isdoubled - see left_offset(self,pid) below.
    if self.double:
      self.left_offset = (640 / (2 * self.players) -
                          self.width * len(self.dirs)) / 2
    else:
      self.left_offset = (640 / self.players - self.width * len(self.dirs)) / 2

    self.battle_lefts = {}

    # Precalcuate soem offsets for battle mode.
    for d in self.dirs:
      self.battle_lefts[d] = int(self.width *
                                 (len(self.dirs) / 2.0 - self.dirs.index(d)))

    # The center of the playfield, for non-arrow sprites (score, lifebar, etc)
    self.sprite_center = 320 / self.players

  # In double and centered modes, we need to have the fields adjacent and
  # dependent on pid.
  # sprite_center will be fine; player_offset will be fine.
  def left_off(self, pid):
    if not self.double and not self.centered: return self.left_offset
    elif pid & 1: return 0
    else: return self.left_offset * 2

GAMES = {
  "SINGLE": GameType(players = 1, theme = "4p"),
  "VERSUS": GameType(players = 2, theme = "4p"),
  "COUPLE": GameType(couple = True, theme = "4p"),
  "DOUBLE": GameType(double = True, players = 1, theme = "4p"),

  "3PANEL": GameType(players = 1, dirs = "kdz", theme = "3p"),
  "3VERSUS": GameType(players = 2, dirs = "kdz", theme = "3p"),
  "3COUPLE": GameType(players = 2, couple = True, dirs = "kdz", theme = "3p"),
  "3DOUBLE": GameType(players = 1, double = True, dirs = "kdz", theme = "3p"),

  "5PANEL": GameType(players = 1, dirs = "wkczg", width = 56, theme = "5p"),
  "5VERSUS": GameType(players = 2, dirs = "wkczg", width = 56, theme = "5p"),
  "5COUPLE": GameType(players = 2, couple = True, dirs = "wkczg",
                      width = 56, theme = "5p"),
  "5DOUBLE": GameType(players = 1, double = True, dirs = "wkczg",
                      width = 56, theme = "5p"),

  "6PANEL": GameType(players = 1, dirs = "lkduzr", theme = "6pl"),
  "6VERSUS": GameType(players = 2, dirs = "lkduzr", width = 48, theme = "6ps"),
  "6COUPLE": GameType(players = 2, couple = True, dirs = "lkduzr",
                      width = 48, theme = "6ps"),
  "6DOUBLE": GameType(players = 1, double = True, dirs = "lkduzr",
                      width = 48, theme = "6ps"),

  "8PANEL": GameType(players = 1, dirs = "wlkduzrg", theme = "8pl"),
  "8VERSUS": GameType(players = 2, dirs = "wlkduzrg", width = 32,
                      theme = "8ps"),
  "8COUPLE": GameType(players = 2, dirs = "wlkduzrg", width = 32,
                      couple = True, theme = "8ps"),
  "8DOUBLE": GameType(players = 1, dirs = "wlkduzrg", width = 32,
                      double = True, theme = "8ps"),

  "9PANEL": GameType(players = 1, dirs = "wlkdcuzrg", theme = "9pl"),
  "9VERSUS": GameType(players = 2, dirs = "wlkdcuzrg", width = 32,
                      theme = "9ps"),
  "9COUPLE": GameType(players = 2, dirs = "wlkdcuzrg", width = 32,
                      couple = True, theme = "9ps"),
  "9DOUBLE": GameType(players = 1, dirs = "wlkdcuzrg", width = 32,
                      double = True, theme = "9ps"),

  "EZ2SINGLE": GameType(players = 1, dirs = "kldrz", width = 56,
                        theme = "ez2", theme_default = "ez2",
                        dirmap = {"w":"l", "g":"r"}),
  "EZ2VERSUS": GameType(players = 2, dirs = "kldrz", width = 56,
                        theme = "ez2",  theme_default = "ez2",
                        dirmap = {"w":"l", "g":"r"}),
  "EZ2COUPLE": GameType(players = 2, dirs = "kldrz", width = 56,
                        theme = "ez2", theme_default = "ez2", couple = True,
                        dirmap = {"w":"l", "g":"r"}),
  "EZ2DOUBLE": GameType(players = 1, dirs = "kldrz", width = 56,
                        theme = "ez2", theme_default = "ez2", double = True,
                        dirmap = {"w":"l", "g":"r"}),

  "EZ2REAL": GameType(players = 1, dirs = "klwdgrz", width = 56,
                      theme = "ez2real", theme_default = "ez2"),
  "REALVERSUS": GameType(players = 2, dirs = "klwdgrz", width = 32,
                         theme = "ez2real", theme_default = "ez2"),
  "REALCOUPLE": GameType(players = 2, dirs = "klwdgrz", width = 32,
                         theme = "ez2real", theme_default = "ez2",
                         couple = True),
  "REALDOUBLE": GameType(players = 1, dirs = "klwdgrz", width = 32,
                         theme = "ez2real", theme_default = "ez2",
                         double = True),

  "PARAPARA": GameType(players = 1, dirs = "lkuzr", width = 48,
                       theme = "para"),
  "PARAVERSUS": GameType(players = 2, dirs = "lkuzr", width = 48,
                         theme = "para"),
  "PARACOUPLE": GameType(players = 2, couple = True, dirs = "lkuzr",
                      width = 48, theme = "para"),
  "PARADOUBLE": GameType(players = 1, double = True, dirs = "lkuzr",
                      width = 48, theme = "para"),

  "DMX": GameType(players = 1, dirs = "lkzr", width = 32, theme = "dmx",
                  theme_default = "dmxesque"),
  "DMXVERSUS": GameType(players = 2, dirs = "lkzr", width = 32,
                        centered = True, theme = "dmx",
                        theme_default = "dmxesque"),
  "DMXCOUPLE": GameType(players = 2, couple = True, dirs = "lkzr",
                        theme_default = "dmxesque", width = 32,
                        centered = True, theme = "dmx"),
  "DMXDOUBLE": GameType(players = 1, double = True, dirs = "lkzr", width = 32,
                        theme_default = "dmxesque", theme = "dmx"),
  }

SINGLE = [mode for mode in GAMES if (GAMES[mode].players == 1 and
                                     not GAMES[mode].double)]
VERSUS = [mode for mode in GAMES if (GAMES[mode].players == 2 and
                                     not GAMES[mode].couple)]
COUPLE = [mode for mode in GAMES if GAMES[mode].couple]
ONLY_COUPLE = [mode for mode in GAMES if (GAMES[mode].couple and
                                          not GAMES[mode].double)]
DOUBLE = [mode for mode in GAMES if GAMES[mode].double]

# Convert versus modes to single modes, for grading.
VERSUS2SINGLE = {
  "VERSUS": "SINGLE",
  "3VERSUS": "3PANEL",
  "5VERSUS": "5PANEL",
  "6VERSUS": "6PANEL",
  "8VERSUS": "8PANEL",
  "9VERSUS": "9PANEL",
  "PARAVERSUS": "PARAPARA",
  "DMXVERSUS": "DMX",
  "EZ2VERSUS": "EZ2SINGLE",
  "REALVERSUS": "EZ2REAL",
}

for game in GAMES: GAMES[game].name = game
