# Colors and functions for working with colors

color = {
  _('red'): [255, 0, 0],
  _('pink'): [255, 127, 127],
  _('yellow'): [255, 255, 0],
  _('green'): [0, 255, 0],
  _('cyan'): [0, 255, 255],
  _('blue'): [0, 0, 255],
  _('purple'): [255, 0, 255],
  _('orange'): [255, 127, 0],
  _('aqua'): [0, 255, 127],
  _('white'): [255, 255, 255],
  _('black'): [0, 0, 0],
  _('gray'): [127, 127, 127]
  }

# We use these a lot, so save lookup time
WHITE = color[_("white")]
BLACK = color[_("black")]

def brighten(color, diff = 64):
  return [min(x + diff, 255) for x in color]

def darken(color, diff = 64):
  return [max(x - diff, 0) for x in color]

def darken_div(color, div = 3.5):
  return [x / div for x in color]

def average(clr1, clr2, w = 0.5):
  return [int((c1 * w + c2 * (1 - w))) for c1, c2 in zip(clr1, clr2)]
