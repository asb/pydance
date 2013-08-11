from math import sqrt
from listener import Listener

# Track statistics about the kind of steps being made.
class Stats(Listener):
  def __init__(self):
    self.hold_count = 0
    self.bad_holds = 0
    self.good_holds = 0
    self.arrow_count = 0
    self.maxcombo = 0
    self.steps = { "V": 0, "P": 0, "G": 0, "O": 0, "B": 0, "M": 0 }
    self.early = self.late = self.ontime = 0
    self._times = []

  def stepped(self, pid, dir, curtime, etime, rating, combo):
    if rating is None: return

    if combo > self.maxcombo: self.maxcombo = combo
    self.steps[rating] += 1
    self.arrow_count += 1

    if curtime > etime: self.late += 1
    elif etime > curtime: self.early += 1
    else: self.ontime += 1

    if rating != "M" and rating != None:
      self._times.append(etime - curtime)

  def times(self):
    s = sum(self._times)
    avg = s / len(self._times)
    s2 = sum([(i - avg)**2 for i in self._times])
    stddev = sqrt(s2 / (len(self._times) - 1))
    return avg, stddev

  def ok_hold(self, pid, time, dir, whichone):
    self.hold_count += 1
    self.good_holds += 1

  def broke_hold(self, pid, time, dir, whichone):
    self.hold_count += 1
    self.bad_holds += 1

  def __getitem__(self, item): return self.steps[item]
