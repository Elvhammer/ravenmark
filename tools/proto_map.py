"""Keelvik prototype map: tile grid, objects, chests, signs and area zones.

    python3 proto_map.py            # writes game/data/world.json and prints an ASCII preview

Tiles (16 px):
  ,  grass          :  path            .  sand / beach     w  wooden planks (bridge, piers)
  f  flower meadow  T  forest (blocked; trees drawn as objects)
  =  river (fresh water: surf with the otter, walk on it in winter)
  "  reeds (blocked, walkable in winter)
  ~  sea            !  cold sea (Rimestream: seal only)
  ^  cliff face / rock (blocked)        v  ledge (hop down: south only)
  R  ravine (blocked; cross with the Bird Bell)
  b  reef / breakers (blocked, even for the otter)
  l  low-tide sandbar (sea, too shallow and rocky to swim; walkable at dawn)
"""
import json
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'game', 'data', 'world.json')
W, H = 96, 64
rng = np.random.default_rng(42)
T = [[','] * W for _ in range(H)]


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        T[y][x] = c


def get(x, y):
    return T[y][x] if 0 <= x < W and 0 <= y < H else '^'


def line(pts, r, c, only=None):
    """thick polyline of tiles"""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for t in np.linspace(0, 1, n):
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for y in range(int(cy - r) - 1, int(cy + r) + 2):
                for x in range(int(cx - r) - 1, int(cx + r) + 2):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.25 and (only is None or get(x, y) in only):
                        put(x, y, c)


def rect(x0, y0, x1, y1, c, only=None):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if only is None or get(x, y) in only:
                put(x, y, c)


def coast(y):
    c = 75 + 2.2 * np.sin(y / 4.3)
    if 10 <= y <= 26:
        c -= 7 * np.sin(np.pi * (y - 10) / 16)          # Keelvik harbour bay
    if 44 <= y <= 62:
        c += 9 * np.sin(np.pi * (y - 44) / 18)          # Sule Ness headland
    return int(round(c))


# ---- sea, cold water, beaches
for y in range(H):
    cx = coast(y)
    for x in range(cx, W):
        put(x, y, '~')
for y in range(0, 13):
    for x in range(W):
        if get(x, y) == '~' and x + y * 0.8 >= 84:
            put(x, y, '!')                               # Rimestream: the cold current in the north-east
for y in range(28, 44):
    cx = coast(y)
    rect(cx - 3, y, cx - 1, y, '.')                      # beach cove south of Keelvik
for y in range(2, 10):
    cx = coast(y)
    rect(cx - 2, y, cx - 1, y, '.')                      # pebble beach north of the harbour

# ---- forests (route edges)
rect(0, 0, 45, 11, 'T')                                  # north of the river, Lauvdal
rect(0, 26, 49, H - 1, 'T')                              # south-west woods
rect(46, 0, 58, 4, 'T')                                  # behind Keelvik
for y in range(26, H):                                   # soften the south-west forest edge
    edge = 49 + int(round(2 * np.sin(y / 3.0)))
    for x in range(edge - 3, edge + 1):
        if rng.random() < 0.5:
            put(x, y, ',')

# ---- the Lauva river, its reeds and Damholm (winter-only islet)
river = [(-1, 13), (8, 14), (18, 12.5), (28, 13.5), (38, 15), (47, 15), (56, 16.5), (64, 17), (70, 17)]
line(river, 1.3, '=')
rect(25, 11, 33, 15, '"', only='=,T')                    # reed beds all around Damholm
for (x, y) in ((29, 12), (28, 13), (29, 13), (30, 13), (29, 14), (28, 14), (30, 14)):   # Damholm (winter-only islet)
    put(x, y, ',')
rect(23, 16, 35, 16, '=')                                # open channel south of the reeds, so the river stays connected
rect(23, 15, 24, 15, '=')
rect(34, 15, 35, 15, '=')

# ---- Lauvdal route: corridor + path along the south bank
rect(0, 15, 45, 25, ',', only='T,')
for x in range(0, 46):                                   # wavy forest edges
    top = 11 + int(round(1.5 * np.sin(x / 3.1)))
    bot = 24 + int(round(2 * np.sin(x / 4.3 + 1)))
    for y in range(bot, 27):
        if get(x, y) == ',':
            put(x, y, 'T')
line([(-1, 19), (10, 19), (18, 18), (28, 19.5), (38, 20), (46, 20), (52, 21.5)], 0.7, ':', only=',f')
for (x, y) in [(5, 22), (13, 23), (20, 21), (35, 23), (41, 22)]:
    rect(x - 1, y, x + 1, y + 1, 'f', only=',')
