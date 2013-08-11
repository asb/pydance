# These parse various file formats describing steps.
# Please read docs/dance-spec.txt

import colors
import games
import stepfilters

from lyrics import Lyrics
from util import toRealTime
from constants import *

from pygame.mixer import music

# FIXME: This can probably be replaced by something smaller, like a tuple.
class SongEvent(object):
  def __init__ (self, bpm, when=0.0, beat = 0, feet=None, next=None,
                extra=None, color=None, appear=None):
    self.bpm  = bpm
    self.when = when
    self.appear = appear
    self.feet = feet
    self.extra = extra
    self.color = color
    self.beat = beat

  def __repr__(self):
    rest = []
    if self.feet: rest.append('feet=%r'%self.feet)
    if self.extra: rest.append('extra=%r'%self.extra)
    if self.extra: rest.append('color=%r'%self.color)
    if self.appear: rest.append('appear=%r'%self.appear)
    return '<SongEvent when=%r bpm=%r %s>' % (self.when,self.bpm,
                                                ' '.join(rest))

# Step objects, made from SongItem objects

class Steps(object):
  def __init__(self, song, difficulty, player, pid, lyrics, playmode):
    self.playmode = playmode
    self.difficulty = difficulty
    self.feet = song.difficulty[playmode][difficulty]
    self.length = 0.0
    self.offset = -(song.info["gap"] + mainconfig['masteroffset']) / 1000.0
    self.soffset = self.offset * 1000
    self.bpm = song.info["bpm"]

    if mainconfig['onboardaudio']:
      self.offset = int(self.offset * 48000.0/44128.0)
      self.bpm = self.bpm * 48000.0/44128.0

    self.lastbpmchangetime = []
    self.totalarrows = 0
    self.ready = None

    offbeat_color_mod = 3

    holdlist = []
    holdtimes = []
    holdbeats = []
    releaselist = []
    releasetimes = []
    releasebeats = []
    self.numholds = 1
    holding = [0] * len(games.GAMES[playmode].dirs)
    coloring_mod = 0
    cur_time = float(self.offset)
    last_event_was_freeze = False
    cur_beat = 0
    cur_bpm = self.bpm
    if player.target_bpm is not None:
      self.target_bpm = player.target_bpm * 1.0
      self.speed = None
    else:
      self.target_bpm = None

    # If *_lead is too small, arrows don't appear fast enough. If it's
    # too large, many arrows queue up and pydance slows down.
    # 6.5 == (480 (screen height) - 64 (space on top)) / 64 (pixels per beat)
    # If we have a constant "speed", use beats. If we have a constant effective
    # BPM, use time.
    if self.target_bpm is None:
      beat_lead = 6.5 / player.speed
    else:
      time_lead = 6.5 / self.target_bpm * 60

    # self.lastbpmchangetime is used in several places. For most purposes, the
    # initial BPM setting is not considered a BPM change, but for the purpose
    # of back-tracking to find the number of seconds corresponding to a given
    # number of beats at a certain point in the song, it is, so it is initialized
    # here, and the first element is deleted later.
    self.lastbpmchangetime = [[0.0,self.bpm]]
    self.events = [SongEvent(when = cur_time, bpm = cur_bpm, beat = cur_beat,
                             extra = song.difficulty[playmode][difficulty])]

    self.event_idx = 0
    self.nevent_idx = 0

    if playmode in song.steps:
      song_steps = song.steps[playmode][difficulty]
      if playmode in games.COUPLE: song_steps = song_steps[pid]
      # Copy the steps so transformations don't affect both players.
      song_steps = [list(s) for s in song_steps]
    else:
      song_steps = stepfilters.generate_mode(song, difficulty, playmode, pid)

    song_steps = stepfilters.compress(song_steps)

    if player.transform:
      T = stepfilters.rotate[player.transform]
      song_steps = T(playmode).transform(song_steps)

    if not player.holds:
      song_steps = stepfilters.RemoveHoldTransform().transform(song_steps)
    if player.size: stepfilters.size(song_steps, player.size)
    if player.jumps != 1:
      song_steps = stepfilters.jumps[player.jumps]().transform(song_steps)

    if not player.secret_kind:
      song_steps = stepfilters.RemoveSecret().transform(song_steps)

    for words in song_steps:

      if words[0] == 'W':
        cur_time += float(words[1])
        cur_beat += cur_bpm * float(words[1]) / 60
        last_event_was_freeze = False
      elif words[0] == 'R':
        self.ready = cur_time
        last_event_was_freeze = False
        coloring_mod = 0
      elif isinstance(words[0], float):
        # Don't create arrow events with no arrows
        arrowcount = 0
        for i in words[1:]: arrowcount += int(i)

        if arrowcount != 0:
          feetstep = words[1:]

          if last_event_was_freeze:
            time_to_add = last_event_was_freeze
            last_event_was_freeze = False
          else: time_to_add = cur_time

          # Check for holds
          for hold,fs in enumerate(feetstep):
            h = holding[hold]
            if fs & 2 and h == 0:
              holdtimes.insert(self.numholds, time_to_add)
              holdbeats.insert(self.numholds, cur_beat)
              holdlist.insert(self.numholds, hold)
              releasetimes.append(None)
              releasebeats.append(None)
              releaselist.append(None)
              h = holding[hold] = self.numholds
              self.numholds += 1

            elif (fs and holding[hold]):
              releasetimes[h - 1] = time_to_add
              releasebeats[h - 1] = cur_beat
              releaselist[h - 1] = hold
              fs = feetstep[hold] = 0
              h = holding[hold] = 0

          if coloring_mod == int(coloring_mod):
            color = coloring_mod % 4
            if color == 3: color = 1
            offbeat_color_mod = 3
          else:
            color = offbeat_color_mod
            offbeat_color_mod ^= 2

          if self.target_bpm is None:
            # Backtrack through BPM changes until we hit the BPM segment the
            # correct number of beats before this step, and then find the right
            # time within that segment when the arrow should first be visible.
            beat_led=beat_lead
            bpm_i=-1
            time_led=0.0

            while time_to_add-time_led>0 and beat_led>(time_to_add-time_led-self.lastbpmchangetime[bpm_i][0])*self.lastbpmchangetime[bpm_i][1]/60:
              beat_led-=(time_to_add-time_led-self.lastbpmchangetime[bpm_i][0])*self.lastbpmchangetime[bpm_i][1]/60
              time_led=time_to_add-self.lastbpmchangetime[bpm_i][0]
              bpm_i-=1
              
            if time_to_add<=time_led:
              time_led=time_to_add
            else:
              time_led+=beat_led/self.lastbpmchangetime[bpm_i][1]*60
          else:
            time_led=time_lead
          self.events.append(SongEvent(when = time_to_add, bpm = cur_bpm,
                                       feet = feetstep, extra = words[0],
                                       beat = cur_beat,
                                       color = color,
                                       appear = max(time_to_add-time_led,0)))

          for arrowadder in feetstep:
            if arrowadder & 1 and not arrowadder & 4:
              self.totalarrows += 1

        # Even if there are no steps in the event, we don't want to
        # propogate the freeze.
        else: last_event_was_freeze = False

        beat = words[0]

        cur_time += toRealTime(cur_bpm, beat)
        cur_beat += beat
        coloring_mod += beat

        if int(coloring_mod + 0.0001) > int(coloring_mod):
          coloring_mod = float(int(coloring_mod + 0.0001))
        if int(cur_beat + 0.0001) > int(cur_beat):
          cur_beat = float(int(cur_beat + 0.0001))

      elif words[0] == "D":
        last_event_was_freeze = False
        cur_time += toRealTime(cur_bpm, 4.0 * words[1])
        cur_beat += 4.0 * words[1]
        coloring_mod += 4 * words[1]

      elif words[0] == "B":
        cur_bpm = words[1]
        last_event_was_freeze = False
        self.lastbpmchangetime.append([cur_time, cur_bpm])

      elif words[0] == "S":
        # We can treat stops as a BPM change to zero with a wait.
        last_event_was_freeze = cur_time
        self.lastbpmchangetime.append([cur_time, 1e-127]) # This is zero
        cur_time += float(words[1])
        self.lastbpmchangetime.append([cur_time, cur_bpm])

      elif words[0] == "L" and lyrics:
        lyrics.addlyric(cur_time - 0.4, words[1], words[2])

    self.length = cur_time + toRealTime(cur_bpm, 8.0)

    self.holdinfo = zip(holdlist, holdtimes, releasetimes)
    self.holdref = zip(holdlist, holdtimes)
    self.holdbeats = zip(holdbeats, releasebeats)

    if self.ready == None:
      if len(self.events) > 1:
        self.ready = self.events[1].when - toRealTime(self.events[1].bpm, 16)
      else: self.ready = 0.0

    # Delete the initial setting of BPM.
    del self.lastbpmchangetime[0]

  def play(self):
    self.curtime = 0.0
    self.event_idx = self.nevent_idx = 0
    self.playingbpm = self.bpm

  def get_events(self):
    events, nevents = [], []
    idx = self.event_idx
    nidx = self.nevent_idx
    time = self.curtime = float(music.get_pos())/1000.0
    while (idx < len(self.events) and
           self.events[idx].when <= time + 2 * toRealTime(self.events[idx].bpm, 1)):
      events.append(self.events[idx])
      idx += 1

    bpm = self.playingbpm
    self.event_idx = idx
    
    while (nidx < len(self.events) and self.events[nidx].appear <= time):
      self.playingbpm = self.events[nidx].bpm
      nevents.append(self.events[nidx])
      nidx += 1   
    self.nevent_idx = nidx

    return events, nevents, time, bpm

