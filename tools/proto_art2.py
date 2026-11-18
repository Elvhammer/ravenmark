"""Increment 1 art: new map objects, interiors, the cave, NPCs, companions, the great erne, item icons,
the pixel font, dialog UI and the in-game world map. Called from proto_build.py (same style + palette).

  register()          adds the new season-dependent map objects to proto_build.KINDS (before build_objects)
  build_all(manifest) renders everything else and adds it to the sprite manifest
"""
import json
import os
import numpy as np
from PIL import Image

import proto_build as PB
import proto_rooms as ROOMS
import mount_ideas as MI

G = PB.G
ART = PB.ART
C = PB.C
SEASONS = PB.SEASONS


def setp(x, y, c):
    G['setp'](x, y, c)


def P(key):
    return G['P'][key]


def ellipse_pts(cx, cy, rx, ry):
    return [(x, y) for y in range(int(cy - ry) - 1, int(cy + ry) + 2) for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1]


def lit_key(nx, ny, keys, x=0, y=0, dither=0.25):
    """pick a shade from keys (light..dark) for a surface normal-ish position, light from the top-left"""
    v = -(0.6 * nx + 0.8 * ny) * 0.5 + 0.5 + (G['BAYER'][y % 4, x % 4] - 0.5) * dither
    return keys[int(np.clip((1 - v) * len(keys), 0, len(keys) - 1))]


def fill_ell(cx, cy, rx, ry, keys, outline=True):
    pts = set(ellipse_pts(cx, cy, rx, ry))
    for (x, y) in pts:
        setp(x, y, lit_key((x - cx) / rx, (y - cy) / ry, keys, x, y))
    if outline:
        for (x, y) in pts:
            if any((x + dx, y + dy) not in pts for dx, dy in ((1, 0), (0, 1))):
                setp(x, y, 'ink')
    return pts


def add(ay, fn, shadow=None):
    if shadow:
        G['shadows'].append(shadow)
    G['objects'].append((ay, fn))


# ====================================================================== overworld objects (4 seasons)
def draw_standing_stone(ax, ay):
    def draw():
        top = ay - 21
        for y in range(top, ay + 1):
            k = y - top
            half = 4 if k > 3 else [1, 2, 3, 4][k]
            if k > 12:
                half = 5
            for x in range(ax - half, ax + half + 1):
                c = 'stone_lt' if x < ax - 1 else ('stone' if x < ax + 3 else 'stone_dk')
                if x in (ax - half, ax + half) or k == 0 or y == ay:
                    c = 'ink'
                elif k < 9 and x < ax + 1 and (x * 3 + y) % 5 < 2:
                    c = 'leaf'                                          # moss on the weathered top
                setp(x, y, c)
        for (x, y) in ((ax, top + 9), (ax, top + 10), (ax, top + 11), (ax - 1, top + 10), (ax + 1, top + 12),
                       (ax - 1, top + 14), (ax, top + 15), (ax + 1, top + 14)):
            setp(x, y, 'stone_dk')                                      # carved rune
    add(ay, draw, (ax + 4, ay, 7, 2))


def draw_puffin(ax, ay):
    k, w, o, O = C('#1E1B2C'), 'cream', C('#E0A256'), C('#B8483A')
    rows = ['..kk...', '.kkkk..', '.kwwkoO', '.kwwk..', 'kkwwwk.', 'kkwwwk.', '.kwwwk.', '..ww...', '..o.o..']
    pal = {'k': k, 'w': w, 'o': o, 'O': O}

    def draw():
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch != '.':
                    setp(ax - 3 + dx, ay - 8 + dy, pal[ch])
    add(ay, draw, (ax + 2, ay, 3, 1))


def draw_cave_mouth(ax, ay, dx=0):
    """a dark opening in a rock face; dx shifts it (the Sule Ness mouth sits one tile right of its anchor)"""
    cx = ax + dx

    def draw():
        rim = set()
        for (x, y) in ellipse_pts(cx, ay - 9, 15, 13):                 # rock mass around the opening
            if y <= ay:
                rim.add((x, y))
        for (x, y) in rim:
            nx, ny = (x - cx) / 15, (y - ay + 9) / 13
            c = lit_key(nx, ny, ['stone_lt', 'stone', 'stone', 'stone_dk'], x, y)
            if (x * 7 + y * 3) % 23 == 0:
                c = 'stone_dk'
            setp(x, y, c)
        hole = set()
        for (x, y) in ellipse_pts(cx, ay - 4, 8, 10):                  # the arch
            if y <= ay:
                hole.add((x, y))
        for (x, y) in hole:
            d = ((x - cx) / 8) ** 2 + ((y - ay + 4) / 10) ** 2
            setp(x, y, C('#1E1B2C') if d < 0.55 or y > ay - 3 else 'slate_dk')
        for (x, y) in rim:
            if (x, y) not in hole and any((x + a, y + b) not in rim for a, b in ((1, 0), (-1, 0), (0, -1))):
                setp(x, y, 'ink')
        for x in range(cx - 14, cx + 15):
            if (x, ay) in rim and (x, ay) not in hole:
                setp(x, ay, 'ink')
        for (x, y) in ((cx - 10, ay - 1), (cx - 11, ay - 2), (cx + 10, ay - 1), (cx + 11, ay - 2), (cx - 12, ay - 1)):
            setp(x, y, 'stone_dk')
    add(ay, draw, (cx + 4, ay, 15, 3))


def draw_ruin(ax, ay):
    """the old watch: a broken round stone tower on the plateau (2 x 2 tiles, anchor = bottom-left tile)"""
    cx = ax + 8

    def draw():
        x0, x1 = cx - 15, cx + 15
        tops = [ay - 30 + int(4 * abs(np.sin(x * 0.7)) + (8 if x > cx + 4 else 0) + (5 if x < cx - 9 else 0))
                for x in range(x0, x1 + 1)]
        for i, x in enumerate(range(x0, x1 + 1)):
            t = (x - cx) / 15
            for y in range(tops[i], ay + 1):
                row = (y - ay) // 4
                joint = (y - ay) % 4 == 0 or (x + (3 if row % 2 else 0)) % 7 == 0
                c = 'stone_lt' if t < -0.35 else ('stone' if t < 0.45 else 'stone_dk')
                if joint:
                    c = 'stone_dk' if c != 'stone_dk' else 'slate_dk'
                if y == tops[i] or x in (x0, x1) or y == ay:
                    c = 'ink'
                elif y == tops[i] + 1 and (x * 5) % 3:
                    c = 'leaf'
                setp(x, y, c)
        for y in range(ay - 13, ay + 1):                               # empty doorway
            for x in range(cx - 3, cx + 4):
                d = ((x - cx) / 4) ** 2 + ((y - ay + 8) / 6) ** 2
                if y > ay - 8 or d <= 1:
                    setp(x, y, C('#1E1B2C'))
        for (rx, ry, w) in ((cx + 19, ay - 1, 5), (cx - 19, ay, 4), (cx + 14, ay + 1, 3)):     # rubble
            for (x, y) in ellipse_pts(rx, ry - 2, w / 2, 2):
                setp(x, y, lit_key((x - rx) / w, (y - ry) / 3, ['stone_lt', 'stone', 'stone_dk'], x, y))
    add(ay, draw, (cx + 5, ay, 18, 4))


FOX_PAL = {'o': '#E0A256', 'O': '#A8693F', 'd': '#6E4A35', 'w': '#F2E3B3', 'k': '#1E1B2C', 'n': '#3D3550'}
OWL_PAL = {'b': '#A8693F', 'B': '#6E4A35', 'w': '#F2E3B3', 'y': '#E0A256', 'k': '#1E1B2C', 'g': '#8A8496'}


def draw_pen(ax, ay, fox=True, owl=True):
    """Hedda's animal pen: a low fence (3 x 2 tiles), a straw hutch, a perch post; fox kit and owlet inside"""
    def draw():
        x0, x1, yb, yt = ax - 23, ax + 23, ay, ay - 22
        for y in range(yt + 4, yb):                                    # straw floor
            for x in range(x0 + 1, x1):
                if (x * 3 + y * 7) % 11 == 0:
                    setp(x, y, 'path_lt')
        for y in range(yt - 6, yt + 8):                                # hutch
            for x in range(x0 + 2, x0 + 16):
                c = 'wood' if x < x0 + 12 else 'wood_dk'
                if y < yt:
                    c = 'thatch_lt' if x < x0 + 9 else 'thatch'
                if x in (x0 + 2, x0 + 15) or y == yt - 6 or y == yt + 7:
                    c = 'ink'
                setp(x, y, c)
        for y in range(yt + 2, yt + 7):
            for x in range(x0 + 6, x0 + 11):
                setp(x, y, C('#1E1B2C'))
        for y in range(yt - 4, yb - 6):                                # perch post
            setp(x1 - 9, y, 'trunk'); setp(x1 - 8, y, 'trunk_dk')
        for x in range(x1 - 13, x1 - 4):
            setp(x, yt - 4, 'trunk_lt')
        if owl:
            put_rows(x1 - 13, yt - 15, OWL_ROWS_SIT, OWL_PAL)
        if fox:
            put_rows(ax - 4, yb - 14, FOX_ROWS_SIT, FOX_PAL)
        for (y, sag) in ((yt + 2, 0), (yt + 6, 0)):                    # back fence rails
            for x in range(x0, x1 + 1):
                setp(x, y, 'wood_lt'); setp(x, y + 1, 'wood_dk')
        for x in range(x0, x1 + 1):                                     # front fence (in front of the animals)
            for y in (yb - 7, yb - 3):
                setp(x, y, 'wood_lt'); setp(x, y + 1, 'wood_dk')
        for px in list(range(x0, x1 + 1, 9)) + [x1 - 1]:
            for y in range(yt, yb + 1):
                setp(px, y, 'wood_lt'); setp(px + 1, y, 'wood_dk')
    add(ay, draw, (ax + 4, ay, 26, 3))


def put_rows(x0, y0, rows, pal):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.':
                setp(x0 + dx, y0 + dy, C(pal[ch]) if pal[ch].startswith('#') else pal[ch])


FOX_ROWS_SIT = ['.k.....k.', '.ok...ko.', '.oookooo.', 'oowoooowo', 'ookwoowko', '.oowwwoo.', '..wwkww..',
                '.oowwwoo.', 'ooowwwooo', 'ooowwwoooO', 'oo.www.oOO', '.dd...ddwO', '........ww']
OWL_ROWS_SIT = ['.B.....B.', '.BbbbbbB.', 'BbwwbwwbB', 'bwykbkywb', 'bwwwywwwb', 'Bbbwywbb.', 'BbBwwwBbB',
                'BbwBwBwbB', 'Bbwwwwwb.', '.BbwBwbB.', '..y...y..']


def draw_linden(ax, ay):
    G['tree'](ax, ay, 1.55)


