# Store information about player records

from constants import *
import cPickle as pickle
import grades
import games

record_fn = os.path.join(rc_path, "records")

try: records = pickle.load(file(record_fn, "r"))
except: records = {}
bad_records = {}

# Before starting, move any records we don't know about into a different hash,
# so we don't try to load them for player's {best,worst}.
# Do store them however, so when the songs appear again they'll be valid.
def verify(recordkeys):
  for k in records.keys():
    if k[0] not in recordkeys:
      bad_records[k] = records[k]
      del(records[k])
    elif len(records[k]) < 3: records[k] += (1,)
  
# records maps the title, mix, difficulty, and game onto a tuple
# (rank, name) where rank is a floating point number from 0 to 1; and
# name is the name of the player who made the score.

# recordkey is a string of the mix, title, and subtitle, concatenated,
# lowercased, with non-alphanumerics removed.

# A score is considered "beaten" (and therefore deserving of a new name
# value) when the new rank is greater than the old rank.

# The actual "grade" is calculated via grades.py, from the rank. This is
# done in the song selector.

def add(recordkey, diff, game, rank, name):
  game = games.VERSUS2SINGLE.get(game, game)
  t = (recordkey, diff, game)
  if t in records:
    if rank > records[t][0]:
      records[t] = (rank, name, records[t][2] + 1)
      return True
    else:
      records[t] = records[t][:2] + (records[t][2] + 1,)
      return False
  else:
    records[t] = (rank, name, 1)
    return True

def get(recordkey, diff, game):
  game = games.VERSUS2SINGLE.get(game, game)
  return records.get((recordkey, diff, game), (-1, ""))

def write():
  r = {}
  r.update(bad_records)
  r.update(records)
  pickle.dump(r, file(record_fn, "w"), 2)

# Highest scores
def best(index, diffs, game):
  game = games.VERSUS2SINGLE.get(game, game)
  if not isinstance(diffs, list): diffs = [diffs]
  index -= 1
  r = [(v[0], k[0]) for k, v in records.items() if
       (k[1] in diffs and k[2] == game)] 
  if len(r) == 0: return None
  r.sort()
  r.reverse()
  index %= len(r)
  return r[index][1]

# Lowest scores
def worst(index, diffs, game):
  game = games.VERSUS2SINGLE.get(game, game)
  index -= 1
  if not isinstance(diffs, list): diffs = [diffs]
  r = [(v[0], k[0]) for k, v in records.items() if
       (k[1] in diffs and k[2] == game)] 
  if len(r) == 0: return None
  r.sort()
  index %= len(r)
  return r[index][1]

# Most-played songs
def like(index, diffs, game):
  game = games.VERSUS2SINGLE.get(game, game)
  if not isinstance(diffs, list): diffs = [diffs]
  index -= 1
  r = [(v[2], k[0]) for k, v in records.items() if
       (k[1] in diffs and k[2] == game)] 
  if len(r) == 0: return None
  r.sort()
  r.reverse()
  index %= len(r)
  return r[index][1]

# Least-played songs
def dislike(index, diffs, game):
  game = games.VERSUS2SINGLE.get(game, game)
  index -= 1
  if not isinstance(diffs, list): diffs = [diffs]
  r = [(v[2], k[0]) for k, v in records.items() if
       (k[1] in diffs and k[2] == game)] 
  if len(r) == 0: return None
  r.sort()
  index %= len(r)
  return r[index][1]
