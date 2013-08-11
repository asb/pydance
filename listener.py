# This is the base class for most of the active objects in the game.

# It basically says that the object should do nothing on all the
# events it might get.

class Listener(object):
  def __init__(self):
    raise NotImplementedError("This class should never be instantiated.")

  # change_bpm, stepped, broke_hold, and ok_hold receive the player's
  # "virtual" pid number, which is not the same as the real pid in
  # doubled modes. set_song always receives the real pid number, because
  # a song is only set once, not once for each virtual pid.

  # This is received when a hold is sucessfully completed ("OK").
  # dir is the direction of this hold.
  # whichone is a unique ID of the hold for this song.
  def ok_hold(self, pid, curtime, dir, whichone): pass

  # Received when a hold is broken ("NG") for the first time.
  def broke_hold(self, pid, curtime, dir, whichone): pass

  # Received when an arrow is stepped on or missed.
  # combo is the current combo count. rating is V (marvelous), P
  # (perfect), G (great), O (okay), B (boo), or M (miss), or None,
  # if no arrow was hit.

  # Note that since Combo objects are Listeners, the order Listeners
  # are called in *does* matter in that case.
  # etime is the "proper" time to step.
  def stepped(self, pid, dir, curtime, etime, rating, combo): pass

  # Received when a new song is started. difficulty is the name as a
  # string; count is the number of arrows in the song; feet is the
  # song rating.
  def set_song(self, pid, bpm, difficulty, count, holds, feet): pass

  # Received when the BPM of the song changes. The new BPM is given.
  def change_bpm(self, pid, curtime, bpm): pass
