import os
import math
import pygame
import fontfx
import colors
import ui
import records
import grades
import dance
import random
import options
import error
import util

from constants import *
from interface import *
from pygame.mixer import music
from fonttheme import FontTheme

from i18n import *

SORTS = {
  "subtitle": lambda x: x.info["subtitle"].lower(),
  "title": lambda x: (x.info["title"].lower(), SORTS["subtitle"](x)),
  "artist": lambda x: (x.info["artist"].lower(), SORTS["title"](x)),
  "bpm": lambda x: (x.info["bpm"], SORTS["title"](x)),
  "mix": lambda x: (x.info["mix"], SORTS["title"](x)),
  "rating": lambda x: (x.difficulty[x.diff_list[0]], SORTS["rank"](x)),
  "difficulty": lambda x: (util.difficulty_sort_key(x.diff_list[0]), SORTS["rating"](x)),
  "rank": lambda x: -records.get(x.info["recordkey"],x.diff_list[0],game)[0],
  }

SORT_DANCES = {
  "mix":False,
  "title":False,
  "artist":False,
  "bpm":False,
  "rating":True,
  "difficulty":True
  }

TEXTS = [_("subtitle"),_("title"),_("artist"),_("bpm"),_("mix"),
         _("rating"),_("difficulty"),_("rank")]

# Dance sort names define sorting formats which are tied to dance data in songs;
# therefore they can only be used if subfolders are allowed as each song may
# appear in multiple folders.
SORT_NAMES = ["mix", "title", "artist", "bpm", "rating", "difficulty"]
NUM_SORTS = len(SORT_NAMES)

SS_HELP = [
  _("Up / Down: Change song selection"),
  _("Left / Right: Change difficulty setting"),
  _("Enter / Up Right: Open a folder or start a song"),
  _("Escape / Up Left: Closes  folder or exit"),
  _("Tab / Select: Go to a random song"),
  _("Start: Go to the options screen"),
  _("F11: Toggle fullscreen - S: Change the sort mode"),
  ]

class FolderDisplay(object):
  def __init__(self, name, type, count):
    #TODO: translate name for the sorting option
    #name=_(name)
    #try:
       #name = unicode(name,"ISO-8859-15").encode("ascii","ignore")
    #except:
       #None

    self.name = name
    self._name = folder_name(name, type)
    self._type = type
    self.isfolder = True
    self.banner = None
    self.clip = None
    self.info = {}
    self.info["title"] = self._name
    self.info["artist"] = _("%d songs") % count
    self.info["subtitle"] = None

  def render(self):
    if self.banner: return

    name = self.name
    for path in [rc_path, pydance_path]:
      filename = os.path.join(path, "banners", self._type, name+".png")
      if os.path.exists(filename):
        self.banner, self.clip = load_banner(filename)
        break

    else:
      if self._type == "mix":
        for dir in mainconfig["songdir"].split(os.pathsep):
          dir = os.path.expanduser(dir)
          fn = os.path.join(dir, name, "banner.png")
          if os.path.exists(fn): self.banner, self.clip = load_banner(fn)

    if self.banner == None: self.banner = SongItemDisplay.no_banner
    self.cdtitle = pygame.Surface([0, 0])

class SongPreview(object):
  def __init__(self):
    self._playing = False
    self._filename = None
    self._end_time = self._start_time = 0
    if not mainconfig["previewmusic"]:
      music.load(os.path.join(sound_path, "menu.ogg"))
      music.play(4, 0.0)
 
  def preview(self, song):
    if mainconfig["previewmusic"] and not song.isfolder:
      if (song.info["filename"].lower().endswith("mp3") and
          mainconfig["previewmusic"] == 2):
        music.stop()
        self._playing = False
        return
      if len(song.info["preview"]) == 2:
        # A DWI/SM/dance-style preview, an offset in the song and a length
        # to play starting at the offset.
        self._start, length = song.info["preview"]
        self._filename = song.info["filename"]
      else:
        # KSF-style preview, a separate filename to play.
        self._start, length = 0, 100
        self._filename = song.info["preview"]
      if self._playing: music.fadeout(500)
      self._playing = False
      self._start_time = pygame.time.get_ticks() + 500
      self._end_time = int(self._start_time + length * 1000)
    elif song.isfolder: music.fadeout(500)

  def update(self, time):
    if self._filename is None: pass
    elif time < self._start_time: pass
    elif not self._playing:
      try:
        music.stop()
        music.load(self._filename)
        music.set_volume(0.01) # 0.0 stops pygame.mixer.music.
        # Workaround for a pygame/libsdl mixer bug.
        #music.play(0, self._start)
        music.play(0, 0)
        self._playing = True
      except: # Filename not found? Song is too short? SMPEG blows?
        music.stop()
        self.playing = False
    elif time < self._start_time + 1000: # mixer.music can't fade in
      music.set_volume((time - self._start_time) / 1000.0)
    elif time > self._end_time - 1000:
      music.fadeout(1000)
      self._playing = False
      self._filename = None