def draw_beacon(ax, ay):
    """Fyrholm's old beacon: a squat stone tower with an iron fire basket"""
    def draw():
        for y in range(ay - 26, ay + 1):
            k = (y - ay + 26) / 26
            half = int(round(5 + 3 * k))
            for x in range(ax - half, ax + half + 1):
                c = 'stone_lt' if x < ax - 2 else ('stone' if x < ax + 3 else 'stone_dk')
                if (y - ay) % 5 == 0 or (x + (2 if ((y - ay) // 5) % 2 else 0)) % 5 == 0:
                    c = 'stone_dk' if c != 'stone_dk' else 'slate_dk'
                if x in (ax - half, ax + half) or y == ay:
                    c = 'ink'
                setp(x, y, c)
        for x in range(ax - 7, ax + 8):
            setp(x, ay - 27, 'ink'); setp(x, ay - 28, 'iron')
        for y in range(ay - 36, ay - 28):                               # fire basket
            for x in range(ax - 6, ax + 7):
                if (x - ax) % 3 == 0 or y == ay - 29:
                    setp(x, y, 'iron')
        for (x, y) in ellipse_pts(ax, ay - 34, 4.5, 5):
            if y < ay - 29:
                setp(x, y, 'glow' if abs(x - ax) < 2 and y > ay - 37 else 'glass')
        for (x, y) in ((ax - 1, ay - 40), (ax + 1, ay - 41), (ax, ay - 39), (ax + 2, ay - 38)):
            setp(x, y, 'glass')
    add(ay, draw, (ax + 6, ay, 10, 3))


def draw_sapling(ax, ay):
    """a young birch sprouting right in the path: slim white trunk, a small airy crown"""
    def draw():
        for y in range(ay - 22, ay + 1):
            setp(ax - 1, y, 'cream')
            setp(ax, y, C('#3D3550') if (y * 5) % 7 == 0 else 'sand_dk')
        for (x0, y0, x1, y1) in ((ax - 1, ay - 14, ax - 5, ay - 18), (ax, ay - 17, ax + 4, ay - 21)):
            n = max(abs(x1 - x0), abs(y1 - y0))
            for t in range(n + 1):
                setp(x0 + (x1 - x0) * t // n, y0 + (y1 - y0) * t // n, 'trunk_dk')
        crown = {}
        for (ox, oy, r) in [(0, -27, 5.5), (-5, -21, 4), (5, -23, 4), (-1, -32, 3.5)]:
            for (x, y) in ellipse_pts(ax + ox, ay + oy, r, r):
                crown[(x, y)] = True
        for (x, y) in crown:
            if (x * 7 + y * 3) % 9 == 0:
                continue                                                 # airy gaps in the young crown
            setp(x, y, lit_key((x - ax) / 6, (y - ay + 26) / 7, ['leaf_hi', 'leaf_lt', 'leaf', 'leaf_dk'], x, y, 0.4))
        for (x, y) in crown:
            if ((x + 1, y) not in crown or (x, y + 1) not in crown) and (x * 7 + y * 3) % 9:
                setp(x, y, 'leaf_ol')
    add(ay, draw, (ax + 4, ay, 6, 2))


def draw_cracked_rock(ax, ay):
    def draw():
        pts = set(ellipse_pts(ax, ay - 7, 9, 7.5))
        pts = {(x, y) for (x, y) in pts if y <= ay}
        for (x, y) in pts:
            setp(x, y, lit_key((x - ax) / 9, (y - ay + 7) / 7.5, ['stone_lt', 'stone', 'stone', 'stone_dk'], x, y))
        crack = [(ax - 1, ay - 14), (ax, ay - 12), (ax - 1, ay - 10), (ax + 1, ay - 9), (ax + 2, ay - 7), (ax + 1, ay - 5),
                 (ax + 3, ay - 3), (ax + 3, ay - 1), (ax - 2, ay - 8), (ax - 4, ay - 7), (ax - 5, ay - 5), (ax + 4, ay - 8),
                 (ax + 6, ay - 9)]
        for (x, y) in crack:
            setp(x, y, C('#1E1B2C')); setp(x, y + 1, C('#1E1B2C'))
            if (x + 1, y) in pts:
                setp(x + 1, y, 'stone_lt')
        for (x, y) in pts:
            if any((x + dx, y + dy) not in pts for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                setp(x, y, 'ink')
    add(ay, draw, (ax + 4, ay, 10, 2.5))


def draw_hedge(ax, ay, gap=False):
    """a thick hedge filling one tile; with gap=True the owl has shown the hidden way through"""
    def draw():
        pts = {}
        for (ox, oy, r) in [(-5, -6, 6), (4, -6, 6), (0, -12, 6), (-6, -14, 4.5), (6, -14, 4.5), (0, -3, 7)]:
            for (x, y) in ellipse_pts(ax + ox, ay + oy, r, r):
                if y <= ay:
                    pts[(x, y)] = True
        for (x, y) in pts:
            v = (x - ax) / 9, (y - ay + 10) / 10
            setp(x, y, lit_key(v[0], v[1], ['leaf_hi', 'leaf_lt', 'leaf', 'leaf_dk'], x, y, 0.45))
        for (x, y) in pts:
            if (x + 1, y) not in pts or (x, y + 1) not in pts:
                setp(x, y, 'leaf_ol')
        if gap:
            for y in range(ay - 11, ay + 1):
                for x in range(ax - 3, ax + 4):
                    d = (x - ax) ** 2 / 12 + (y - ay + 5) ** 2 / 40
                    if y > ay - 5 or d <= 1:
                        setp(x, y, 'leaf_dk' if abs(x - ax) == 3 else C('#2F4A35') if y < ay - 2 else 'floor_dk')
    add(ay, draw, (ax + 3, ay, 10, 3))


def draw_thicket(ax, ay):
    """a wall of thorny brambles"""
    rng = np.random.default_rng(ax * 7 + ay)

    def draw():
        mass = {}
        for (ox, oy, r) in [(-5, -6, 5.5), (4, -6, 5.5), (0, -11, 5), (-6, -12, 4), (6, -12, 4), (0, -3, 6.5)]:
            for (x, y) in ellipse_pts(ax + ox, ay + oy, r, r):
                if y <= ay:
                    mass[(x, y)] = True
        for (x, y) in mass:
            c = 'leaf_dk' if (x * 3 + y * 5) % 7 else 'roof_dk'
            if (x + y) % 5 == 0:
                c = 'trunk_dk'
            setp(x, y, c)
        for (x, y) in mass:
            if (x + 1, y) not in mass or (x, y + 1) not in mass or (x - 1, y) not in mass or (x, y - 1) not in mass:
                setp(x, y, 'ink')
        stems = []
        for i in range(9):
            x = ax - 9 + i * 2.2 + rng.uniform(-1, 1)
            h = rng.uniform(15, 22)
            bend = rng.uniform(-6, 6)
            stems.append([(x + bend * (t / h) ** 2, ay - t) for t in np.arange(0, h, 0.5)])
        for s in stems:
            for (x, y) in s:
                setp(int(round(x)), int(round(y)), 'trunk')
        for s in stems:
            for j, (x, y) in enumerate(s[::5]):
                setp(int(round(x)) + (1 if j % 2 else -1), int(round(y)), 'cream')
                if rng.random() < 0.55:
                    lx, ly = int(round(x)) + (1 if j % 2 else -1), int(round(y))
                    setp(lx, ly, 'leaf_dk'); setp(lx + (1 if j % 2 else -1), ly - 1, 'leaf')
        for _ in range(8):
            s = stems[int(rng.integers(0, len(stems)))]
            x, y = s[int(rng.integers(len(s) // 3, len(s)))]
            setp(int(round(x)), int(round(y)), 'band')
        for s in stems:                                                  # thorn outline
            x, y = s[-1]
            setp(int(round(x)), int(round(y)) - 1, 'ink')
    add(ay, draw, (ax + 3, ay, 10, 2.5))


def draw_perch(ax, ay):
    """a tall dead pine with a crossbar, streaked white: the great erne's roost"""
    def draw():
        for y in range(ay - 46, ay + 1):
            w = 2 if y > ay - 30 else 1
            for x in range(ax - w, ax + w + 1):
                c = 'trunk_lt' if x < ax else ('trunk' if x == ax else 'trunk_dk')
                if (y * 3 + x) % 9 == 0 or (y % 7 == 0 and x == ax):
                    c = 'cream'
                setp(x, y, c)
        for x in range(ax - 9, ax + 10):
            setp(x, ay - 40, 'trunk_lt'); setp(x, ay - 39, 'trunk_dk')
        for (x0, y0, x1, y1) in ((ax - 2, ay - 24, ax - 8, ay - 31), (ax + 2, ay - 18, ax + 7, ay - 23)):
            n = max(abs(x1 - x0), abs(y1 - y0))
            for t in range(n + 1):
                setp(x0 + (x1 - x0) * t // n, y0 + (y1 - y0) * t // n, 'trunk_dk')
        for (x, y) in ellipse_pts(ax, ay - 43, 6, 2.5):                 # nest
            setp(x, y, 'thatch' if (x + y) % 3 else 'thatch_dk')
        for (x, y) in ((ax - 5, ay), (ax - 4, ay - 1), (ax + 4, ay), (ax + 5, ay - 1)):
            setp(x, y, 'trunk_dk')
    add(ay, draw, (ax + 6, ay, 7, 2))


def draw_stall(ax, ay, cloth, cloth_dk, goods):
    """night-market stall (3 tiles wide) with a striped awning and two lanterns"""
    def draw():
        x0, x1 = ax - 23, ax + 23
        for px in (x0 + 1, x1 - 2):                                     # posts
            for y in range(ay - 50, ay - 10):
                setp(px, y, 'trunk'); setp(px + 1, y, 'trunk_dk')
        for y in range(ay - 54, ay - 45):                               # awning
            for x in range(x0 - 2, x1 + 3):
                c = cloth if ((x - x0) // 4) % 2 == 0 else 'cream'
                if y >= ay - 47:
                    c = cloth_dk if ((x - x0) // 4) % 2 == 0 else 'sand_dk'
                if y == ay - 54:
                    c = 'ink'
                setp(x, y, c)
            if y >= ay - 47:
                for x in range(x0 - 2, x1 + 3, 4):
                    setp(x, ay - 45, cloth_dk)
        for lx in (x0 + 6, x1 - 6):                                     # lanterns
            setp(lx, ay - 44, 'iron'); setp(lx, ay - 43, 'iron')
            for y in range(ay - 42, ay - 37):
                for x in range(lx - 2, lx + 3):
                    setp(x, y, 'ink' if x in (lx - 2, lx + 2) or y in (ay - 42, ay - 38) else 'glow')
        for y in range(ay - 14, ay + 1):                                # counter
            for x in range(x0, x1 + 1):
                if y < ay - 10:
                    c = 'wood_lt' if y == ay - 14 else 'wood'
                else:
                    c = cloth if ((x - x0) // 4) % 2 == 0 else 'cream'
                    if y == ay:
                        c = 'ink'
                if x in (x0, x1):
                    c = 'ink'
                setp(x, y, c)
        goods(x0, x1, ay - 14)
    add(ay, draw, (ax + 4, ay, 26, 3))


def goods_feathers(x0, x1, y):
    cols = ['band', 'feather', 'river', 'gold', 'cream', 'leaf_lt']
    for i, x in enumerate(range(x0 + 4, x1 - 3, 4)):
        c = cols[i % len(cols)]
        for k in range(5):
            setp(x + (k // 3), y - 1 - k, c)
    for x in (x0 + 18, x0 + 28):                                         # bells
        for (bx, by) in ellipse_pts(x, y - 3, 2.5, 3):
            if by < y:
                setp(bx, by, 'gold' if bx < x else 'wood_lt')


def goods_charts(x0, x1, y):
    for i, x in enumerate(range(x0 + 3, x1 - 6, 9)):
        for yy in range(y - 4, y):
            for xx in range(x, x + 7):
                setp(xx, yy, 'cream' if (xx + yy) % 5 else 'river')
        setp(x, y - 4, 'sand_dk'); setp(x + 6, y - 1, 'sand_dk')
    for k in range(4):
        setp(x1 - 4, y - 1 - k, 'gold')


CABIN = {'wall': '#6E4A35', 'wall_sh': '#5A3D2E', 'wall_dk': '#3D3550'}
CABIN_ROOF = {s: {'roof_lt': PB.LEAF[s][2], 'roof': PB.LEAF[s][1], 'roof_dk': PB.LEAF[s][0], 'roof_ln': PB.LEAF[s][0]}
              for s in SEASONS}

NEW_KINDS = {
    'standing_stone': (draw_standing_stone, (24, 32), (12, 28), {'snow': 1}),
    'puffin': (draw_puffin, (16, 16), (8, 12), {}),
    'cave_mouth': (lambda x, y: draw_cave_mouth(x, y + 4, 16), (64, 40), (16, 30), {'snow': 2}),
    'cave_mouth_n': (lambda x, y: draw_cave_mouth(x, y + 4), (48, 40), (24, 30), {'snow': 2}),
    'ruin': (draw_ruin, (64, 48), (16, 42), {'snow': 2}),
    'pen': (draw_pen, (64, 48), (32, 42), {'snow': 1}),
    'pen_onlyfox': (lambda x, y: draw_pen(x, y, owl=False), (64, 48), (32, 42), {'snow': 1}),
    'pen_onlyowl': (lambda x, y: draw_pen(x, y, fox=False), (64, 48), (32, 42), {'snow': 1}),
    'cabin': (lambda x, y: G['house_v2'](x, y - 52), (96, 80), (8, 72), {'extra': CABIN, 'extra_season': CABIN_ROOF,
                                                                         'snow': 1}),
    'linden': (draw_linden, (112, 112), (56, 104), {'snow': 4}),
    'beacon': (draw_beacon, (32, 56), (16, 50), {'snow': 1}),
    'sapling': (draw_sapling, (48, 48), (24, 42), {'snow': 3}),
    'cracked_rock': (draw_cracked_rock, (32, 28), (16, 24), {'snow': 2}),
    'hedge': (draw_hedge, (32, 32), (16, 28), {'snow': 2}),
    'hedge_open': (lambda x, y: draw_hedge(x, y, True), (32, 32), (16, 28), {'snow': 2}),
    'thicket': (draw_thicket, (32, 32), (16, 28), {'snow': 1}),
    'perch': (draw_perch, (32, 56), (16, 50), {'snow': 1}),
    'stall_a': (lambda x, y: draw_stall(x, y, 'band', 'roof_dk', goods_feathers), (64, 64), (32, 58), {'snow': 1}),
    'stall_b': (lambda x, y: draw_stall(x, y, 'river', 'river_dp', goods_charts), (64, 64), (32, 58), {'snow': 1}),
}
NEW_EMISSIVE = {'cabin': ('glass', 'glass_lt', 'glow'), 'beacon': ('glow', 'glass'), 'stall_a': ('glow',),
                'stall_b': ('glow',)}


def register():
    PB.KINDS.update(NEW_KINDS)
    PB.EMISSIVE.update(NEW_EMISSIVE)


# ====================================================================== interiors (summer palette, no seasons)
def draw_counter(ax, ay, n=4):
    def draw():
        x0, x1 = ax - 8, ax - 8 + 16 * n - 1
        for y in range(ay - 17, ay + 1):
            for x in range(x0, x1 + 1):
                if y < ay - 11:
                    c = 'wood_lt' if y < ay - 15 else 'plank_lt'
                else:
                    c = 'wood' if (x - x0) % 8 else 'wood_dk'
                    if y > ay - 3:
                        c = 'wood_dk'
                if x in (x0, x1) or y in (ay - 17, ay):
                    c = 'ink'
                setp(x, y, c)
        for (mx, kind) in ((x0 + 9, 'mug'), (x0 + 16, 'mug'), (x0 + 40, 'bell'), (x0 + 50, 'jar')):
            if mx > x1 - 4:
                continue
            if kind == 'mug':
                for y in range(ay - 20, ay - 14):
                    for x in range(mx, mx + 4):
                        setp(x, y, 'ink' if x == mx + 3 or y == ay - 15 else 'tin_lt' if x == mx else 'tin')
                setp(mx + 4, ay - 18, 'tin_dk')
            elif kind == 'bell':
                for (x, y) in ellipse_pts(mx, ay - 17, 2.5, 2.5):
                    if y <= ay - 16:
                        setp(x, y, 'gold')
                setp(mx, ay - 20, 'iron')
            else:
                for y in range(ay - 22, ay - 14):
                    for x in range(mx, mx + 5):
                        setp(x, y, 'ink' if x in (mx, mx + 4) else ('glass' if y > ay - 19 else 'glass_lt'))
    add(ay, draw)


def draw_shelf(ax, ay, n=3):
    def draw():
        x0, x1 = ax - 8, ax - 8 + 16 * n - 1
        top = ay - 26
        for y in range(top, ay - 1):
            for x in range(x0, x1 + 1):
                c = 'wood_dk' if (y - top) % 9 == 8 else ('plank_dk' if x not in (x0, x1) else 'wood_dk')
                if x in (x0, x1) or y == top:
                    c = 'ink' if y == top else 'wood_dk'
                setp(x, y, c)
        cols = ['band', 'glass', 'leaf', 'gold', 'cream', 'river', 'tin', 'roof_lt']
        i = 0
        for shelf_y in (top + 8, top + 17, top + 25):
            x = x0 + 2
            while x < x1 - 3:
                h = 3 + (i * 5) % 4
                w = 2 + (i * 3) % 2
                for y in range(shelf_y - h, shelf_y):
                    for xx in range(x, x + w):
                        setp(xx, y, cols[i % len(cols)])
                setp(x, shelf_y - h, 'cream')
                x += w + 1 + (i % 3 == 0)
                i += 1
    add(ay - 20, draw)


def draw_fireplace(ax, ay):
    def draw():
        x0, x1, top = ax - 8, ax + 23, ay - 30
        for y in range(top, ay + 1):
            for x in range(x0, x1 + 1):
                row = (y - top) // 4
                c = 'stone_lt' if x < x0 + 8 else ('stone' if x < x1 - 6 else 'stone_dk')
                if (y - top) % 4 == 0 or (x + (3 if row % 2 else 0)) % 8 == 0:
                    c = 'stone_dk'
                if x in (x0, x1) or y in (top, ay):
                    c = 'ink'
                setp(x, y, c)
        for x in range(x0 - 1, x1 + 2):
            setp(x, top + 8, 'wood_lt'); setp(x, top + 9, 'wood_dk')
        for y in range(top + 14, ay):                                   # firebox
            for x in range(x0 + 6, x1 - 5):
                d = ((x - (x0 + x1) / 2) / 10) ** 2 + ((y - ay + 2) / 12) ** 2
                if y > ay - 8 or d <= 1:
                    setp(x, y, C('#1E1B2C'))
        for (x, y) in ellipse_pts((x0 + x1) / 2, ay - 4, 5, 5):        # flames
            if y < ay - 1:
                dd = abs(x - (x0 + x1) / 2) + (ay - 4 - y) * 0.4
                setp(x, y, 'glow' if dd < 2 else 'glass')
        for x in range(x0 + 9, x1 - 8):
            setp(x, ay - 1, 'trunk'); setp(x, ay - 2, 'trunk_lt' if x % 3 else 'trunk_dk')
    add(ay - 20, draw)


def draw_table(ax, ay, w=2):
    def draw():
        x0, x1 = ax - 6, ax - 8 + 16 * w - 3
        for y in range(ay - 12, ay - 3):
            for x in range(x0, x1 + 1):
                c = 'wood_lt' if y < ay - 9 else 'wood'
                if x in (x0, x1) or y == ay - 12:
                    c = 'ink'
                setp(x, y, c)
        for x in range(x0, x1 + 1):
            setp(x, ay - 3, 'wood_dk'); setp(x, ay - 2, 'ink')
        for lx in (x0 + 1, x1 - 2):
            for y in range(ay - 2, ay + 2):
                setp(lx, y, 'wood_dk'); setp(lx + 1, y, 'ink')
        for y in range(ay - 11, ay - 8):                                # plate + mug
            for x in range(x0 + 4, x0 + 9):
                setp(x, y, 'cream' if y != ay - 9 else 'sand_dk')
        for y in range(ay - 14, ay - 9):
            for x in range(x1 - 7, x1 - 4):
                setp(x, y, 'tin' if x < x1 - 5 else 'tin_dk')
    add(ay, draw, (ax + 8, ay + 1, 14, 2))


def draw_stool(ax, ay):
    def draw():
        for (x, y) in ellipse_pts(ax, ay - 6, 4, 2.5):
            setp(x, y, 'wood_lt' if y < ay - 6 else 'wood')
        for lx in (ax - 3, ax + 2):
            for y in range(ay - 4, ay + 1):
                setp(lx, y, 'wood_dk')
    add(ay, draw, (ax + 2, ay, 4, 1.5))


def draw_window(ax, ay, night=False):
    def draw():
        x0, x1, y0, y1 = ax - 7, ax + 6, ay - 26, ay - 12
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if x in (x0, x1) or y in (y0, y1) or x == (x0 + x1) // 2 or y == (y0 + y1) // 2:
                    c = 'wood_dk'
                else:
                    if night:
                        c = 'slate_dk' if (x * 7 + y * 3) % 17 else 'cream'
                    else:
                        c = 'glass_lt' if (x - y) % 7 in (0, 1) else 'sky' if False else 'river_lt'
                setp(x, y, c)
        for x in range(x0 - 1, x1 + 2):
            setp(x, y1 + 1, 'wood_lt'); setp(x, y1 + 2, 'wood_dk')
    add(ay - 20, draw)


def draw_rug(ax, ay, w=3, h=2):
    def draw():
        x0, x1, y0, y1 = ax - 8, ax - 8 + 16 * w - 1, ay - 14, ay - 14 + 16 * h - 1
        for y in range(y0 + 2, y1 - 1):
            for x in range(x0 + 2, x1 - 1):
                b = min(x - x0 - 2, x1 - 2 - x, y - y0 - 2, y1 - 2 - y)
                c = 'band' if b in (0, 1) else ('gold' if b == 3 else ('roof_dk' if ((x + y) // 3) % 4 == 0 else 'band'))
                if b == 2 or b == 4:
                    c = 'roof_dk'
                setp(x, y, c)
        for x in range(x0 + 3, x1 - 1, 2):
            setp(x, y0 + 1, 'cream'); setp(x, y1 - 1, 'cream')
    add(-1000, draw)


def draw_sacks(ax, ay):
    def draw():
        for (cx, cy) in ((ax - 3, ay - 5), (ax + 4, ay - 4)):
            pts = set(ellipse_pts(cx, cy, 4.5, 5))
            for (x, y) in pts:
                setp(x, y, lit_key((x - cx) / 4.5, (y - cy) / 5, ['sand_lt', 'sand', 'sand_dk'], x, y))
            for (x, y) in pts:
                if (x + 1, y) not in pts or (x, y + 1) not in pts:
                    setp(x, y, 'ink')
            setp(cx, cy - 5, 'trunk_dk'); setp(cx - 1, cy - 6, 'sand_dk'); setp(cx + 1, cy - 6, 'sand_dk')
    add(ay, draw, (ax + 3, ay, 8, 2))


def draw_bench(ax, ay, n=3):
    def draw():
        x0, x1 = ax - 8, ax - 8 + 16 * n - 1
        for y in range(ay - 14, ay - 5):
            for x in range(x0, x1 + 1):
                c = 'wood_lt' if y < ay - 11 else 'wood'
                if x in (x0, x1) or y == ay - 14:
                    c = 'ink'
                setp(x, y, c)
        for x in range(x0, x1 + 1):
            setp(x, ay - 5, 'wood_dk')
        for lx in (x0 + 1, x0 + 22, x1 - 2):
            for y in range(ay - 4, ay + 1):
                setp(lx, y, 'wood_dk'); setp(lx + 1, y, 'ink')
        for k in range(8):                                              # saw, mallet, shavings
            setp(x0 + 4 + k, ay - 13 + k // 4, 'iron')
        for y in range(ay - 14, ay - 10):
            for x in range(x0 + 20, x0 + 25):
                setp(x, y, 'trunk')
        for x in range(x0 + 24, x0 + 31):
            setp(x, ay - 12, 'wood_dk')
        for (x, y) in ((x1 - 8, ay - 12), (x1 - 6, ay - 11), (x1 - 10, ay - 10), (x1 - 5, ay - 13)):
            setp(x, y, 'cream')
    add(ay, draw, (ax + 16, ay + 1, 24, 2))


def draw_boatmodel(ax, ay):
    def draw():
        x0, x1 = ax - 6, ax + 21
        for lx in (x0 + 4, x1 - 4):                                     # stand
            for y in range(ay - 6, ay + 1):
                setp(lx, y, 'wood_dk')
        for x in range(x0 + 2, x1 - 1):
            setp(x, ay - 6, 'wood')
        for x in range(x0, x1 + 1):                                     # hull
            t = (x - x0) / (x1 - x0)
            depth = int(round(6 * np.sin(np.pi * t) ** 0.5))
            for k in range(depth + 1):
                y = ay - 8 - 6 + k + (6 - depth)
                c = 'roof_lt' if k < 2 else ('roof' if k < depth else 'ink')
                setp(x, y, c)
        for y in range(ay - 30, ay - 13):                               # mast + sail
            setp(ax + 7, y, 'trunk_dk')
        for y in range(ay - 28, ay - 15):
            for x in range(ax + 8, ax + 8 + (y - ay + 30) // 2 + 1):
                setp(x, y, 'cream' if x < ax + 12 else 'sand')
    add(ay, draw, (ax + 8, ay + 1, 12, 2))


def draw_planks(ax, ay):
    def draw():
        for i in range(4):
            x = ax - 6 + i * 3
            for y in range(ay - 26 + i, ay + 1):
                setp(x, y, 'wood_lt'); setp(x + 1, y, 'wood'); setp(x + 2, y, 'ink' if i == 3 else 'wood_dk')
    add(ay, draw, (ax + 3, ay, 7, 2))


def draw_nets(ax, ay):
    def draw():
        x0, x1, top = ax - 8, ax + 23, ay - 27
        for x in range(x0, x1 + 1):
            setp(x, top, 'trunk_dk')
        for x in range(x0 + 1, x1):
            sag = int(round(8 * np.sin(np.pi * (x - x0) / (x1 - x0))))
            for y in range(top + 1, top + 9 + sag):
                if (x + y) % 3 == 0 or (x - y) % 3 == 0:
                    setp(x, y, 'sand_dk')
        for fx in (x0 + 6, x0 + 16, x0 + 26):
            for (x, y) in ellipse_pts(fx, top + 12, 1.5, 1.5):
                setp(x, y, 'band')
    add(ay - 20, draw)


def draw_bed(ax, ay):
    def draw():
        x0, x1, y0 = ax - 7, ax + 6, ay - 28
        for y in range(y0, ay + 1):
            for x in range(x0, x1 + 1):
                if y < y0 + 8:
                    c = 'cream' if y > y0 + 2 else 'wood_dk'
                else:
                    c = 'blanket' if ((y - y0) // 3) % 3 else 'blanket_lt'
                if x in (x0, x1) or y in (y0, ay):
                    c = 'wood_dk' if y != ay else 'ink'
                setp(x, y, c)
    add(ay, draw, (ax + 2, ay, 9, 2))


def draw_stove(ax, ay):
    def draw():
        x0, x1, top = ax - 6, ax + 5, ay - 24
        for y in range(top, ay + 1):
            for x in range(x0, x1 + 1):
                c = 'iron' if x < x1 - 2 else 'slate_dk'
                if x in (x0, x1) or y in (top, ay):
                    c = 'ink'
                setp(x, y, c)
        for y in range(ay - 9, ay - 3):
            for x in range(x0 + 3, x1 - 2):
                setp(x, y, 'glass' if y > ay - 7 else 'glow')
        for y in range(top - 12, top):
            setp(ax - 1, y, 'iron'); setp(ax, y, 'slate_dk')
    add(ay - 20, draw)


def draw_crystal(ax, ay):
    def draw():
        for (dx, h, w) in ((-3, 9, 2), (1, 13, 2), (4, 7, 2), (-1, 6, 1)):
            for k in range(h):
                ww = w if k < h - 3 else max(0, w - (k - h + 4))
                for x in range(ax + dx - ww, ax + dx + ww + 1):
                    setp(x, ay - k, 'frz_hi' if x <= ax + dx - ww + 1 else 'frz')
            setp(ax + dx, ay - h, 'frz_hi')
    add(ay, draw, (ax + 2, ay, 6, 2))


def draw_boulder(ax, ay):
    G['rock'](ax, ay, 13, 9)


def draw_toolrack(ax, ay, pick=True):
    def draw():
        x0, x1 = ax - 7, ax + 7
        for lx in (x0, x1):
            for y in range(ay - 22, ay + 1):
                setp(lx, y, 'wood'); setp(lx + 1, y, 'wood_dk')
        for x in range(x0, x1 + 2):
            setp(x, ay - 20, 'wood_lt'); setp(x, ay - 6, 'wood_lt'); setp(x, ay - 5, 'wood_dk')
        for k in range(14):                                              # a shovel
            setp(x1 - 3, ay - 19 + k, 'trunk')
        for y in range(ay - 7, ay - 3):
            for x in range(x1 - 5, x1 - 1):
                setp(x, y, 'iron')
        if pick:
            for k in range(15):
                setp(x0 + 4 + k // 5, ay - 4 - k, 'trunk_lt')
            for k in range(-5, 6):
                setp(x0 + 7 + k, ay - 19 + abs(k) // 2, 'iron')
                setp(x0 + 7 + k, ay - 18 + abs(k) // 2, 'slate_dk')
    add(ay, draw, (ax + 3, ay, 8, 2))


def draw_note(ax, ay):
    def draw():
        for y in range(ay - 20, ay - 15):
            for x in range(ax - 3, ax + 4):
                setp(x, y, 'cream' if (x, y) != (ax + 3, ay - 20) else 'sand_dk')
        for x in range(ax - 2, ax + 2):
            setp(x, ay - 18, 'slate')
        setp(ax - 2, ay - 16, 'slate')
    add(ay + 1, draw)


ROOM_KINDS = {
    'counter4': (draw_counter, (80, 32), (8, 26), {}),
    'shelf3': (draw_shelf, (64, 40), (8, 34), {}),
    'fireplace': (draw_fireplace, (48, 40), (8, 34), {}),
    'table': (draw_table, (40, 28), (8, 22), {}),
    'stool': (draw_stool, (16, 16), (8, 12), {}),
    'window': (draw_window, (24, 36), (12, 30), {}),
    'window_night': (lambda x, y: draw_window(x, y, True), (24, 36), (12, 30), {}),
    'rug': (draw_rug, (56, 40), (8, 18), {'flat': True}),
    'sacks': (draw_sacks, (24, 20), (12, 15), {}),
    'bench3': (draw_bench, (56, 24), (8, 18), {}),
    'boatmodel': (draw_boatmodel, (40, 40), (8, 34), {}),
    'planks': (draw_planks, (24, 32), (8, 28), {}),
    'nets': (draw_nets, (48, 40), (8, 34), {}),
    'bed': (draw_bed, (24, 36), (12, 32), {}),
    'stove': (draw_stove, (24, 44), (12, 38), {}),
    'crystal': (draw_crystal, (24, 24), (12, 20), {}),
    'boulder': (draw_boulder, (32, 24), (16, 20), {}),
    'toolrack': (draw_toolrack, (24, 32), (12, 28), {}),
    'toolrack_empty': (lambda x, y: draw_toolrack(x, y, False), (24, 32), (12, 28), {}),
    'note': (draw_note, (16, 28), (8, 24), {}),
}
ROOM_EMISSIVE = {'fireplace': ('glow', 'glass'), 'stove': ('glow', 'glass'), 'crystal': ('frz_hi', 'frz')}


def build_room_objects(manifest):
    for kind, (fn, size, anchor, opt) in ROOM_KINDS.items():
        rgba, shadow, anc = PB.render_sprite(fn, 'summer', size, anchor)
        spr, (ox, oy) = PB.crop(rgba, anc)
        PB.save_rgba(spr, os.path.join(ART, 'objects', f'{kind}.png'))
        manifest[kind] = {'ox': int(ox), 'oy': int(oy), 'w': int(spr.shape[1]), 'h': int(spr.shape[0]), 'seasonal': False}
        if opt.get('flat'):
            manifest[kind]['flat'] = True
    for kind in ('barrel', 'crate'):                                    # indoor copies of map props (no snow)
        manifest[kind + '_in'] = dict(manifest[kind], seasonal=False, file=kind + '_summer')
    PB.build_lights(manifest, ROOM_KINDS, ROOM_EMISSIVE)


# ====================================================================== room + cave grounds
def build_room_grounds():
    os.makedirs(os.path.join(ART, 'rooms'), exist_ok=True)
    PB.set_palette('summer')
    maps = ROOMS.build()
    for mid, m in maps.items():
        img = cave_ground(m) if m['kind'] == 'cave' else room_ground(m)
        PB.save_rgba(img, os.path.join(ART, 'rooms', f'{mid}.png'))


def room_ground(m):
    T = m['terrain']
    Wt, Ht = m['width'], m['height']
    img = np.zeros((Ht * 16, Wt * 16, 3), np.uint8)
    R = np.random.default_rng(len(m['id'])).random((Ht * 16, Wt * 16))
    stone = m['floor'] == 'stone'

    def tile(x, y):
        return T[y][x] if 0 <= x < Wt and 0 <= y < Ht else 'W'

    def is_face(x, y):
        return tile(x, y) in 'WSU' and (tile(x, y + 1) not in 'WSU' or tile(x, y + 2) not in 'WSU') and \
            any(tile(x, yy) == '.' for yy in (y + 1, y + 2))
    for ty in range(Ht):
        for tx in range(Wt):
            ch = tile(tx, ty)
            x0, y0 = tx * 16, ty * 16
            for yy in range(16):
                for xx in range(16):
                    X, Y = x0 + xx, y0 + yy
                    if ch in '.D':
                        if stone:
                            row = Y // 8
                            joint = Y % 8 == 0 or (X + (5 if row % 2 else 0)) % 12 == 0
                            c = C('#3D3550') if joint else (C('#6E4A35') if R[Y, X] < 0.03 else C('#8A8496'))
                        else:
                            row = Y // 5
                            seam = Y % 5 == 4 or (X + row * 11) % 32 == 0
                            c = P('plank_dk') if seam else (P('plank_lt') if Y % 5 == 0 else P('plank'))

                    elif is_face(tx, ty) or ch in 'SU':
                        top_face = tile(tx, ty + 1) in 'WSU'
                        if m['wall'] == 'stone':
                            row = Y // 5
                            joint = Y % 5 == 0 or (X + (4 if row % 2 else 0)) % 10 == 0
                            c = C('#3D3550') if joint else C('#8A8496')
                            if yy >= 9 and not top_face:
                                c = C('#3D3550') if joint else C('#6E4A35')
                        else:
                            c = P('wood') if (X % 6) not in (0, 5) else P('wood_dk')
                            if X % 6 == 1:
                                c = P('wood_lt')
                            if not top_face and yy >= 9:                # wainscot
                                c = P('trunk') if yy != 9 else P('trunk_lt')
                                if yy == 15:
                                    c = P('trunk_dk')
                        if top_face and yy < 3:
                            c = C('#1E1B2C') if yy == 0 else C('#3D3550')
                    else:                                               # wall top
                        c = C('#1E1B2C') if (X * 3 + Y * 5) % 11 else C('#3D3550')
                    img[Y, X] = c
            if ch == 'D':                                               # door mat + threshold
                for yy in range(3, 14):
                    for xx in range(2, 14):
                        img[y0 + yy, x0 + xx] = P('band') if (xx + yy) % 4 else P('roof_dk')
                img[y0 + 14:y0 + 16, x0:x0 + 16] = C('#1E1B2C')
            if ch == 'S':                                               # cellar door in the back wall
                for yy in range(1, 16):
                    for xx in range(3, 13):
                        c = P('trunk_dk') if xx in (3, 12) or yy == 1 else (P('trunk') if xx % 3 else P('trunk_dk'))
                        if yy in (5, 12):
                            c = P('iron')
                        img[y0 + yy, x0 + xx] = c
                img[y0 + 9, x0 + 10] = P('gold')
            if ch == 'U':                                               # stairs going up
                for yy in range(0, 16):
                    for xx in range(2, 14):
                        step = yy // 4
                        c = [P('wood_dk'), P('wood'), P('wood_lt'), P('plank_lt')][step]
                        if yy % 4 == 3:
                            c = P('trunk_dk')
                        if xx in (2, 13):
                            c = P('ink')
                        img[y0 + yy, x0 + xx] = c
    for ty in range(Ht):                                                # contact shadows under walls
        for tx in range(Wt):
            if tile(tx, ty) in '.D':
                if tile(tx, ty - 1) in 'WSU':
                    img[ty * 16:ty * 16 + 3, tx * 16:tx * 16 + 16] = (img[ty * 16:ty * 16 + 3, tx * 16:tx * 16 + 16] * 0.7)
                if tile(tx - 1, ty) == 'W':
                    img[ty * 16:ty * 16 + 16, tx * 16:tx * 16 + 2] = (img[ty * 16:ty * 16 + 16, tx * 16:tx * 16 + 2] * 0.75)
    for o in m['objects']:                                               # baked shadows of furniture
        if o['kind'] in ('rug',):
            continue
    rgba = np.zeros(img.shape[:2] + (4,), np.uint8)
    rgba[..., :3] = PB.quantize(img)
    rgba[..., 3] = 255
    return rgba


def cave_ground(m):
    T = m['terrain']
    Wt, Ht = m['width'], m['height']
    HH, WW = Ht * 16, Wt * 16
    img = np.zeros((HH, WW, 3), np.uint8)
    R = np.random.default_rng(9).random((HH, WW))
    sn = G['smooth_noise']
    n1 = sn(WW, HH, 7, 90)

    def tile(x, y):
        return T[y][x] if 0 <= x < Wt and 0 <= y < Ht else 'W'
    for Y in range(HH):
        for X in range(WW):
            tx, ty = X // 16, Y // 16
            ch = tile(tx, ty)
            yy = Y % 16
            if ch == 'W':
                if tile(tx, ty + 1) != 'W':                             # rock face
                    k = yy / 16
                    c = C('#8A8496') if k < 0.45 else C('#3D3550')
                    if (Y + int(round(2 * np.sin(X / 4.0)))) % 5 == 0 or (X * 7 + Y) % 13 == 0:
                        c = C('#3D3550') if k < 0.45 else C('#1E1B2C')
                    if yy < 2:
                        c = C('#9CD0C9') if yy == 0 and (X % 5) else C('#8A8496')
                else:
                    c = C('#1E1B2C') if n1[Y, X] > -0.35 or (X + Y) % 2 else C('#3D3550')
            elif ch == '=':
                c = C('#2E5466') if (X + Y // 2) % 9 else C('#4E8C95')
                if tile(tx, ty - 1) != '=' and yy < 2:
                    c = C('#1E1B2C')
            else:
                c = C('#6E4A35') if n1[Y, X] > 0.55 else C('#3D3550')
                if R[Y, X] < 0.015:
                    c = C('#8A8496')
                if ch in 'AB' and R[Y, X] < 0.4:
                    c = C('#8A8496')
            img[Y, X] = c
    rgba = np.zeros((HH, WW, 4), np.uint8)
    rgba[..., :3] = PB.quantize(img)
    rgba[..., 3] = 255
    return rgba


# ====================================================================== characters: NPCs from the hero rig
NPC_STYLES = {   # hat style, colour map (hero rig letters -> hex), extras
    'marit': ('hair_bun', {'k': '#A8693F', 'K': '#6E4A35', 'c': '#B8483A', 'C': '#6E4A35', 'l': '#E48A73',
                           'p': '#B8483A', 'P': '#6E4A35', 'y': '#B8483A', 'Y': '#6E4A35'}, {'apron': True}),
    'halvard': ('cap', {'H': '#3D3550', 'h': '#1E1B2C', 'L': '#8A8496', 'k': '#8A8496', 'K': '#3D3550', 'c': '#4E8C95',
                        'C': '#2E5466', 'l': '#9CD0C9', 'y': '#2E5466', 'Y': '#1E1B2C'}, {'beard': '#8A8496'}),
    'eirik': ('hair', {'k': '#6E4A35', 'K': '#3D3550', 'c': '#9CD0C9', 'C': '#4E8C95', 'l': '#F2E3B3', 'y': '#9CD0C9',
                       'Y': '#4E8C95'}, {'apron': '#A8693F', 'beard': '#6E4A35'}),
    'liv': ('sou', {'H': '#E0A256', 'h': '#A8693F', 'L': '#F2E3B3', 'r': '#E0A256', 'k': '#F2E3B3', 'K': '#E0A256',
                    'c': '#E0A256', 'C': '#A8693F', 'l': '#F2E3B3', 'p': '#2E5466', 'P': '#1E1B2C', 'y': '#E0A256',
                    'Y': '#A8693F', 'b': '#A8693F'}, {'long': True}),
    'ole': ('cap', {'H': '#2E5466', 'h': '#1E1B2C', 'L': '#4E8C95', 'k': '#F2E3B3', 'K': '#8A8496', 'c': '#2E5466',
                    'C': '#1E1B2C', 'l': '#4E8C95', 'y': '#F2E3B3', 'Y': '#8A8496', 'p': '#3D3550'},
            {'beard': '#F2E3B3'}),
    'tove': ('hood', {'H': '#4F7A3C', 'h': '#2F4A35', 'L': '#8DB054', 'k': '#B8483A', 'K': '#6E4A35', 'c': '#A8693F',
                      'C': '#6E4A35', 'l': '#E0A256', 'y': '#4F7A3C', 'Y': '#2F4A35', 'p': '#6E4A35'}, {}),
    'hedda': ('kerchief', {'H': '#E48A73', 'h': '#B8483A', 'L': '#F2E3B3', 'k': '#6E4A35', 'K': '#3D3550',
                           'c': '#A8693F', 'C': '#6E4A35', 'l': '#E0A256', 'y': '#A8693F', 'Y': '#6E4A35'},
              {'apron': True}),
    'selma': ('hood', {'H': '#3D3550', 'h': '#1E1B2C', 'L': '#8A8496', 'k': '#F2E3B3', 'K': '#9CD0C9', 'c': '#3D3550',
                       'C': '#1E1B2C', 'l': '#8A8496', 'p': '#3D3550', 'P': '#1E1B2C', 'y': '#9CD0C9', 'Y': '#4E8C95'},
              {'long': True}),
    'sigve': ('brim', {'H': '#8A8496', 'h': '#3D3550', 'L': '#9CD0C9', 'r': '#B8483A', 'k': '#1E1B2C', 'K': '#3D3550',
                       'c': '#4F7A3C', 'C': '#2F4A35', 'l': '#8DB054', 'y': '#4E8C95', 'Y': '#2E5466'},
              {'beard': '#3D3550', 'scarf': True}),
    'collector': ('tall', {'H': '#3D3550', 'h': '#1E1B2C', 'L': '#8A8496', 'r': '#E0A256', 'k': '#8A8496',
                           'K': '#3D3550', 'c': '#8A8496', 'C': '#3D3550', 'l': '#F2E3B3', 'b': '#E0A256',
                           'y': '#E0A256', 'Y': '#A8693F', 'p': '#3D3550', 'P': '#1E1B2C'}, {'moustache': '#3D3550'}),
    'ingrid': ('kerchief', {'H': '#4E8C95', 'h': '#2E5466', 'L': '#9CD0C9', 'k': '#1E1B2C', 'K': '#3D3550',
                            'c': '#E48A73', 'C': '#B8483A', 'l': '#F2E3B3', 'y': '#4E8C95', 'Y': '#2E5466'},
               {'feather': True, 'long': True}),
    'joar': ('cap', {'H': '#B8483A', 'h': '#6E4A35', 'L': '#E48A73', 'k': '#1E1B2C', 'K': '#3D3550', 'c': '#6E4A35',
                     'C': '#3D3550', 'l': '#A8693F', 'y': '#E0A256', 'Y': '#A8693F'}, {'beard': '#1E1B2C', 'scarf': True}),
    'brit': ('kerchief', {'H': '#B8483A', 'h': '#6E4A35', 'L': '#E48A73', 'k': '#E0A256', 'K': '#A8693F',
                          'c': '#9CD0C9', 'C': '#4E8C95', 'l': '#F2E3B3', 'y': '#9CD0C9', 'Y': '#4E8C95'}, {}),
    'tobias': ('cap', {'H': '#8A8496', 'h': '#3D3550', 'L': '#9CD0C9', 'k': '#8A8496', 'K': '#3D3550', 'c': '#4F7A3C',
                       'C': '#2F4A35', 'l': '#8DB054', 'y': '#4F7A3C', 'Y': '#2F4A35'}, {'beard': '#8A8496'}),
    'arne': ('hood', {'H': '#6E4A35', 'h': '#3D3550', 'L': '#A8693F', 'k': '#F2E3B3', 'K': '#8A8496', 'c': '#A8693F',
                      'C': '#6E4A35', 'l': '#E0A256', 'y': '#6E4A35', 'Y': '#3D3550', 'p': '#6E4A35'},
             {'beard': '#F2E3B3', 'long_beard': True}),
    'ylva': ('hair_braids', {'k': '#E0A256', 'K': '#A8693F', 'c': '#E48A73', 'C': '#B8483A', 'l': '#F2E3B3',
                             'p': '#E48A73', 'P': '#B8483A', 'y': '#E48A73', 'Y': '#B8483A'}, {}),
}


def make_hat(style):
    def hat(g, side=False, back=False):
        if style == 'brim':
            ORIG_HAT(g, side, back)
        elif style == 'cap':
            g.rect(5, 5, 14, 7, 'H'); g.rect(6, 4, 13, 4, 'H'); g.rect(6, 4, 8, 5, 'L'); g.rect(12, 4, 13, 5, 'h')
            if side:
                g.rect(12, 7, 17, 7, 'h'); g.rect(5, 5, 6, 7, 'h')
            elif not back:
                g.rect(5, 7, 14, 7, 'h')
        elif style in ('hair', 'hair_bun', 'hair_braids'):
            g.rect(5, 5, 14, 7, 'k'); g.rect(6, 4, 13, 4, 'k'); g.put(6, 5, 'K'); g.put(13, 5, 'K')
            if style == 'hair_bun':
                g.rect(8, 1, 11, 3, 'k'); g.put(8, 1, 'K'); g.put(11, 3, 'K')
            if style == 'hair_braids':
                for (x, y) in ((4, 8), (4, 9), (4, 10), (3, 11), (3, 12), (15, 8), (15, 9), (15, 10), (16, 11), (16, 12)):
                    if not side or x < 10:
                        g.put(x, y, 'k')
                g.put(3, 13, 'r'); g.put(16, 13, 'r')
            if side:
                g.rect(5, 8, 8, 10, 'k')
            if back:
                g.rect(5, 8, 14, 11, 'k')
        elif style == 'hood':
            g.rect(5, 3, 14, 7, 'H'); g.rect(4, 5, 15, 7, 'H'); g.rect(6, 2, 13, 2, 'H')
            g.rect(5, 3, 6, 6, 'L'); g.rect(14, 4, 15, 7, 'h')
            if back:
                g.rect(4, 3, 15, 12, 'H'); g.rect(4, 3, 5, 12, 'L'); g.rect(14, 3, 15, 12, 'h'); g.rect(9, 3, 9, 12, 'h')
            elif side:
                g.rect(4, 6, 8, 12, 'H'); g.rect(4, 6, 4, 12, 'L'); g.rect(13, 4, 14, 7, 'h')
            else:
                g.rect(4, 8, 4, 12, 'H'); g.rect(15, 8, 15, 12, 'h')
        elif style == 'kerchief':
            g.rect(5, 4, 14, 7, 'H'); g.rect(6, 3, 13, 3, 'H')
            for (x, y) in ((6, 5), (9, 4), (12, 5), (8, 7), (11, 7), (13, 7)):
                g.put(x, y, 'L')
            if back:
                g.rect(8, 8, 11, 9, 'H'); g.put(8, 10, 'h'); g.put(11, 10, 'h')
            elif side:
                g.rect(4, 7, 5, 9, 'H'); g.put(4, 10, 'h')
        elif style == 'sou':
            g.rect(6, 3, 13, 6, 'H'); g.rect(7, 2, 12, 2, 'H'); g.rect(6, 3, 7, 6, 'L'); g.rect(12, 3, 13, 6, 'h')
            if side:
                g.rect(5, 7, 17, 7, 'H'); g.rect(3, 7, 6, 10, 'H'); g.put(3, 10, 'h'); g.rect(13, 7, 17, 7, 'L')
            elif back:
                g.rect(3, 7, 16, 9, 'H'); g.rect(3, 9, 16, 9, 'h')
            else:
                g.rect(3, 7, 16, 7, 'H'); g.rect(3, 7, 6, 7, 'L'); g.put(3, 8, 'h'); g.put(16, 8, 'h')
        elif style == 'tall':
            g.rect(6, 0, 13, 4, 'H'); g.rect(6, 0, 7, 4, 'L'); g.rect(12, 0, 13, 4, 'h'); g.rect(6, 5, 13, 5, 'r')
            if side:
                g.rect(4, 6, 17, 6, 'H'); g.rect(5, 7, 16, 7, 'h')
            else:
                g.rect(3, 6, 16, 6, 'H'); g.rect(4, 7, 15, 7, 'h')
    return hat


ORIG_HAT = PB.hat
ORIG_SCARF = PB.scarf_tail


def npc_rows(npc, direction):
    style, pal, extra = NPC_STYLES[npc]
    PB.hat = make_hat(style)
    PB.scarf_tail = ORIG_SCARF if extra.get('scarf') else (lambda g, pose: None)
    try:
        rows = [list(r) for r in PB.hero_body(direction, 0)]
    finally:
        PB.hat, PB.scarf_tail = ORIG_HAT, ORIG_SCARF

    def put(x, y, c):
        if 0 <= y < len(rows) and 0 <= x < len(rows[0]) and rows[y][x] not in '.o':
            rows[y][x] = c
    if extra.get('apron'):
        ap = extra['apron'] if isinstance(extra['apron'], str) else '#F2E3B3'
        pal = dict(pal, A=ap)
        if direction == 'down':
            for y in range(13, 19):
                for x in range(7, 13):
                    put(x, y, 'A')
        elif direction == 'right':
            for y in range(13, 19):
                for x in range(12, 14):
                    put(x, y, 'A')
    if extra.get('beard') and direction != 'up':
        pal = dict(pal, B=extra['beard'])
        if direction == 'down':
            cells = [(5, 10), (14, 10), (5, 11), (6, 11), (13, 11), (14, 11)] + [(x, 12) for x in range(6, 14)]
            if extra.get('long_beard'):
                cells += [(x, 13) for x in range(7, 13)] + [(x, 14) for x in range(8, 12)]
        else:
            cells = [(9, 10), (9, 11), (10, 11), (14, 11)] + [(x, 12) for x in range(10, 15)]
            if extra.get('long_beard'):
                cells += [(x, 13) for x in range(11, 15)]
        for (x, y) in cells:
            put(x, y, 'B')
    if extra.get('moustache') and direction != 'up':
        pal = dict(pal, B=extra['moustache'])
        for x in ((7, 8, 11, 12) if direction == 'down' else (12, 13, 14)):
            put(x, 11, 'B')
    if extra.get('feather'):
        pal = dict(pal, f='#E48A73', F='#B8483A')
        for (x, y, c) in ((15, 2, 'f'), (16, 1, 'f'), (16, 2, 'F'), (15, 3, 'F'), (17, 0, 'f')):
            if 0 <= y < len(rows):
                rows[y][x] = c
    return [''.join(r) for r in rows], pal


def char_rgba(rows, pal):
    a = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    PB.set_palette('summer')
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in '.o':
                continue
            v = pal.get(ch) or PB.HPAL.get(ch)
            a[y, x, :3] = C(v) if v.startswith('#') else G['P'][v]
            a[y, x, 3] = 255
    out = a.copy()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != 'o':
                continue
            acc = [a[yy, xx, :3].astype(float) for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)
                   if 0 <= yy < len(rows) and 0 <= xx < len(row) and a[yy, xx, 3]]
            if acc:
                ext = lambda yy, xx: not (0 <= yy < len(rows) and 0 <= xx < len(row)) or rows[yy][xx] == '.'
                lit = (ext(y - 1, x) or ext(y, x - 1)) and not (ext(y + 1, x) or ext(y, x + 1))
                out[y, x, :3] = np.clip(np.mean(acc, axis=0) * (0.84 if lit else 0.6), 0, 255)
                out[y, x, 3] = 255
    out[..., :3] = PB.quantize(out[..., :3])
    return out


def build_npcs():
    d = os.path.join(ART, 'npcs')
    os.makedirs(d, exist_ok=True)
    for npc in NPC_STYLES:
        sheet = np.zeros((PB.HH_, PB.HW * 3, 4), np.uint8)
        for i, direction in enumerate(('down', 'up', 'right')):
            rows, pal = npc_rows(npc, direction)
            sheet[:, i * PB.HW:(i + 1) * PB.HW] = char_rgba(rows, pal)
        PB.save_rgba(sheet, os.path.join(d, f'{npc}.png'))


# ====================================================================== companions + the great erne
class Spr:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = np.zeros((h, w, 3), np.uint8)
        self.a = np.zeros((h, w), bool)
        self.outl = np.zeros((h, w), bool)

    def set(self, x, y, c, outline=False):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img[y, x] = C(c) if isinstance(c, str) and c.startswith('#') else (G['P'][c] if isinstance(c, str) else c)
            self.a[y, x] = True
            self.outl[y, x] = outline

    def shape(self, pix, colour, outline=True):
        pix = set(pix)
        for (x, y) in pix:
            self.set(x, y, colour(x, y) if callable(colour) else colour)
        if outline:
            for (x, y) in pix:
                if any((x + dx, y + dy) not in pix for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.set(x, y, '#1E1B2C', outline=True)

    def rgba(self, soft=True):
        img = self.img.copy()
        if soft:
            inner = self.a & ~self.outl
            for y, x in zip(*np.where(self.outl)):
                acc = [self.img[yy, xx] for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)
                       if 0 <= yy < self.h and 0 <= xx < self.w and inner[yy, xx]]
                if acc:
                    out = lambda yy, xx: not (0 <= yy < self.h and 0 <= xx < self.w) or not self.a[yy, xx]
                    lit = (out(y - 1, x) or out(y, x - 1)) and not (out(y + 1, x) or out(y, x + 1))
                    img[y, x] = np.clip(np.mean(acc, axis=0) * (0.84 if lit else 0.6), 0, 255)
        out = np.zeros((self.h, self.w, 4), np.uint8)
        out[..., :3] = PB.quantize(img)
        out[..., 3] = self.a * 255
        return out


def shade3(cx, cy, rx, ry, lt, md, dk):
    def f(x, y):
        v = -(0.6 * (x - cx) / rx + 0.8 * (y - cy) / ry)
        return lt if v > 0.35 else (md if v > -0.45 else dk)
    return f


def ell(cx, cy, rx, ry):
    return set(ellipse_pts(cx, cy, rx, ry))


def limb(x0, y0, x1, y1, w0, w1):
    return MI.limb(x0, y0, x1, y1, w0, w1)


FOX = ('#E0A256', '#A8693F', '#6E4A35')
OWL = ('#A8693F', '#6E4A35', '#3D3550')


def fox_frame(direction, f):
    s = Spr(20, 16)
    b = [0, -1, 0, -1][f]
    lt, md, dk = FOX
    step = [0, 1, 0, -1][f]
    if direction == 'right':
        tail = limb(5, 10 + b, 1, 6 + b - step, 2.0, 1.4)
        s.shape(tail, shade3(3, 8, 3, 3, lt, md, dk))
        for (x, y) in ell(1, 6 + b - step, 1.6, 1.6):
            s.set(x, y, 'cream')
        for (lx, off) in ((7, step), (12, -step)):                     # legs
            s.shape(limb(lx, 11 + b, lx + off, 14, 0.9, 0.8), lambda x, y: '#3D3550')
        s.shape(ell(9.5, 10 + b, 5, 3), shade3(9.5, 10, 5, 3, lt, md, dk))
        for x in range(7, 13):
            s.set(x, 12 + b, 'cream')
        head = ell(14, 6 + b, 3.5, 3) | limb(14, 7 + b, 18, 8 + b, 1.6, 1.0)
        s.shape(head, shade3(14, 6, 4, 3, lt, md, dk))
        for (x, y) in ((15, 8 + b), (16, 8 + b), (17, 8 + b), (16, 9 + b)):
            s.set(x, y, 'cream')
        s.set(18, 7 + b, '#1E1B2C')
        s.shape(limb(12, 4 + b, 12, 1 + b, 1.3, 0.6), lambda x, y: md)
        s.set(12, 1 + b, '#3D3550')
        s.set(15, 6 + b, '#1E1B2C')
    else:
        back = direction == 'up'
        sway = [0, 1, 0, -1][f]
        if back:
            s.shape(ell(10, 10 + b, 4.5, 3.5), shade3(10, 10, 4.5, 3.5, lt, md, dk))
            tail = limb(10, 12 + b, 10 + sway * 2, 15, 1.8, 1.6)
            s.shape(tail, shade3(10, 13, 2, 2, lt, md, dk))
            s.set(10 + sway * 2, 15, 'cream')
            s.shape(ell(10, 5 + b, 4, 3.2), shade3(10, 5, 4, 3, lt, md, dk))
        else:
            tail = limb(13, 11 + b, 16, 7 + b - sway, 1.8, 1.4)
            s.shape(tail, shade3(14, 9, 3, 3, lt, md, dk))
            for (x, y) in ell(16, 7 + b - sway, 1.4, 1.4):
                s.set(x, y, 'cream')
            s.shape(ell(10, 11 + b, 4.5, 3.2), shade3(10, 11, 4.5, 3.2, lt, md, dk))
            for x in range(8, 13):
                s.set(x, 11 + b, 'cream'); s.set(x, 12 + b, 'cream')
            for lx in (8, 12):
                s.set(lx, 14 + (step if lx == 8 else -step) * 0, '#3D3550'); s.set(lx, 13 + b, '#3D3550')
            s.shape(ell(10, 6 + b, 4.2, 3.3), shade3(10, 6, 4, 3, lt, md, dk))
            for (x, y) in ell(10, 8 + b, 2.2, 1.3):
                s.set(x, y, 'cream')
            s.set(10, 8 + b, '#1E1B2C')
            s.set(8, 6 + b, '#1E1B2C'); s.set(12, 6 + b, '#1E1B2C')
        for ex in (7, 13):
            s.shape(limb(ex, 4 + b, ex + (-1 if ex == 7 else 1), 1 + b, 1.3, 0.6), lambda x, y: md)
            s.set(ex + (-1 if ex == 7 else 1), 1 + b, '#3D3550')
    return s.rgba()


def owl_frame(direction, f):
    """the owlet flutters at shoulder height; a small shadow sits on the ground below it"""
    s = Spr(20, 24)
    b = [0, -1, -2, -1][f]
    lt, md, dk = OWL
    for (x, y) in ell(10, 21, 3.5, 1.2):                              # ground shadow
        if (x + y) % 2 == 0:
            s.set(x, y, '#1E1B2C')
    flap = f in (1, 3)
    cy = 8 + b
    if direction == 'right':
        wing = ell(8, cy + 2, 3, 3.5) if not flap else limb(9, cy, 3, cy - 4, 2.0, 1.0)
        s.shape(ell(10, cy + 1, 4, 5), shade3(10, cy, 4, 5, lt, md, dk))
        s.shape(wing, shade3(8, cy, 3, 3, md, dk, dk))
        s.set(12, cy - 1, '#F2E3B3'); s.set(13, cy - 1, '#E0A256'); s.set(13, cy - 2, '#F2E3B3')
        s.set(13, cy, '#1E1B2C')
        s.set(14, cy + 1, '#E0A256')
        s.set(9, cy - 5, md); s.set(9, cy - 6, dk)
        s.set(9, cy + 6, '#E0A256'); s.set(11, cy + 6, '#E0A256')
    else:
        if flap:
            for sx in (-1, 1):
                s.shape(limb(10 + sx * 3, cy, 10 + sx * 8, cy - 3, 1.8, 0.9), shade3(10, cy, 6, 3, md, dk, dk))
        s.shape(ell(10, cy + 1, 4.5, 5), shade3(10, cy, 4.5, 5, lt, md, dk))
        for sx in (-1, 1):
            s.set(10 + sx * 3, cy - 4, md); s.set(10 + sx * 4, cy - 5, dk)
        if direction == 'down':
            for (x, y) in ell(10, cy - 1, 3.4, 2.4):
                s.set(x, y, '#F2E3B3')
            for ex in (8, 12):
                s.set(ex, cy - 1, '#E0A256'); s.set(ex, cy - 2, '#1E1B2C') if False else s.set(ex, cy - 1, '#1E1B2C')
                s.set(ex + (1 if ex == 8 else -1), cy - 1, '#E0A256')
            s.set(10, cy, '#E0A256')
            for (x, y) in ((9, cy + 3), (11, cy + 3), (10, cy + 4)):
                s.set(x, y, '#F2E3B3')
        else:
            for (x, y) in ((9, cy + 1), (11, cy + 2), (10, cy + 3), (9, cy + 4)):
                s.set(x, y, dk)
        if not flap:
            for sx in (-1, 1):
                for k in range(4):
                    s.set(10 + sx * 4, cy + k, dk)
        s.set(9, cy + 6, '#E0A256'); s.set(11, cy + 6, '#E0A256')
    return s.rgba()


def build_companions():
    d = os.path.join(ART, 'companions')
    os.makedirs(d, exist_ok=True)
    for kind, fn, (w, h) in (('fox', fox_frame, (20, 16)), ('owl', owl_frame, (20, 24))):
        sheet = np.zeros((h * 3, w * 4, 4), np.uint8)
        for r, direction in enumerate(('down', 'up', 'right')):
            for f in range(4):
                sheet[r * h:(r + 1) * h, f * w:(f + 1) * w] = fn(direction, f)
        PB.save_rgba(sheet, os.path.join(d, f'{kind}.png'))


def erne_frame(f):
    """the great erne seen from above, flying up the screen, the cartographer riding on its back"""
    s = Spr(112, 64)
    cx, cy = 56, 30
    lift = [0, -5, 0, 4][f]
    span = [50, 44, 50, 46][f]
    for sx in (-1, 1):                                                 # wings
        tipx, tipy = cx + sx * span, cy - 4 + lift
        wing = set()
        for i in range(0, span + 1):
            x = cx + sx * i
            t = i / span
            lead = cy - 6 + (tipy - 2 - (cy - 6)) * t - (5 * np.sin(np.pi * t / 0.9) if t < 0.9 else 0)
            trail = cy + 13 - (cy + 13 - (tipy + 3)) * t ** 0.8 + (2 if (i // 3) % 2 and 0.3 < t < 0.85 else 0)
            for y in range(int(lead), int(trail) + 1):
                wing.add((x, y))
        for k in range(4):                                             # primary feathers (fingers)
            fy = tipy - 1 + k * 3
            wing |= limb(tipx - sx * 4, fy, tipx + sx * 5, fy + 1 + k, 1.1, 0.7)
        def wcol(x, y, tipx=tipx, sx=sx):
            t = abs(x - cx) / span
            lead = cy - 6 + (tipy - 2 - (cy - 6)) * t - (5 * np.sin(np.pi * t / 0.9) if t < 0.9 else 0)
            if y < lead + 4 and t < 0.8:
                return '#A8693F' if (x + y) % 3 else '#E0A256'
            if t > 0.82:
                return '#3D3550'
            return '#6E4A35' if (x // 2 + y) % 4 else '#3D3550'
        s.shape(wing, wcol)
    s.shape(ell(cx, cy + 16, 6, 6) & {(x, y) for x in range(112) for y in range(cy + 13, 64)},
            lambda x, y: '#F2E3B3' if (x + y) % 4 else '#9CD0C9')        # white tail
    s.shape(ell(cx, cy + 2, 7, 13), shade3(cx, cy, 7, 13, '#A8693F', '#6E4A35', '#3D3550'))
    s.shape(ell(cx, cy - 13, 4.5, 4.5), shade3(cx, cy - 13, 4.5, 4.5, '#F2E3B3', '#E0A256', '#A8693F'))
    for (x, y) in ((cx, cy - 18), (cx, cy - 19), (cx - 1, cy - 18), (cx + 1, cy - 18)):
        s.set(x, y, '#E0A256')
    s.set(cx, cy - 20, '#A8693F')
    rows = PB.hero_body('up', 0)[:16]                                 # rider (seen from behind)
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch not in '.':
                key = PB.HPAL.get(ch) if ch != 'o' else 'ink'
                s.set(cx - 10 + dx, cy - 12 + dy, key, outline=ch == 'o')
    return s.rgba()


def build_erne():
    d = os.path.join(ART, 'companions')
    sheet = np.zeros((64, 112 * 4, 4), np.uint8)
    for f in range(4):
        sheet[:, f * 112:(f + 1) * 112] = erne_frame(f)
    PB.save_rgba(sheet, os.path.join(d, 'erne.png'))
    s = np.zeros((14, 72, 4), np.uint8)                                # flight shadow
    for y in range(14):
        for x in range(72):
            d_ = ((x - 36) / 36) ** 2 + ((y - 7) / 6.5) ** 2
            if d_ <= 1 and (x + y) % 2 == 0:
                s[y, x] = (30, 27, 44, 255)
    PB.save_rgba(s, os.path.join(d, 'erne_shadow.png'))
    o = np.zeros((6, 14, 4), np.uint8)                                  # small soft shadow for people
    for y in range(6):
        for x in range(14):
            if ((x - 6.5) / 7) ** 2 + ((y - 2.5) / 3) ** 2 <= 1:
                o[y, x] = (30, 27, 44, 255)
    PB.save_rgba(o, os.path.join(d, 'shadow.png'))


# ====================================================================== item icons (16 x 16)
def icon(draw):
    s = Spr(16, 16)
    draw(s)
    return s.rgba()


def I_axe(s):
    s.shape(limb(4, 14, 10, 4, 0.9, 0.9), lambda x, y: '#A8693F')
    s.shape({(x, y) for x in range(8, 15) for y in range(2, 8) if (x - 8) + abs(y - 4.5) * 0.6 < 6.5},
            shade3(11, 4, 3, 3, '#9CD0C9', '#8A8496', '#3D3550'))


def I_pickaxe(s):
    s.shape(limb(4, 14, 9, 5, 0.9, 0.9), lambda x, y: '#A8693F')
    s.shape(limb(2, 7, 9, 3, 1.1, 1.3) | limb(9, 3, 14, 8, 1.3, 0.9), shade3(8, 4, 5, 3, '#9CD0C9', '#8A8496', '#3D3550'))


def I_lantern(s):
    s.shape(ell(8, 2.5, 2.2, 2), lambda x, y: '#3D3550')
    s.set(8, 3, '#1E1B2C') if False else None
    s.shape({(x, y) for x in range(5, 12) for y in range(4, 6)}, lambda x, y: '#8A8496')
    s.shape({(x, y) for x in range(5, 12) for y in range(6, 13)},
            lambda x, y: '#3D3550' if x in (5, 11) or x == 8 else ('#F2E3B3' if y < 9 else '#E0A256'))
    s.shape({(x, y) for x in range(4, 13) for y in range(13, 15)}, lambda x, y: '#8A8496')


def I_cellar_key(s):
    ring = ell(5, 5, 3.4, 3.4) - ell(5, 5, 1.4, 1.4)
    s.shape(ring | limb(7, 7, 13, 13, 0.9, 0.9) | {(11, 14), (12, 14), (13, 11), (14, 11)},
            shade3(7, 7, 5, 5, '#F2E3B3', '#E0A256', '#A8693F'))


def I_bird_bell(s):
    bell = {(x, y) for (x, y) in ell(8, 8, 4.5, 5) if y <= 9} | {(x, 10) for x in range(2, 15)} | \
        {(x, 11) for x in range(2, 15)}
    s.shape(bell, shade3(8, 7, 5, 5, '#F2E3B3', '#E0A256', '#A8693F'))
    s.shape(ell(8, 13, 1.4, 1.4), lambda x, y: '#6E4A35')
    s.shape({(7, 2), (8, 2), (9, 2), (7, 1), (9, 1)}, lambda x, y: '#8A8496')
    s.shape(limb(11, 4, 15, 1, 1.0, 0.6), lambda x, y: '#9CD0C9')


def I_bread(s):
    s.shape(ell(8, 9, 6.5, 4), shade3(8, 8, 6.5, 4, '#E0A256', '#A8693F', '#6E4A35'))
    for k in (-3, 0, 3):
        s.set(8 + k, 7, '#F2E3B3'); s.set(9 + k, 8, '#F2E3B3')


def I_lamp_oil(s):
    s.shape({(x, y) for x in range(4, 12) for y in range(5, 15)},
            lambda x, y: '#F2E3B3' if 8 <= y <= 10 else ('#9CD0C9' if x < 6 else '#4E8C95'))
    s.shape(limb(10, 5, 12, 2, 0.8, 0.6), lambda x, y: '#8A8496')
    for x in range(5, 11):
        s.set(x, 9, '#B8483A')


def I_moon_tea(s):
    s.shape({(x, y) for x in range(3, 11) for y in range(7, 14)} | {(11, 9), (12, 9), (12, 10), (12, 11), (11, 11)},
            lambda x, y: '#F2E3B3' if x < 9 else '#9CD0C9')
    for x in range(4, 10):
        s.set(x, 8, '#A8693F')
    for (x, y) in ((5, 5), (6, 4), (5, 3), (8, 5), (9, 4), (8, 2)):
        s.set(x, y, '#9CD0C9')


def I_smoked_fish(s):
    body = limb(2, 9, 11, 8, 2.8, 1.6) | {(x, y) for x in range(11, 15) for y in range(4, 13) if abs(y - 8) <= x - 10}
    s.shape(body, shade3(7, 7, 6, 3, '#E0A256', '#A8693F', '#6E4A35'))
    s.set(4, 8, '#1E1B2C')
    for x in range(6, 11, 2):
        s.set(x, 10, '#6E4A35')


def I_sea_chart(s):
    s.shape({(x, y) for x in range(2, 14) for y in range(3, 13)},
            lambda x, y: '#A8693F' if x in (2, 13) else '#F2E3B3')
    for (x, y) in ((4, 5), (5, 5), (6, 6), (6, 7), (5, 8), (5, 9), (6, 10), (9, 6), (10, 6), (11, 7), (10, 9)):
        s.set(x, y, '#4E8C95')
    s.set(10, 10, '#B8483A')


def I_ship_plans(s):
    s.shape({(x, y) for x in range(2, 14) for y in range(3, 13)}, lambda x, y: '#6E4A35' if x in (2, 13) else '#2E5466')
    for x in range(4, 12):
        s.set(x, 9, '#9CD0C9')
    for (x, y) in ((4, 8), (11, 8), (5, 10), (10, 10), (6, 10), (7, 10), (8, 10), (9, 10), (8, 5), (8, 6), (8, 7), (9, 6),
                   (10, 7)):
        s.set(x, y, '#9CD0C9')
    for y in range(3, 13):
        s.set(7, y, '#B8483A') if y in (3, 12) else None


def I_ring(s):
    outer, hole = ell(8, 9, 5, 4.6), ell(8, 9, 2.2, 1.8)
    s.shape(outer - hole, shade3(8, 9, 5, 4.6, '#F2E3B3', '#9CD0C9', '#8A8496'), outline=False)
    for (x, y) in outer:
        if any((x + a, y + b) not in outer for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            s.set(x, y, '#3D3550', outline=True)
    for (x, y) in hole:
        if any((x + a, y + b) not in hole for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            s.set(x, y, '#8A8496')
    s.shape(ell(8, 4.5, 1.8, 1.6), lambda x, y: '#4E8C95')
    s.set(8, 4, '#F2E3B3')


def I_knife(s):
    s.shape(limb(3, 13, 9, 7, 1.0, 1.2), lambda x, y: '#9CD0C9' if x + y < 16 else '#8A8496')
    s.shape(limb(10, 6, 13, 3, 1.2, 1.2), lambda x, y: '#A8693F')


def I_tern_plank(s):
    s.shape({(x, y) for x in range(1, 15) for y in range(5, 11)}, lambda x, y: '#A8693F' if y < 8 else '#6E4A35')
    for (x, y) in ((5, 7), (6, 8), (7, 7), (8, 6), (9, 7), (10, 8), (11, 7), (7, 8), (8, 9)):
        s.set(x, y, '#F2E3B3')


def I_compass(s):
    s.shape(ell(8, 8, 6, 6), shade3(8, 8, 6, 6, '#F2E3B3', '#E0A256', '#A8693F'))
    for (x, y) in ell(8, 8, 4, 4):
        s.set(x, y, '#F2E3B3')
    for k in range(4):
        s.set(8, 4 + k, '#B8483A'); s.set(8, 8 + k, '#3D3550')
    s.set(7, 5, '#B8483A'); s.set(9, 5, '#B8483A')


def I_amber_heart(s):
    heart = ell(5.5, 6, 3.4, 3.2) | ell(10.5, 6, 3.4, 3.2) | {(x, y) for x in range(2, 15) for y in range(7, 15)
                                                              if abs(x - 8) <= 14 - y - (y - 7) * 0.2}
    s.shape(heart, shade3(7, 6, 6, 6, '#F2E3B3', '#E0A256', '#A8693F'))
    s.set(5, 5, '#F2E3B3'); s.set(6, 5, '#F2E3B3'); s.set(5, 6, '#F2E3B3')
    s.set(9, 10, '#B8483A')


def I_moonstone(s):
    s.shape(ell(8, 9, 4.2, 5), shade3(8, 8, 4.2, 5, '#F2E3B3', '#9CD0C9', '#4E8C95'))
    s.set(6, 6, '#F2E3B3'); s.set(7, 5, '#F2E3B3')
    for (x, y) in ((2, 3), (13, 4), (14, 12), (3, 13)):
        s.set(x, y, '#9CD0C9')


def I_lucky_hook(s):
    hook = limb(10, 2, 10, 10, 0.8, 0.8) | limb(10, 10, 7, 13, 0.9, 0.9) | limb(7, 13, 4, 10, 0.9, 0.8) | \
        limb(4, 10, 5, 8, 0.8, 0.6)
    s.shape(hook, lambda x, y: '#E0A256' if x <= 9 else '#A8693F')
    s.shape(ell(10, 2, 1.4, 1.4), lambda x, y: '#A8693F')


def I_sea_glass(s):
    pts = {(x, y) for x in range(3, 14) for y in range(4, 13) if (x - 3) + (y - 4) > 2 and (13 - x) + (12 - y) > 3
           and (x - 3) + (12 - y) > 1}
    s.shape(pts, shade3(8, 8, 5, 4, '#9CD0C9', '#4E8C95', '#2E5466'))
    s.set(6, 6, '#F2E3B3'); s.set(7, 6, '#F2E3B3')


def I_carving(s):
    s.shape(ell(8, 9, 4.5, 5.5), shade3(8, 8, 4.5, 5.5, '#E0A256', '#A8693F', '#6E4A35'))
    for ex in (6, 10):
        s.set(ex, 7, '#F2E3B3'); s.set(ex, 8, '#1E1B2C') if False else None
    s.set(6, 7, '#F2E3B3'); s.set(10, 7, '#F2E3B3'); s.set(6, 8, '#1E1B2C'); s.set(10, 8, '#1E1B2C')
    s.set(8, 9, '#6E4A35')
    s.set(5, 3, '#A8693F'); s.set(11, 3, '#A8693F')
    for x in range(5, 12):
        s.set(x, 15, '#6E4A35')


ICONS = {'axe': I_axe, 'pickaxe': I_pickaxe, 'lantern': I_lantern, 'cellar_key': I_cellar_key, 'bird_bell': I_bird_bell,
         'bread': I_bread, 'lamp_oil': I_lamp_oil, 'moon_tea': I_moon_tea, 'smoked_fish': I_smoked_fish,
         'sea_chart': I_sea_chart, 'ship_plans': I_ship_plans, 'ring': I_ring, 'knife': I_knife,
         'tern_plank': I_tern_plank, 'compass': I_compass, 'amber_heart': I_amber_heart, 'moonstone': I_moonstone,
         'lucky_hook': I_lucky_hook, 'sea_glass': I_sea_glass, 'carving': I_carving}


def build_icons():
    out = os.path.join(ART, 'hud')
    for k, fn in ICONS.items():
        PB.save_rgba(icon(fn), os.path.join(out, f'icon_{k}.png'))
    s = Spr(9, 9)                                                       # coin counter
    s.shape(ell(4, 4, 3.6, 3.6), shade3(4, 4, 3.6, 3.6, '#F2E3B3', '#E0A256', '#A8693F'))
    s.set(4, 3, '#A8693F'); s.set(4, 4, '#A8693F'); s.set(4, 5, '#A8693F')
    PB.save_rgba(s.rgba(), os.path.join(out, 'hud_coin.png'))


# ====================================================================== font, dialog UI, emotes, sparkle
EXTRA_GLYPHS = {
    '"': ['#.#', '#.#', '...', '...', '...', '...', '...'], '(': ['.#', '#.', '#.', '#.', '#.', '#.', '.#'],
    ')': ['#.', '.#', '.#', '.#', '.#', '.#', '#.'], ';': ['.', '#', '.', '.', '.', '#', '#'],
    '=': ['....', '....', '####', '....', '####', '....', '....'], '>': ['#...', '.#..', '..#.', '...#', '..#.', '.#..', '#...'],
    '<': ['...#', '..#.', '.#..', '#...', '.#..', '..#.', '...#'], '%': ['##..#', '##.#.', '..#..', '.#...', '#..##', '...##', '.....'],
    '*': ['.....', '#.#.#', '.###.', '#####', '.###.', '#.#.#', '.....'], '&': ['.##..', '#..#.', '.##..', '#.#.#', '#..#.', '.##.#', '.....'],
    '_': ['....', '....', '....', '....', '....', '....', '####'],
}


def build_font():
    glyphs = dict(PB.FONT)
    glyphs.update(EXTRA_GLYPHS)
    order = sorted(glyphs)
    w = sum(len(glyphs[c][0]) + 1 for c in order)
    a = np.zeros((8, w, 4), np.uint8)
    meta, x = {}, 0
    for ch in order:
        g = glyphs[ch]
        for dy, row in enumerate(g):
            for dx, c in enumerate(row):
                if c == '#':
                    a[dy, x + dx] = (255, 255, 255, 255)
        meta[ch] = [x, len(g[0])]
        x += len(g[0]) + 1
    PB.save_rgba(a, os.path.join(ART, 'hud', 'font.png'))
    with open(os.path.join(PB.GAME, 'data', 'font.json'), 'w') as f:
        json.dump({'height': 7, 'glyphs': meta}, f)
    return set(glyphs)


def build_ui():
    out = os.path.join(ART, 'hud')
    PB.save_rgba(PB.panel(12, 12), os.path.join(out, 'panel9.png'))
    p = PB.panel(12, 12)                                                 # highlighted (selected) variant
    p[1:-1, 1:-1, :3] = PB.GOLD
    p[2:-2, 2:-2, :3] = PB.INK
    PB.save_rgba(p, os.path.join(out, 'panel9_sel.png'))
    ar = np.zeros((7, 4, 4), np.uint8)                                   # menu cursor
    for y in range(7):
        for x in range(4):
            if x <= 3 - abs(y - 3):
                ar[y, x] = (*PB.GOLD, 255)
    PB.save_rgba(ar, os.path.join(out, 'cursor.png'))
    nx = np.zeros((5, 7, 4), np.uint8)                                   # "more text" arrow
    for y in range(4):
        for x in range(7):
            if abs(x - 3) <= 3 - y:
                nx[y, x] = (*PB.CREAM, 255)
    PB.save_rgba(nx, os.path.join(out, 'next.png'))
    emotes = {
        'alert': (['..#..', '..#..', '..#..', '..#..', '.....', '..#..'], '#B8483A'),
        'question': (['.###.', '#...#', '...#.', '..#..', '.....', '..#..'], '#3D3550'),
        'music': (['..###', '..#.#', '..#.#', '###.#', '##.##', '...##'], '#2E5466'),
        'dots': (['.....', '.....', '.....', '#.#.#', '.....', '.....'], '#3D3550'),
        'heart': (['.....', '##.##', '#####', '#####', '.###.', '..#..'], '#B8483A'),
        'sniff': (['#...#', '.#.#.', '..#..', '.....', '#.#.#', '.....'], '#6E4A35'),
    }
    for k, (rows, col) in emotes.items():
        a = np.zeros((12, 11, 4), np.uint8)
        for y in range(10):
            for x in range(11):
                if 0 < x < 10 and 0 < y < 9 or (1 < x < 9 and y in (0, 9)):
                    a[y, x] = (*PB.CREAM, 255)
        for y in range(10):
            for x in range(11):
                if a[y, x, 3] and any(not (0 <= y + dy < 12 and 0 <= x + dx < 11) or not a[y + dy, x + dx, 3]
                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    a[y, x] = (*PB.INK, 255)
        for (x, y) in ((4, 10), (5, 10), (5, 11)):
            a[y, x] = (*PB.INK, 255)
        a[9, 4] = (*PB.CREAM, 255); a[9, 5] = (*PB.CREAM, 255)
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch == '#':
                    a[2 + dy, 3 + dx] = (*C(col), 255)
        PB.save_rgba(a, os.path.join(out, f'emote_{k}.png'))
    # sparkle: emissive (off-palette) so it shows at night too
    frames = [['....#....', '....#....', '.........', '.........', '##.....##', '.........', '.........', '....#....',
               '....#....'],
              ['.........', '....#....', '....#....', '...###...', '.#######.', '...###...', '....#....', '....#....',
               '.........'],
              ['.........', '.........', '.........', '....#....', '...###...', '....#....', '.........', '.........',
               '.........']]
    a = np.zeros((9, 27, 4), np.uint8)
    for i, fr in enumerate(frames):
        for y, row in enumerate(fr):
            for x, ch in enumerate(row):
                if ch == '#':
                    core = abs(x - 4) + abs(y - 4) <= 1
                    a[y, i * 9 + x] = (255, 255, 235, 255) if core else (255, 236, 170, 255)
    PB.save_rgba(a, os.path.join(ART, 'objects', 'sparkle.png'))
    d = np.zeros((8, 14, 4), np.uint8)                                   # a freshly dug hole
    PB.set_palette('summer')
    for y in range(8):
        for x in range(14):
            r = ((x - 6.5) / 6.5) ** 2 + ((y - 4) / 3.5) ** 2
            if r <= 1:
                c = G['P']['trunk_dk'] if r < 0.45 else (G['P']['trunk'] if y > 3 else G['P']['path_dk'])
                d[y, x] = (*c, 255)
    d[..., :3] = PB.quantize(d[..., :3])
    PB.save_rgba(d, os.path.join(ART, 'objects', 'dig_hole.png'))


# ====================================================================== in-game world map (M)
def build_worldmap():
    import gen_world_map as WM
    g, put = WM.terrain(rivers=False)
    for p in WM.GULLROCK + WM.SEA_ARCH + WM.SPIRES:
        put(*p, '^')
    for y, (a, b) in WM.EMBERKEY.items():
        for x in range(a, b + 1):
            put(x, y, '^' if (x, y) in WM.EMBER_PEAK else ':')
    for y, (a, b) in WM.VELLMARCH_ISLE.items():
        for x in range(a, b + 1):
            put(x, y, ',')
    for p in WM.VELLMARCH_CLIFFS:
        put(*p, '^')
    W_, H_ = 288, 144
    col = {'~': '#2E5466', '^': '#8A8496', 'T': '#2F4A35', ',': '#4F7A3C', ':': '#A8693F', '=': '#4E8C95',
           '"': '#8DB054', '*': '#9CD0C9'}
    img = np.zeros((H_, W_, 3), np.uint8)
    for y in range(H_):
        for x in range(W_):
            cx, cy = x * WM.W / W_, y * WM.H / H_
            ch = g[min(WM.H - 1, int(cy))][min(WM.W - 1, int(cx))]
            c = C(col.get(ch, '#4F7A3C'))
            if ch == '~' and (x * 3 + y * 5) % 23 == 0:
                c = C('#4E8C95')
            if ch == 'T' and (x + y) % 3 == 0:
                c = C('#4F7A3C')
            if ch == '^' and (x + 2 * y) % 5 == 0:
                c = C('#3D3550')
            img[y, x] = c
    from PIL import ImageDraw                                           # rivers: thin lines through their cells
    pim = Image.fromarray(img)
    dr = ImageDraw.Draw(pim)
    for name, cells in WM.RIVERS.items():
        a, b = WM.RIVER_ENDS[name]
        pts = [((c[0] + 0.5) * W_ / WM.W, (c[1] + 0.5) * H_ / WM.H) for c in [a] + cells + [b]]
        dr.line(pts, fill=tuple(int(v) for v in C('#4E8C95')), width=2)
    img = np.array(pim)
    land = np.zeros((H_, W_), bool)
    for y in range(H_):
        for x in range(W_):
            land[y, x] = g[min(WM.H - 1, int(y * WM.H / H_))][min(WM.W - 1, int(x * WM.W / W_))] != '~'
    edge = land & ~(np.roll(land, 1, 0) & np.roll(land, -1, 0) & np.roll(land, 1, 1) & np.roll(land, -1, 1))
    img[edge] = C('#F2E3B3')
    for cells in WM.ISLETS:
        x, y = int((cells[0] + 0.5) * W_ / WM.W), int((cells[1] + 0.5) * H_ / WM.H)
        img[y:y + 2, x:x + 2] = C('#F2E3B3')
    a = np.zeros((H_, W_, 4), np.uint8)
    a[..., :3] = img
    a[..., 3] = 255
    labels = {}
    for code, (x, y, name) in WM.TOWNS.items():
        px, py = int((x + 0.5) * W_ / WM.W), int((y + 0.5) * H_ / WM.H)
        a[py - 1:py + 2, px - 1:px + 2, :3] = PB.INK
        a[py, px, :3] = C('#B8483A')
        labels[name.upper()] = [px, py, code in 'LMNO']
    PB.save_rgba(a, os.path.join(ART, 'hud', 'worldmap.png'))
    return labels


def build_all(manifest):
    build_room_objects(manifest)
    build_room_grounds()
    build_npcs()
    build_companions()
    build_erne()
    build_icons()
    build_font()
    build_ui()
    labels = build_worldmap()
    with open(os.path.join(PB.GAME, 'data', 'worldmap.json'), 'w') as f:
        json.dump({'labels': labels}, f)


# ====================================================================== low tide (dawn): the sandbar overlay
def build_lowtide():
    T = PB.MAP.T
    tiles = [(x, y) for y in range(len(T)) for x in range(len(T[0])) if T[y][x] == 'l']
    x0, x1 = min(t[0] for t in tiles) * 16, (max(t[0] for t in tiles) + 1) * 16
    y0, y1 = min(t[1] for t in tiles) * 16 - 4, (max(t[1] for t in tiles) + 1) * 16 + 4
    PB.set_palette('summer')
    a = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    R = np.random.default_rng(12).random(a.shape[:2])
    for yy in range(y1 - y0):
        for xx in range(x1 - x0):
            X, Y = x0 + xx, y0 + yy
            tx, ty = X // 16, Y // 16
            inside = 0 <= ty < len(T) and T[ty][tx] == 'l'
            edge = min(Y - (y0 + 4), (y1 - 4) - 1 - Y)
            wob = int(round(1.5 * np.sin(X / 5.0)))
            if not inside and not (-4 <= edge < 0):
                continue
            if edge + wob < -1:
                if (X + Y) % 2 == 0 and edge + wob >= -3:
                    a[yy, xx, :3] = G['P']['foam']; a[yy, xx, 3] = 255
                continue
            c = G['P']['sand_wet']
            if (Y + int(round(2 * np.sin(X / 6.0)))) % 4 == 0:
                c = G['P']['sand']
            if R[yy, xx] < 0.02:
                c = G['P']['shell'] if 'shell' in G['P'] else G['P']['sand_lt']
            if edge + wob <= 0:
                c = G['P']['sand_dk']
            a[yy, xx, :3] = c
            a[yy, xx, 3] = 255
    a[..., :3] = PB.quantize(a[..., :3])
    PB.save_rgba(a, os.path.join(ART, 'ground', 'lowtide.png'))
    return {'x': int(x0), 'y': int(y0), 'w': int(x1 - x0), 'h': int(y1 - y0)}