line([(16, 19), (16, 9)], 0.6, ':', only=',T=')           # side path north over a bridge to a hidden nook
rect(13, 6, 19, 9, ',', only='T')
rect(15, 12, 16, 15, 'w', only='=:')                    # little bridge
rect(15, 11, 16, 11, ':', only='T,')

# ---- Keelvik
rect(46, 5, 71, 30, ',', only='T,f')
for y in range(5, 31):
    for x in range(46, 72):
        if T[y][x] == '~' and x < coast(y):
            put(x, y, ',')
line(river[5:], 1.3, '=')
line([(46, 20), (52, 21.5), (60, 22), (66, 22)], 0.7, ':', only=',f')     # main street
line([(56, 21), (56, 8)], 0.8, ':', only=',=')                             # north street
rect(55, 15, 57, 18, 'w', only='=:')                                       # town bridge
line([(52, 8), (63, 8)], 0.7, ':', only=',')
rect(57, 23, 61, 26, ':')                                                  # little square
for (y, x0, x1) in [(20, coast(20) - 1, coast(20) + 5), (27, coast(27) - 1, coast(27) + 4)]:
    rect(x0, y, x1, y, 'w')                                                # piers into the harbour
line([(66, 22), (coast(20) - 1, 20)], 0.6, ':', only=',.')
line([(66, 22), (coast(27) - 2, 27)], 0.6, ':', only=',.')

# ---- Sule Ness: meadow, two ledges, headland cliffs
line([(59, 26), (58, 32), (60, 38), (64, 44), (70, 50), (77, 53)], 0.8, ':', only=',f.T')
rect(50, 31, 70, 62, ',', only='T,')
for (x, y) in [(53, 40), (55, 49), (61, 56), (66, 41), (52, 55)]:
    rect(x - 1, y, x + 2, y + 1, 'f', only=',')
for x in range(50, 66):                                  # ledge 1, with a ramp gap at x 66..
    if get(x, 34) in ',:f':
        put(x, 34, 'v')
for x in range(54, 70):                                  # ledge 2
    if get(x, 45) in ',:f':
        put(x, 45, 'v')
for x in range(66, 70):
    put(x, 34, ':')
for x in range(70, 73):
    if get(x, 45) not in '~.':
        put(x, 45, ':')
for y in range(44, H):                                   # cliffs along the headland's sea edge
    cx = coast(y)
    for x in (cx - 1, cx - 2):
        if y >= 46 and get(x, y) != '~':
            put(x, y, '^')
for x in range(60, W):
    for y in (H - 2, H - 1):
        if get(x, y) != '~':
            put(x, y, '^')
# offshore islet (reachable by otter)
for y in range(37, 42):
    for x in range(86, 92):
        if (x - 88.5) ** 2 / 9 + (y - 39) ** 2 / 4 <= 1:
            put(x, y, ',' if (x - 88.5) ** 2 / 9 + (y - 39) ** 2 / 4 < 0.45 else '.')

# ---------------------------------------------------------------- increment 1 places
# Moonlit Grove: a clearing in the south-west forest; path from Lauvdal (a fallen young tree blocks it: axe)
for y in range(28, 40):
    for x in range(15, 34):
        if ((x - 24) / 7.0) ** 2 + ((y - 34) / 4.6) ** 2 <= 1:
            put(x, y, ',')
for y in range(24, 31):
    put(22, y, ':')
rect(26, 33, 27, 34, '=')                                # moon pond
rect(27, 29, 29, 30, '^')                                # rock outcrop with the cave's north mouth
put(28, 30, ',')                                         # door into the cave (step up)
# Mossholt (FD1, forest caretaker): hidden clearing far south-west, trail from the grove behind a thicket
for y in range(40, 58):
    for x in range(1, 18):
        if ((x - 9) / 7.5) ** 2 + ((y - 48) / 7.0) ** 2 <= 1:
            put(x, y, ',')
line([(17, 34), (14, 37), (11, 41), (9, 44)], 0.5, ',', only='T')
put(10, 41, ',')
put(10, 42, ',')
# Sule Ness: rock outcrop with the cave's south mouth on the forest edge (cracked rock in front: pickaxe)
rect(44, 50, 47, 54, '^')
for x in (47, 48, 49):
    put(x, 52, ',')
# Lauvdal north: a plateau beyond a ravine (Bird Bell); the walking-stick nook is the south rim
rect(10, 0, 24, 2, ',')
rect(10, 3, 24, 5, 'R')
# Owl's Hollow (owl-only): a clearing north of the river, behind a hedge at the forest edge
rect(36, 7, 41, 9, ',')
rect(38, 10, 38, 11, ',')
# Owl glade (owl-only): a small glade off the Sule Ness meadow, behind a hedge
rect(42, 39, 46, 41, ',')
put(47, 40, ',')
put(48, 40, ',')
# Low tide: a sandbar at dawn out to a reef-ringed islet below Sule Ness
for x in (77, 78, 79):
    put(x, 35, 'l')