# Player-indep data generated from SongItem.

class SongData(object):
  def __init__(self, song, config):
    if song.info["background"]: self.background = song.info["background"]
    else: self.background = os.path.join(image_path, "bg.png")

    for key in ["movie", "filename", "title", "artist", "startat", "endat",
                "banner"]:
      self.__dict__[key] = song.info[key]

    self.soffset = song.info["gap"] * 1000

    self.crapout = 0

    self.__dict__.update(config)

    try:
        # if user used some internationalization in the configuration file,
	# so in mainconfig["lyriccolor"], maybe there is invalid colors
	# TODO: not save translated colors in the config file, only English
        clrs = [colors.color[_(c)] for c in mainconfig["lyriccolor"].split("/")]
    except:
        clrs = ["cyan","aqua"]

    clrs.reverse()
    self.lyricdisplay = Lyrics(clrs)

    atsec = 0
    for lyr in song.lyrics:
      self.lyricdisplay.addlyric(*lyr)

  def init(self):
    try: music.load(self.filename)
    except:
      print _("Not a supported file type:"), self.filename
      self.crapout = 1

  def play(self):
    music.play(0, self.startat)

  def kill(self):
    music.stop()

  def is_over(self):
    if not music.get_busy(): return True
    elif self.endat and music.get_pos() > self.endat * 1000:
      music.stop()
      return True
    else: return False
