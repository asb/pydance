import fontfx
import colors
import steps
import random
import arrows
import lifebars
import scores
import combos
import grades
import judge
import stats

from constants import *
from pad import pad

from util import toRealTime
from gfxtheme import GFXTheme
from announcer import Announcer

from listener import Listener

from pygame.sprite import RenderUpdates, RenderClear

from fonttheme import FontTheme

# This class keeps an ordered list of sprites in addition to the dict,
# so we can draw in the order the sprites were added.
class OrderedRenderUpdates(RenderClear):
  def __init__(self, group = ()):
    self.spritelist = []
    RenderClear.__init__(self, group)

  def sprites(self):
    return list(self.spritelist)

  # A patch has been sent to Pete in the hopes that we can avoid overriding
  # this function, and only override add_internal (pygame 1.5.6)
  def add(self, sprite):
    has = self.spritedict.has_key
    if hasattr(sprite, '_spritegroup'):
      for sprite in sprite.sprites():
        if not has(sprite):
          self.add_internal(sprite)
          sprite.add_internal(self) 
    else:
      try: len(sprite)
      except (TypeError, AttributeError):
        if not has(sprite):
          self.add_internal(sprite)
          sprite.add_internal(self) 
      else:
        for sprite in sprite:
          if not has(sprite):
            self.add_internal(sprite)
            sprite.add_internal(self) 

  def add_internal(self, sprite):
    RenderClear.add_internal(self, sprite)
    self.spritelist.append(sprite)

  def remove_internal(self, sprite):
    RenderClear.remove_internal(self, sprite)
    self.spritelist.remove(sprite)

  def draw(self, surface):
    spritelist = self.spritelist
    spritedict = self.spritedict
    surface_blit = surface.blit
    dirty = self.lostsprites
    self.lostsprites = []
    dirty_append = dirty.append
    for s in spritelist:
      r = spritedict[s]
      newrect = surface_blit(s.image, s.rect)
      if r is 0:
        dirty_append(newrect)
      else:
        if newrect.colliderect(r):
          dirty_append(newrect.union(r))
        else:
          dirty_append(newrect)
      spritedict[s] = newrect
    return dirty

class HoldJudgeDisp(Listener, pygame.sprite.Sprite):
  def __init__(self, pid, player, game):
    pygame.sprite.Sprite.__init__(self)
    self.pid = pid
    self.game = game

    self.space = pygame.surface.Surface([48, 24])
    self.space.fill([0, 0, 0])

    self.image = pygame.surface.Surface([len(game.dirs) * game.width, 24])
    self.image.fill([0, 0, 0])
    self.image.set_colorkey([0, 0, 0], RLEACCEL)

    self.okimg = fontfx.shadefade(_("OK"), FontTheme.Dance_hold_judgment, 3, [48, 24], [112, 224, 112])
    self.ngimg = fontfx.shadefade(_("NG"), FontTheme.Dance_hold_judgment, 3, [48, 24], [224, 112, 112])

    self.rect = self.image.get_rect()
    if player.scrollstyle == 2: self.rect.top = 228
    elif player.scrollstyle == 1: self.rect.top = 400
    else: self.rect.top = 56

    self.rect.left = game.left_off(pid) + pid * game.player_offset
    self.len = len(game.dirs)

  def set_song(self, pid, bpm, difficulty, count, holds, feet):
    self.slotnow = [self.space] * self.len
    self.slotold = list(self.slotnow)
    self.slothit = [-1] * self.len

  def ok_hold(self, pid, curtime, direction, whichone):
    if pid != self.pid: return
    self.slothit[self.game.dirs.index(direction)] = curtime
    self.slotnow[self.game.dirs.index(direction)] = self.okimg

  def broke_hold(self, pid, curtime, direction, whichone):
    if pid != self.pid: return
    self.slothit[self.game.dirs.index(direction)] = curtime
    self.slotnow[self.game.dirs.index(direction)] = self.ngimg
    
  def update(self, curtime):
    for i,s in enumerate(self.slotnow):
      if (curtime - self.slothit[i] > 0.5):
        s = self.slotnow[i] = self.space
      if s != self.slotold[i]:
        x = (i * self.game.width)
        self.image.blit(s, [x, 0])
        self.slotold[i] = s

