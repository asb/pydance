from constants import *

from util import toRealTime
from announcer import Announcer
from listener import Listener

# The judge is responsible for correlating step times and arrows times,
# and then rating them (V/P/G/O/B), as well as expiring arrows when
# they're missed. Listener objects get their information from the judge,
# which is also a Listener itself.

class AbstractJudge(Listener):
  def __init__ (self, pid, songconf):
    self._pid = pid
    self._scale = songconf["judgescale"]
    self._ann = Announcer(mainconfig["djtheme"])

  def set_song(self, pid, bpm, difficulty, count, holds, feet):
    self.holdsub = {}
    self._steps = {}
    # Hidden steps were first used in Technomotion. They count for points,
    # if you hit them, but you can't miss them.
    self._hidden_steps = {}

  def broke_hold(self, pid, curtime, dir, whichone):
    if pid != self._pid: return
    if self.holdsub.get(whichone) != -1: self.holdsub[whichone] = -1

  # Handle a key press and see if it can be associated with an upcoming
  # arrow; rate it if so.
  def handle_key(self, dir, curtime):
    times = self._steps.keys()
    times.sort()
    etime = 0.0
    done = 0
    rating = None
    off = -1
    for t in times:
      if dir in self._steps[t]:
        rating = self._get_rating(curtime, t)
        if rating != None:
          etime = t
          self._steps[etime] = self._steps[etime].replace(dir, "")
          if etime in self._hidden_steps:
            self._hidden_steps[etime].replace(dir, "")
          break

    return rating, dir, etime

  # Add an arrow to the list of steps to be checked on a keypress.
  def handle_arrow(self, key, etime, is_hidden):
    if etime in self._steps: self._steps[etime] += key
    else: self._steps[etime] = key

    if is_hidden:
      if etime in self._hidden_steps: self._hidden_steps[etime] += key
      else: self._hidden_steps[etime] = key

  # Mark arrows that are very old as misses.
  def expire_arrows(self, curtime):
    times = self._steps.keys()
    misses = ""
    for time in times:
      if self._is_miss(curtime, time) and self._steps[time]:
        for d in self._hidden_steps.get(time, ""):
          self._steps[time] = self._steps[time].replace(d, "")
        misses += self._steps[time]
        del(self._steps[time])
    return misses

  # Check whether or not an arrow is a miss.
  def _is_miss(self, curtime, time):
    raise NotImplementedError("This class should not be instantiated.")

  # Rate a (possible) step.
  def _get_rating(self, curtime, time):
    raise NotImplementedError("This class should not be instantiated.")

# This judge rates steps based on constant time offsets (although
# multiplied by scale).
class TimeJudge(AbstractJudge):

  def __init__ (self, pid, songconf):
    AbstractJudge.__init__(self, pid, songconf)
    self._v = self._scale * 0.0225
    self._p = self._scale * 0.045
    self._g = self._scale * 0.090
    self._o = self._scale * 0.135
    self._b = self._scale * 0.180
    self.ok_time = self._scale * 0.25
  
  def _get_rating(self, curtime, t):
    offset = abs(curtime - t)
    if offset < self._v: return "V"
    elif offset < self._p: return "P"
    elif offset < self._g: return "G"
    elif offset < self._o: return "O"
    elif offset < self._b: return "B"
    else: return None

  def _is_miss(self, curtime, time): return time < curtime - self._b

# This judge rates steps based on what fraction of a beat they are from
# the correct time, and therefore makes fast songs much harder, and slow
# songs easier.
class BeatJudge(AbstractJudge):

  def set_song(self, pid, bpm, difficulty, count, holds, feet):
    AbstractJudge.set_song(self, pid, bpm, difficulty, count, holds, feet)
    self._tick = toRealTime(bpm, 0.16666666666666666)
    self._v = self._scale * 1
    self._p = self._scale * 4
    self._g = self._scale * 7
    self._o = self._scale * 9
    self._b = self._scale * 12
    self.ok_time = toRealTime(bpm, 2) * self._scale
    self._b_ticks = self._b * self._tick
  
  def change_bpm(self, pid, curtime, bpm):
    if self._pid != pid: return
    if bpm >= 1: self._tick = toRealTime(bpm, 0.16666666666666666)
    self._v = self._scale * 1
    self._p = self._scale * 4
    self._g = self._scale * 7
    self._o = self._scale * 9
    self._b = self._scale * 12
    self.ok_time = toRealTime(bpm, 2) * self._scale
    self._b_ticks = self._b * self._tick

  def _get_rating(self, curtime, t):
    off = abs((curtime - t) / self._tick)
    if off <= self._v: return "V"
    elif off <= self._p: return "P"
    elif off <= self._g: return "G"
    elif off <= self._o: return "O"
    elif off < self._b: return "B"
    else: return None

  def _is_miss(self, curtime, time): return time < curtime - self._b

judges = [TimeJudge, BeatJudge]
judge_opt = [
  (0, _("Time"),
   _("Judging is based on how many seconds you are from the correct time.")),
  (1, _("Beat"),
   _("Judging is based on how many beats you are from the correct time.")),
  ]