class SongSelect(InterfaceWindow):
  def __init__(self, songs, courses, screen, game):

    InterfaceWindow.__init__(self, screen, "newss-bg.png")
    songs = [s for s in songs if s.difficulty.has_key(game)]
    
    if len(songs) == 0:
      error.ErrorMessage(screen, _("You don't have any songs for the game mode (")
                         + game + _(") that you selected.")) #TODO: format using % for better i18n
      return


    # Construct a mapping between songs displays and dance displays.
    songs_and_dances = [(SongItemDisplay(s, game),
                         [DanceItemDisplay(s, game, diff) for diff in s.diff_list[game]])
                        for s in songs]

    for (s,ds) in songs_and_dances:
      for d in ds:
        s.danceitems[d.diff]=d
        d.songitem=s

    self._songs = [s[0] for s in songs_and_dances]
    self._dances = reduce(lambda x,y: x+y[1],songs_and_dances,[])

    self._index = 0
    self._game = game
    self._config = dict(game_config)
    self._all_songs = self._songs
    self._all_dances = self._dances
    self._all_valid_songs = [s for s in self._songs if s.info["valid"]]
    self._all_valid_dances = [d for d in self._dances if d.info["valid"]]

    self._list = ListBox(FontTheme.SongSel_list,
                         [255, 255, 255], 26, 16, 220, [408, 56])
    # please use set constructions after python 2.4 is adopted
    sort_name = self._update_songitems()

    if len(self._songs) > 60 and mainconfig["folders"]:
      self._create_folders()
      self._create_folder_list()
    else:
      self._folders = None
      self._base_text = sort_name.upper()

      self._songitems.sort(key=SORTS[sort_name])
      self._list.set_items([s.info["title"] for s in self._songitems])

    self._preview = SongPreview()
    self._preview.preview(self._songitems[self._index])
    self._song = self._songitems[self._index]

    # Both players must have the same difficulty in locked modes.
    self._locked = games.GAMES[self._game].couple

    players = games.GAMES[game].players