class JudgingDisp(Listener, pygame.sprite.Sprite):
  def __init__(self, playernum, game):
    pygame.sprite.Sprite.__init__(self)

    self._sticky = mainconfig['stickyjudge']
    self._needsupdate = True
    self._laststep = 0
    self._oldzoom = -1
    self._bottom = 320
    self._centerx = game.sprite_center + (playernum * game.player_offset)
        
    tx = FontTheme.Dance_step_judgment.size(_("MARVELOUS"))[0] + 4
    marvelous = fontfx.shadefade(_("MARVELOUS"), FontTheme.Dance_step_judgment, 4, [tx, 40], [224, 224, 224])

    tx = FontTheme.Dance_step_judgment.size(_("PERFECT"))[0] + 4
    perfect = fontfx.shadefade(_("PERFECT"), FontTheme.Dance_step_judgment, 4, [tx, 40], [224, 224, 32])

    tx = FontTheme.Dance_step_judgment.size(_("GREAT"))[0] + 4
    great = fontfx.shadefade(_("GREAT"), FontTheme.Dance_step_judgment, 4, [tx, 40], [32, 224, 32])

    tx = FontTheme.Dance_step_judgment.size(_("OKAY"))[0] + 4
    okay = fontfx.shadefade(_("OKAY"), FontTheme.Dance_step_judgment, 4, [tx, 40], [32, 32, 224])

    tx = FontTheme.Dance_step_judgment.size(_("BOO"))[0] + 4
    boo = fontfx.shadefade(_("BOO"), FontTheme.Dance_step_judgment, 4, [tx, 40], [96, 64, 32])

    tx = FontTheme.Dance_step_judgment.size(_("MISS"))[0]+4
    miss = fontfx.shadefade(_("MISS"), FontTheme.Dance_step_judgment, 4, [tx, 40], [224, 32, 32])

    self._space = FontTheme.Dance_step_judgment.render(" ", True, [0, 0, 0])

    marvelous.set_colorkey(marvelous.get_at([0, 0]), RLEACCEL)
    perfect.set_colorkey(perfect.get_at([0, 0]), RLEACCEL)
    great.set_colorkey(great.get_at([0, 0]), RLEACCEL)
    okay.set_colorkey(okay.get_at([0, 0]), RLEACCEL)
    boo.set_colorkey(boo.get_at([0, 0]), RLEACCEL)
    miss.set_colorkey(miss.get_at([0, 0]), RLEACCEL)

    self._images = { "V": marvelous, "P": perfect, "G": great,
                     "O": okay, "B": boo, "M": miss }
    
    self.image = self._space
    self._baseimage = self._space

  def stepped(self, pid, dir, curtime, etime, rating, combo):
    if rating is None: return

    self._laststep = curtime
    self._rating = rating
    self._baseimage = self._images.get(rating, self._space)

  def update(self, curtime):
    self._laststep = min(curtime, self._laststep)
    steptimediff = curtime - self._laststep

    zoomzoom = 1 - min(steptimediff, 0.2) * 2

    if zoomzoom != self._oldzoom:
      self._oldzoom = zoomzoom
      self._needsupdate = True
      if (steptimediff > 0.36) and not self._sticky:
        self.image = self._space

    if self._needsupdate:
      self.image = pygame.transform.rotozoom(self._baseimage, 0, zoomzoom)
      self.rect = self.image.get_rect()
      self.rect.centerx = self._centerx
      self.rect.bottom = self._bottom
      self.image.set_colorkey(self.image.get_at([0, 0]), RLEACCEL)
      self._needsupdate = False