for y in range(33, 38):
    for x in range(79, 84):
        if get(x, y) in '~' and not (x == 79 and y == 35):
            put(x, y, 'b')
for (x, y) in ((80, 34), (81, 34), (82, 34), (80, 35), (82, 35), (80, 36), (81, 36), (82, 36)):
    put(x, y, '.')
put(81, 35, ',')
# Fyrholm (FD1, lighthouse keeper): an island east of Sule Ness, ringed by reefs (only Ole's boat gets through)
for y in range(44, 62):
    for x in range(82, 96):
        d = ((x - 89) / 4.6) ** 2 + ((y - 53) / 5.6) ** 2
        if d <= 1:
            put(x, y, ',' if d < 0.62 else '.')
        elif d <= 1.55 and get(x, y) == '~':
            put(x, y, 'b')

# ---------------------------------------------------------------- Part 2: the wider world
# the open ocean begins at the far east edge (deep water: only the whale goes further)
for y in range(14, 43):
    for x in range(93, W):
        if get(x, y) == '~':
            put(x, y, 'O')
# a secret path into the Lauvdal woods (looks like forest; the Running Shoes wait in a hidden clearing)
for (x, y) in [(37, 24), (37, 25), (37, 26), (37, 27), (38, 27), (38, 28), (38, 29), (38, 30), (37, 30), (36, 30),
               (36, 31), (36, 32), (36, 33)]:
    put(x, y, 't')
for (x, y) in [(35, 34), (36, 34), (37, 34), (35, 35), (36, 35), (37, 35)]:
    put(x, y, ',')

# ---------------------------------------------------------------- objects
objects = []        # {kind, x, y} in pixels (x, y = feet / base point)
blocked = set()


def obj(kind, tx, ty, ox=8, oy=14, block=((0, 0),)):
    objects.append({'kind': kind, 'x': tx * 16 + ox, 'y': ty * 16 + oy})
    for (dx, dy) in block:
        blocked.add((tx + dx, ty + dy))


HOUSE_BLOCK = [(dx, dy) for dx in range(4) for dy in (-2, -1, 0)]
for (tx, ty, var) in [(47, 9, 'house_a'), (60, 9, 'house_b'), (64, 13, 'house_a'), (47, 25, 'house_b'), (52, 29, 'house_a')]:
    objects.append({'kind': var, 'x': tx * 16, 'y': ty * 16 + 16})
    for (dx, dy) in HOUSE_BLOCK:
        blocked.add((tx + dx, ty + dy))
objects.append({'kind': 'ship', 'x': 62 * 16, 'y': 30 * 16})                  # half-built ship in the dry dock
for dx in range(0, 6):
    for dy in (-2, -1, 0, 1):
        blocked.add((62 + dx, 28 + dy))
obj('lighthouse', 79, 52, block=[(0, 0), (1, 0), (0, -1), (1, -1)])

# trees: dense in forest tiles, a few on the grass
for ty in range(H):
    for tx in range(W):
        if T[ty][tx] == 'T' and (tx + ty * 2) % 3 == 0 or (T[ty][tx] == 'T' and rng.random() < 0.18):
            kind = 'pine' if rng.random() < (0.55 if ty < 12 else 0.3) else 'oak'
            if kind == 'oak' and rng.random() < 0.35:
                kind = 'oak_red'
            objects.append({'kind': kind, 'x': tx * 16 + 8 + int(rng.integers(-4, 5)), 'y': ty * 16 + 12 + int(rng.integers(-3, 4))})
for (tx, ty, k) in [(4, 23, 'oak'), (24, 22, 'oak_red'), (33, 17, 'pine'), (43, 23, 'oak'), (50, 12, 'oak'), (69, 8, 'pine'),
                    (54, 37, 'oak'), (63, 52, 'oak_red'), (57, 58, 'pine'), (68, 40, 'oak'), (49, 18, 'oak_red')]:
    if T[ty][tx] in ',f':
        obj(k, tx, ty, oy=12)
for (tx, ty) in [(9, 22), (30, 22), (38, 24), (51, 36), (60, 48), (66, 57), (58, 41), (14, 8), (88, 38)]:
    if T[ty][tx] in ',f.':
        obj('bush', tx, ty)