#    self._diffs = [] # Current difficulty setting
    self._diff_widgets = [] # Difficulty widgets
    self._configs = []
    self._diff_names = [] # Current chosen difficulties
    self._pref_diff_names = [] # Last manually selected difficulty names
    self._last_player = 0 # Last player to change a difficulty

    for i in range(players):
      self._configs.append(dict(player_config))
      d = DifficultyBox([84 + (233 * i), 434])
      self._pref_diff_names.append(util.DIFFICULTY_LIST[0])
      if not self._song.isfolder:
        self._diff_names.append(self._song.diff_list[0])
        diff_name = self._diff_names[i]
        rank = records.get(self._song.info["recordkey"],
                           diff_name, self._game)[0]
        grade = grades.grades[self._config["grade"]].grade_by_rank(rank)
        d.set(diff_name, DIFF_COLORS.get(diff_name, [127, 127, 127]),
              self._song.difficulty[diff_name], grade)
      else:
        self._diff_names.append(" ")        
        d.set(_("None"), [127, 127, 127], 0, "?")
      self._diff_widgets.append(d)
    
    ActiveIndicator([405, 259], width = 230).add(self._sprites)
    self._banner = BannerDisplay([205, 230])
    self._banner.set_song(self._song)
    self._sprites.add(HelpText(SS_HELP, [255, 255, 255], [0, 0, 0],
                               FontTheme.help, [206, 20]))

    self._title = TextDisplay('SongSel_sort_mode', [210, 28], [414, 27])
    self._sprites.add(self._diff_widgets +
                      [self._banner, self._list, self._title])
    self._screen.blit(self._bg, [0, 0])
    pygame.display.update()
    self.loop()
    music.fadeout(500)
    pygame.time.wait(500)
    # FIXME Does this belong in the menu code? Probably.
    music.load(os.path.join(sound_path, "menu.ogg"))
    music.set_volume(1.0)
    music.play(4, 0.0)
    player_config.update(self._configs[0]) # Save p1's settings

  def loop(self):
    pid, ev = ui.ui.poll()
    self._list.set_index(self._index)
    self._title.set_text(self._base_text + " - %d/%d" % (self._index + 1,
                                                         len(self._songitems)))
    while not (ev == ui.CANCEL and (not self._folders or self._song.isfolder)):
      # Inactive player. If the event isn't set to ui.PASS, we try to use
      # the pid later, which will be bad.
      if pid >= len(self._diff_names): ev = ui.PASS
      
      elif ev == ui.UP: self._index -= 1
      elif ev == ui.DOWN: self._index += 1
      elif ev == ui.PGUP:
        self._index -= 7
        ev = ui.UP
      elif ev == ui.PGDN:
        self._index += 7
        ev = ui.DOWN

      elif ev == ui.LEFT:
        if not self._song.isfolder:
          namei = self._song.diff_list.index(self._diff_names[pid])
          namei = (namei -1) % len(self._song.diff_list)
          name = self._song.diff_list[namei]
          self._diff_names[pid] = name
          self._pref_diff_names[pid] = name
          self._last_player = pid

      elif ev == ui.RIGHT:
        if not self._song.isfolder:
          namei = self._song.diff_list.index(self._diff_names[pid])
          namei = (namei + 1) % len(self._song.diff_list)
          name = self._song.diff_list[namei]
          self._diff_names[pid] = name
          self._pref_diff_names[pid] = name
          self._last_player = pid

      elif ev == ui.SELECT:
        if self._song.isfolder:
          if len(self._all_valid_songitems) > 0:
            self._song = random.choice(self._all_valid_songitems)
            fol = self._song.folder[SORT_NAMES[mainconfig["sortmode"]]]
            self._create_song_list(fol)
            self._index = self._songitems.index(self._song)      
          else:
            error.ErrorMessage(screen,
                               _("You don't have any songs that are marked ") +
                               _("\"valid\" for random selection."))
        else:
          valid_songs = [s for s in self._songitems if s.info["valid"]]
          if len(valid_songs) > 0:
            self._song = random.choice(valid_songs)
            self._index = self._songitems.index(self._song)
          else:
            error.ErrorMessage(screen, _("You don't have any songs here that ") +
                               _("are marked \"valid\" for random selection."))
      elif ev == ui.START:
        options.OptionScreen(self._configs, self._config, self._screen)
        self._screen.blit(self._bg, [0, 0])
        self.update()
        pygame.display.update()

      elif ev == ui.SORT:
        s = self._songitems[self._index]
        mainconfig["sortmode"] = (mainconfig["sortmode"] + 1) % NUM_SORTS
        sort_name = self._update_songitems()
        if self._folders:
          if s.isfolder:
            self._create_folder_list()
          else:
            s = self._find_resorted()
            self._create_song_list(s.folder[sort_name])
            self._index = self._songitems.index(s)
        else:
          s = self._find_resorted()
          self._base_text = _(sort_name).upper()
          self._songitems.sort(key=SORTS[sort_name])
          self._index = self._songitems.index(s)
          self._list.set_items([s.info["title"] for s in self._songitems])

      elif ev == ui.CONFIRM:
        if self._song.isfolder:
          self._create_song_list(self._song.name)
          self._index = 0
        else:
          music.fadeout(500)
          dance.play(self._screen, [(self._song.filename, self._diff_names)],
                     self._configs, self._config, self._game)
          music.fadeout(500) # The just-played song
          self._screen.blit(self._bg, [0, 0])
          pygame.display.update()
          ui.ui.clear()

      elif ev == ui.CANCEL:
        # first: get the parent folder of the active song
        sort_name = SORT_NAMES[mainconfig["sortmode"]]
        fol = folder_name(self._song.folder[sort_name], sort_name)
        # next: change folder
        self._create_folder_list()
        for d in self._diff_widgets:
          d.set("None", [127, 127, 127], 0, "?")

        lst = [s.info["title"] for s in self._songitems]
        self._index = lst.index(fol)

      elif ev == ui.FULLSCREEN:
        mainconfig["fullscreen"] ^= 1
        pygame.display.toggle_fullscreen()

      self._index %= len(self._songitems)
      self._song = self._songitems[self._index]

      if self._locked and ev in [ui.LEFT, ui.RIGHT]:
        for i, sd in enumerate(self._diff_names):
          self._diff_names[i] = self._diff_names[pid]
          self._pref_diff_names[i] = self._diff_names[pid]

      if ev in [ui.CANCEL, ui.UP, ui.DOWN, ui.SELECT, ui.CONFIRM, ui.SORT]:
        self._preview.preview(self._song)
        self._banner.set_song(self._song)

      if ev in [ui.CANCEL, ui.UP, ui.DOWN, ui.SELECT, ui.CONFIRM, ui.SORT]:
        if ev == ui.UP: self._list.set_index(self._index, -1)
        elif ev == ui.DOWN: self._list.set_index(self._index, 1)
        else: self._list.set_index(self._index, 0) # don't animate
        self._title.set_text(self._base_text + " - %d/%d" % (self._index + 1,
                                                             len(self._songitems)))

      if ev in [ui.UP, ui.DOWN, ui.SELECT, ui.SORT, ui.CONFIRM]:
        if not self._song.isfolder:
          for pl, dname in enumerate(self._diff_names):
            name = self._pref_diff_names[pl]
            if name in self._song.diff_list:
               self._diff_names[pl] = name
            elif self._unify_difficulties(name) in self._song.diff_list:
               self._diff_names[pl] = self._unify_difficulties(name)
            else: 
              # if both name and the song's difficulty list can be indexed:
              # find the nearest defined difficulty
              if  (name in util.DIFFICULTY_LIST or
                  self._unify_difficulties(name) in util.DIFFICULTY_LIST) and \
                  reduce(lambda a,b: a and b in util.DIFFICULTY_LIST, 
                         self._song.diff_list , True ):
                name = self._unify_difficulties(name)
                namei = util.DIFFICULTY_LIST.index(name)
                diffi = [util.DIFFICULTY_LIST.index(d) for 
                                        d in self._song.diff_list]
                dds = [abs(d - namei) for d in diffi]
                self._diff_names[pl] = self._song.diff_list\
                                                          [dds.index(min(dds))]
              else: # no sensible way to resolve this: jump to middle of list
                difflen = len(self._song.diff_list)
                self._diff_names[pl] = self._song.diff_list[difflen/2]
          
      if ev in [ui.UP, ui.DOWN, ui.LEFT, ui.RIGHT, ui.SELECT, ui.CONFIRM]:
        if not self._song.isfolder:
          for i, name in enumerate(self._diff_names):
            rank = records.get(self._song.info["recordkey"],
                               name, self._game)[0]
            grade = grades.grades[self._config["grade"]].grade_by_rank(rank)
            self._diff_widgets[i].set(name,
                                      DIFF_COLORS.get(name, [127,127,127]),
                                      self._song.difficulty[name],
                                    grade)
      
      self.update()
      pid, ev = ui.ui.poll()

  def update(self):
    InterfaceWindow.update(self)
    self._preview.update(pygame.time.get_ticks())

  # Gets rid of superfluous/misspelled difficulties for sorting purposes.
  # Return the difficulty if it's ok, however map S-MANIAC to SMANIAC.
  # Return an existing difficulty if at least the first three characters 
  # are the same.
  def _unify_difficulties(self, difficulty):
    diff = difficulty.upper()
    if not diff in util.DIFFICULTY_LIST:
      diffs = [d for d in util.DIFFICULTY_LIST \
                               if d.startswith(diff[:2])]
      if len(diffs)>0: diff = diffs[0]
      else: diff = "other"
    if diff=="S-MANIAC": diff = "SMANIAC" # see constants.DIFF_COLORS
    return diff
    
  def _create_folders(self):
    mixes = {}
    artists = {}
    titles = {}
    bpms = {}
    difficulties = {}
    ratings = {}

    for s in self._all_songs:
      if s.info["mix"] not in mixes: mixes[s.info["mix"]] = []
      mixes[s.info["mix"]].append(s)
      s.folder["mix"] = s.info["mix"]

      label = s.info["title"][0].capitalize()
      if label not in titles: titles[label] = []
      titles[label].append(s)
      s.folder["title"] = label

      label = s.info["artist"][0].capitalize()
      if label not in artists: artists[label] = []
      artists[label].append(s)
      s.folder["artist"] = label

      for rng in ((0, 50), (50, 100), (100, 121), (110, 120), (120, 130),
                  (130, 140), (140, 150), (150, 160), (160, 170), (170, 180),
                  (180, 190), (190, 200), (200, 225), (225, 250), (250, 275),
                  (275, 299.99999999)):
        if rng[0] < s.info["bpm"] <= rng[1]:
          label = "%3d - %3d" % rng
          if not label in bpms: bpms[label] = []
          bpms[label].append(s)
          s.folder["bpm"] = label
      if s.info["bpm"] >= 300:
        if "300+" not in bpms: bpms["300+"] = []
        bpms["300+"].append(s)
        s.folder["bpm"] = "300+"
    for s in self._all_dances:
      difficulty = self._unify_difficulties(s.diff_list[0])
      label = difficulty
      if not label in difficulties: difficulties[label]=[]
      difficulties[label].append(s)
      # s.folder["difficulty"] is only initialised here.
      if "difficulty" in s.folder.keys():
        # min() can't handle arbitrary comparators, so:
        if util.difficulty_sort(s.folder["difficulty"], label)<=0 :
          s.folder["difficulty"] = s.folder["difficulty"]
        else: s.folder["difficulty"] = label
      else:
        s.folder["difficulty"] = label

      rating = s.difficulty.values()[0]
      label = "%2d" % rating
      if not label in ratings: ratings[label]=[]
      ratings[label].append(s)
      # s.folder["rating"] is only initialised here.
      if "rating" in s.folder.keys():
        s.folder["rating"] = min(s.folder["rating"], label) 
      else:
        s.folder["rating"] = label
        
    self._folders = { "mix": mixes, "title": titles, "artist": artists,
                      "bpm": bpms, "rating": ratings, "difficulty": difficulties }

  def _create_folder_list(self):
    sort_name = SORT_NAMES[mainconfig["sortmode"]]
    lst = self._folders[sort_name].keys()
    lst.sort(lambda x, y: cmp(x.lower(), y.lower()))
    new_songs = [FolderDisplay(folder, sort_name,
                               len(self._folders[sort_name][folder])) for
                 folder in lst]
    self._songitems = new_songs
    self._list.set_items([s.info["title"] for s in self._songitems])
    self._base_text = _("Sort by %s") % _(sort_name).capitalize()
    
  def _create_song_list(self, folder):
    # folder contains a sorting criterion value in string format
    sort_name = SORT_NAMES[mainconfig["sortmode"]]
    songlist = self._folders[sort_name][folder]
    
    songlist.sort(key=SORTS[sort_name])
    
    self._songitems = songlist
    self._list.set_items([s.info["title"] for s in self._songitems])
    if self._folders: self._base_text = folder_name(folder, sort_name)

  def _update_songitems(self):
    sort_name = SORT_NAMES[mainconfig["sortmode"] % NUM_SORTS]
    if SORT_DANCES[sort_name]:
      self._songitems = self._dances
      self._all_songitems = self._all_dances
      self._all_valid_songitems = self._all_valid_dances
    else:
      self._songitems = self._songs
      self._all_songitems = self._all_songs
      self._all_valid_songitems = self._all_valid_songs

    return sort_name

  def _find_resorted(self):
    if isinstance(self._song, SongItemDisplay) and \
       SORT_DANCES[SORT_NAMES[mainconfig["sortmode"] % NUM_SORTS]]:
      diff = self._diff_names[self._last_player]
      return self._song.danceitems[diff]
    elif isinstance(self._song, DanceItemDisplay) and \
         not SORT_DANCES[SORT_NAMES[mainconfig["sortmode"] % NUM_SORTS]]:
      return self._song.songitem
    else: return self._song