class Player(object):

  def __init__(self, pid, config, songconf, game):
    self.theme = GFXTheme(mainconfig.get("%s-theme" % game.theme, "default"),
                          pid, game)
    self.pid = pid
    self.failed = False
    self.escaped = False

    self.__dict__.update(config)

    if self.speed < 0:
      self.target_bpm = -self.speed
    else:
      self.target_bpm = None

    self.game = game

    if self.scrollstyle == 2: self.top = 240 - game.width / 2
    elif self.scrollstyle == 1: self.top = 352
    else: self.top = 64

    self.secret_kind = songconf["secret"]

    self.score = scores.scores[songconf["scoring"]](pid, "NONE", game)
    self.combos = combos.combos[songconf["combo"]](pid, game)
    self.grade = grades.grades[songconf["grade"]]()
    Lifebar = lifebars.bars[songconf["lifebar"]]
    self.lifebar = Lifebar(pid, self.theme, songconf, game)
    self.judging_disp = JudgingDisp(self.pid, game)
    self.stats = stats.Stats()
    self.announcer = Announcer(mainconfig["djtheme"])

    self.listeners = [self.combos, self.score, self.grade, self.lifebar,
                      self.judging_disp, self.stats, self.announcer]

    if not game.double:
      self.judge = judge.judges[songconf["judge"]](self.pid, songconf)
      self.listeners.append(self.judge)
      arr, arrfx = self.theme.toparrows(self.top, self.pid)
      self.toparr = arr
      self.toparrfx = arrfx
      self.listeners.extend(arr.values() + arrfx.values())
      self.holdtext = HoldJudgeDisp(self.pid, self, self.game)
      self.listeners.append(self.holdtext)
    else:
      Judge = judge.judges[songconf["judge"]]
      self.judge = [Judge(self.pid * 2, songconf),
                    Judge(self.pid * 2 + 1, songconf)]
      self.listeners.extend(self.judge)
      arr1, arrfx1 = self.theme.toparrows(self.top, self.pid * 2)
      arr2, arrfx2 = self.theme.toparrows(self.top, self.pid * 2 + 1)
      self.arrows = [self.theme.arrows(self.pid * 2),
                     self.theme.arrows(self.pid * 2 + 1)]
      self.toparr = [arr1, arr2]
      self.toparrfx = [arrfx1, arrfx2]
      self.listeners.extend(arr1.values() + arr2.values() +
                            arrfx1.values() + arrfx2.values())
      self.holdtext = [HoldJudgeDisp(self.pid * 2, self, self.game),
                       HoldJudgeDisp(self.pid * 2 + 1, self, self.game)]
      self.listeners.extend(self.holdtext)

  def set_song(self, song, diff, lyrics):
    self.difficulty = diff

    if self.game.double:
      self.holding = [[-1] * len(self.game.dirs), [-1] * len(self.game.dirs)]
      if self.transform == 1:
        # In double mirror mode, we have to swap the step sets for this
        # player's pids. This ensures, e.g., 1R becomes 2L, rather than 1L.
        self.steps = [steps.Steps(song, diff, self, self.pid * 2 + 1,
                                  lyrics, self.game.name),
                      steps.Steps(song, diff, self, self.pid * 2,
                                  lyrics, self.game.name)]
      else:
        self.steps = [steps.Steps(song, diff, self, self.pid * 2,
                                  lyrics, self.game.name),
                      steps.Steps(song, diff, self, self.pid * 2 + 1,
                                  lyrics, self.game.name)]
      self.length = max(self.steps[0].length, self.steps[1].length)
      self.ready = min(self.steps[0].ready, self.steps[1].ready)
      self.bpm = self.steps[0].bpm

      count = self.steps[0].totalarrows + self.steps[1].totalarrows

      total_holds = 0
      for i in range(2):  total_holds += len(self.steps[i].holdref)

      args = (self.pid, self.bpm, diff, count, total_holds,
              self.steps[0].feet)
      for l in self.listeners: l.set_song(*args)

    else:
      self.holding = [-1] * len(self.game.dirs)
      self.steps = steps.Steps(song, diff, self, self.pid, lyrics,
                               self.game.name)
      self.length = self.steps.length
      self.ready = self.steps.ready
      self.bpm = self.steps.bpm
      self.arrows = self.theme.arrows(self.pid)

      holds = len(self.steps.holdref)

      args = (self.pid, self.bpm, diff, self.steps.totalarrows,
              holds, self.steps.feet)
      for l in self.listeners: l.set_song(*args)

  def start_song(self):
    self.toparr_group = RenderUpdates()
    self.fx_group = RenderUpdates()
    self.text_group = RenderUpdates()
    self.text_group.add([self.score, self.lifebar, self.judging_disp])
    self.text_group.add(self.holdtext)

    if mainconfig["showcombo"]: self.text_group.add(self.combos)

    if self.game.double:
      self.arrow_group = [OrderedRenderUpdates(),
                          OrderedRenderUpdates()]

      for i in range(2):
        self.steps[i].play()
        for d in self.game.dirs:
          if mainconfig["explodestyle"] > -1:
            self.toparrfx[i][d].add(self.fx_group)
          if not self.dark: self.toparr[i][d].add(self.toparr_group)
      self.sprite_groups = [self.toparr_group, self.arrow_group[0],
                            self.arrow_group[1], self.fx_group,
                            self.text_group]
    else:
      self.steps.play()
      self.arrow_group = OrderedRenderUpdates()
      for d in self.game.dirs:
        if mainconfig["explodestyle"] > -1: self.toparrfx[d].add(self.fx_group)
        if not self.dark: self.toparr[d].add(self.toparr_group)
      self.sprite_groups = [self.toparr_group, self.arrow_group,
                            self.fx_group, self.text_group]

  def get_next_events(self, song):
    if self.game.double:
      self.fx_data = [[], []]
      for i in range(2):
        self._get_next_events(song, self.arrow_group[i], self.arrows[i],
                              self.steps[i], self.judge[i])
    else:
      self.fx_data = []
      self._get_next_events(song, self.arrow_group, self.arrows, self.steps,
                            self.judge)

  def _get_next_events(self, song, arrow_grp, arrow_gfx, steps, judge):
    evt = steps.get_events()
    if evt is not None:
      events, nevents, time, bpm = evt
      for ev in events:
        if ev.feet:
          for (dir, num) in zip(self.game.dirs, ev.feet):
            if num & 1: judge.handle_arrow(dir, ev.when, num & 4)

      if self.fade == 5: return # Stealth mode

      newsprites = []
      for ev in nevents:
        if ev.feet:
          for (dir, num) in zip(self.game.dirs, ev.feet):
            # Don't make hidden arrow sprites if we have hidden arrows
            # off entirely, or have them set not to display.
            if not num & 4 or self.secret_kind == 2:
              dirstr = dir + repr(int(ev.color) % self.colortype)
              if num & 1 and not num & 2:
                ns = arrows.ArrowSprite(arrow_gfx[dirstr], ev.beat, num & 4,
                                        ev.when, self, song)
                newsprites.append(ns)
              elif num & 2:
                holdindex = steps.holdref.index((self.game.dirs.index(dir),
                                                 ev.when))
                ns = arrows.HoldArrowSprite(arrow_gfx[dirstr],
                                            steps.holdbeats[holdindex],
                                            num & 4,
                                            steps.holdinfo[holdindex],
                                            self, song)
                newsprites.append(ns)

      arrow_grp.add(newsprites)

  def check_sprites(self, curtime, curbeat, arrows, steps, fx_data, judge):
    misses = judge.expire_arrows(curtime)
    for d in misses:
      for l in self.listeners:
        l.stepped(self.pid, d, curtime, -1, "M", self.combos.combo)
    for rating, dir, time in fx_data:
      if (rating == "V" or rating == "P" or rating == "G"):
        for spr in arrows.sprites():
          if spr.endtime == time and spr.dir == dir:
            if not spr.hold: spr.kill()

    arrows.update(curtime, self.bpm, curbeat, judge)
    self.toparr_group.update(curtime, curbeat)

  def should_hold(self, steps, direction, curtime):
    for i,l in enumerate(steps.holdinfo):
      if l[0] == self.game.dirs.index(direction):
        if ((curtime - 15.0/steps.playingbpm > l[1])
            and (curtime < l[2])):
          return i

  def check_holds(self, pid, curtime, arrows, steps, judge, toparrfx, holding):
    # FIXME THis needs to go away
    keymap_kludge = { "u": pad.UP, "k": pad.UPLEFT, "z": pad.UPRIGHT,
                      "d": pad.DOWN, "l": pad.LEFT, "r": pad.RIGHT,
                      "g": pad.DOWNRIGHT, "w": pad.DOWNLEFT, "c": pad.CENTER }

    for dir in self.game.dirs:
      toparrfx[dir].holding(0)
      current_hold = self.should_hold(steps, dir, curtime)
      dir_idx = self.game.dirs.index(dir)
      if current_hold is not None:
        if pad.states[(pid, keymap_kludge[dir])]:
          if judge.holdsub.get(holding[dir_idx]) != -1:
            toparrfx[dir].holding(1)
          holding[dir_idx] = current_hold
          botchdir, timef1, timef2 = steps.holdinfo[current_hold]
          for spr in arrows.sprites():
            if (spr.endtime == timef1 and spr.dir == dir):
              spr.held()
              break
        else:
          if judge.holdsub.get(current_hold) != -1:
            botchdir, timef1, timef2 = steps.holdinfo[current_hold]
            for spr in arrows.sprites():
              if (spr.endtime == timef1 and spr.dir == dir):
                if spr.broken_at(curtime, judge):
                  args = (pid, curtime, dir, current_hold)
                  for l in self.listeners: l.broke_hold(*args)
                break
      else:
        if holding[dir_idx] > -1:
          if judge.holdsub.get(holding[dir_idx]) != -1:
            args = (pid, curtime, dir, holding[dir_idx])
            for l in self.listeners: l.ok_hold(*args)
            holding[dir_idx] = -1

  def handle_key(self, ev, time):
    ev = ev[0], self.game.dirmap.get(ev[1], ev[1])
    if ev[1] not in self.game.dirs: return

    if self.game.double:
      pid = ev[0] & 1
      rating, dir, etime = self.judge[pid].handle_key(ev[1], time)
      for l in self.listeners:
        l.stepped(ev[0], dir, time, etime, rating, self.combos.combo)
      self.fx_data[pid].append((rating, dir, etime))
    else:
      rating, dir, etime = self.judge.handle_key(ev[1], time)
      for l in self.listeners:
        l.stepped(ev[0], dir, time, etime, rating, self.combos.combo)
      self.fx_data.append((rating, dir, etime))

  def check_bpm_change(self, pid, time, steps, judge):
    newbpm = self.bpm
    for bpm in steps.lastbpmchangetime:
      if time >= bpm[0]: newbpm = bpm[1]

    if newbpm != self.bpm:
      self.bpm = newbpm
      for l in self.listeners: l.change_bpm(pid, time, newbpm)
        
  def clear_sprites(self, screen, bg):
    for g in self.sprite_groups: g.clear(screen, bg)

  def game_loop(self, time, screen):    
    if self.game.double:
      for i in range(2):
        if len(self.steps[i].lastbpmchangetime) == 0:
          cur_beat = (time - self.steps[i].offset) / (60.0 / self.bpm)
        else:
          cur_beat = 0
          oldbpmsub = [self.steps[i].offset, self.steps[i].bpm]
          for bpmsub in self.steps[i].lastbpmchangetime:
            if bpmsub[0] <= time:
              cur_beat += (bpmsub[0] - oldbpmsub[0]) / (60.0 / oldbpmsub[1])
              oldbpmsub = bpmsub
            else: break
          cur_beat += (time - oldbpmsub[0]) / (60.0 / oldbpmsub[1])
            
        self.check_holds(self.pid * 2 + i, time, self.arrow_group[i],
                         self.steps[i], self.judge[i], self.toparrfx[i],
                         self.holding[i])
        self.check_bpm_change(self.pid * 2 + i, time, self.steps[i],
                              self.judge[i])
        self.check_sprites(time, cur_beat, self.arrow_group[i],
                           self.steps[i], self.fx_data[i], self.judge[i])

    else:
      if len(self.steps.lastbpmchangetime) == 0:
        cur_beat = (time - self.steps.offset) / (60.0 / self.bpm)
      else:
        cur_beat = 0
        oldbpmsub = [self.steps.offset, self.steps.bpm]
        for bpmsub in self.steps.lastbpmchangetime:
          if bpmsub[0] <= time:
            cur_beat += (bpmsub[0] - oldbpmsub[0]) / (60.0 / oldbpmsub[1])
            oldbpmsub = bpmsub
          else: break
        cur_beat += (time - oldbpmsub[0]) / (60.0 / oldbpmsub[1])

      self.check_holds(self.pid, time, self.arrow_group, self.steps,
                       self.judge, self.toparrfx, self.holding)
      self.check_bpm_change(self.pid, time, self.steps, self.judge)
      self.check_sprites(time, cur_beat, self.arrow_group, self.steps,
                         self.fx_data, self.judge)


    self.fx_group.update(time)
    self.text_group.update(time)
    if self.lifebar.gameover == lifebars.FAILED and not self.failed:
      self.failed = True

    rects = []
    for g in self.sprite_groups: rects.extend(g.draw(screen))
    return rects