for (tx, ty, k) in [(70, 31, 'rock'), (71, 37, 'rock_big'), (52, 44, 'rock'), (73, 55, 'rock_big'), (64, 60, 'rock'),
                    (90, 40, 'rock'), (45, 23, 'rock'), (22, 24, 'rock'), (69, 4, 'rock')]:
    if T[ty][tx] in ',f.':
        obj(k, tx, ty)
# Keelvik props
for (k, tx, ty) in [('barrel', 51, 10), ('barrel', 52, 10), ('crate', 64, 10), ('crate', 64, 9), ('logs', 61, 21),
                    ('barrel', 68, 14), ('lamp', 55, 20), ('lamp', 58, 14), ('lamp', 62, 23), ('crate', 60, 27),
                    ('rack', 66, 19), ('rack', 69, 25), ('barrel', 51, 26), ('logs', 50, 13)]:
    if T[ty][tx] in ',:f.':
        obj(k, tx, ty)
for (tx, ty) in [(74, 24), (77, 21)]:
    obj('boat', tx, ty, oy=8)
for x in range(50, 55):                                   # fence along the top of ledge 1 (with a gap)
    obj('fence', x, 33, oy=15)
# increment 1 decor (interactive things - chests, signs, NPCs, obstacles - live in content.json)
for (tx, ty) in [(20, 33), (22, 31), (25, 31), (21, 37), (27, 37), (88, 56), (91, 55), (86, 55)]:
    obj('standing_stone', tx, ty)                                       # Moonlit Grove ring, Fyrholm stones
for (tx, ty) in [(43, 39), (45, 41), (42, 41)]:
    obj('standing_stone', tx, ty)                                       # owl glade fairy ring
obj('cave_mouth', 46, 52, ox=8, oy=11, block=[])                         # Sule Ness mouth (door at 47,52)
obj('cave_mouth_n', 28, 30, ox=8, oy=11, block=[])                       # grove mouth (door at 28,30)
obj('ruin', 12, 1, block=[(0, 0), (1, 0), (0, -1), (1, -1)])             # old watch on the plateau
obj('pen', 36, 22, block=[(-1, 0), (0, 0), (1, 0), (-1, -1), (0, -1), (1, -1)])   # Hedda's animal pen
obj('logs', 5, 22)
for (tx, ty, var) in [(3, 46, 'cabin'), (12, 48, 'cabin')]:              # Mossholt cabins
    objects.append({'kind': var, 'x': tx * 16, 'y': ty * 16 + 16})
    for (dx, dy) in HOUSE_BLOCK:
        blocked.add((tx + dx, ty + dy))
obj('linden', 9, 52, block=[(0, 0), (1, 0), (-1, 0)])                    # the Old Linden
for (tx, ty) in [(87, 49), (89, 48), (91, 49), (92, 51)]:
    obj('puffin', tx, ty, block=[])
obj('boat', 84, 53, oy=8)                                                # Ole's boat moored at Fyrholm
obj('beacon', 89, 50)                                                    # Fyrholm's old beacon
signs = []
chests = []

zones = [{'name': 'lauvdal', 'x0': 0, 'y0': 0, 'x1': 45, 'y1': 30},
         {'name': 'keelvik', 'x0': 46, 'y0': 0, 'x1': 73, 'y1': 30},
         {'name': 'sulenes', 'x0': 0, 'y0': 31, 'x1': 95, 'y1': 63}]

edges = [{'side': 'top', 'a': 10, 'b': 24, 'to': 'north', 'shift': 0},          # Erne Cliff -> the snowy north
         {'side': 'top', 'a': 76, 'b': 95, 'to': 'north', 'shift': 0},          # the Rimestream -> the fjord
         {'side': 'bottom', 'a': 77, 'b': 95, 'to': 'south', 'shift': -40},     # the sea south -> Copperhavn
         {'side': 'right', 'a': 14, 'b': 42, 'to': 'ocean', 'shift': -9}]       # the open ocean (whale)
data = {'width': W, 'height': H, 'tile': 16, 'terrain': [''.join(r) for r in T], 'edges': edges, 'kind': 'outdoor',
        'scenery': 'home',
        'objects': objects, 'blocked': sorted([list(b) for b in blocked]),
        'chests': chests, 'signs': signs, 'zones': zones, 'start': [55, 22]}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w') as f:
    json.dump(data, f)

if __name__ == '__main__':
    view = [r[:] for r in T]
    for (x, y) in blocked:
        if view[y][x] in ',f:.':
            view[y][x] = '#'
    for c in chests:
        view[c['y']][c['x']] = 'C'
    view[22][55] = '@'
    print('\n'.join(''.join(r) for r in view))
    print(len(objects), 'objects,', len(blocked), 'blocked tiles')
