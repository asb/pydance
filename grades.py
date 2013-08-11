from listener import Listener

# This will *probably* never have anything in it...
class AbstractGrade(Listener): pass

# DDR 6th-8th mix "dance points" grading. This is IMO one of the
# fairest grading algorithms and definitely one of the most common.
class DancePointsGrade(AbstractGrade):
  def grade_by_rank(cls, rank):
    if rank >= 1.00: return "AAA"
    elif rank >= 0.93: return "AA"
    elif rank >= 0.80: return "A"
    elif rank >= 0.65: return "B"
    elif rank >= 0.45: return "C"
    elif rank == -2: return "F"
    elif rank == -1: return "?"
    else: return "D"
    
  grade_by_rank = classmethod(grade_by_rank)

  def __init__(self):
    self.score = 0
    self.arrow_count = 0
    self.hold_count = 0
    self.inc = { "V": 2, "P": 2, "G": 1, "B": -4, "M": -8 }

  def ok_hold(self, pid, curtime, dir, whichone):
    self.hold_count += 1
    self.score += 6

  def broke_hold(self, pid, curtime, dir, whichone):
    self.hold_count += 1

  def stepped(self, pid, dir, cur_time, etime, rating, combo):
    self.arrow_count += 1
    self.score += self.inc.get(rating, 0)

  def rank(self):
    max_score = float(2 * self.arrow_count + 6 * self.hold_count)
    if max_score == 0: return 0
    else: return (self.score / max_score)

  def grade(self, failed):
    if failed == True: return "F"
    else: return DancePointsGrade.grade_by_rank(self.rank())

# Appropriate for endless mode, it doesn't return E on failure (since
# endless mode always ends in a failure).
class EndlessGrade(DancePointsGrade):
  def grade(self, failed): return DancePointsGrade.grade(self, False)

grades = [DancePointsGrade, EndlessGrade]
grade_opt = [
  (0, _("Dance Points"), ""),
  (1, _("Endless"),
   _("Like dance points, but failing doesn't result in an F.")),
  ]
