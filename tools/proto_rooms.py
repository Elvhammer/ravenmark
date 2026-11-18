"""Interior rooms and the cave as small maps: game/data/maps/<id>.json

Room tiles:  W wall   . floor   D exit door (step down onto it)   S cellar door / U stairs up (step up into it)
Cave tiles:  W rock   . floor   = underground pool   A / B exits (step onto them)
Objects are decor (furniture); interactive things (NPCs, chests, pickups) live in content.json.
"""
import json
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'game', 'data', 'maps')

ROOMS = {
    'inn': {
        'rows': ['WWWWWWWWWWWWWW',
                 'WWWWWWWWWWWSWW',
                 'W............W',
                 'W............W',
                 'W............W',
                 'W............W',
                 'W............W',
                 'W............W',
                 'WWWWWWDWWWWWWW'],
        'decor': [('counter4', 1, 3), ('shelf3', 1, 1), ('fireplace', 6, 1), ('table', 8, 4), ('table', 8, 6),
                  ('stool', 7, 4), ('stool', 10, 6), ('barrel', 12, 6), ('barrel', 12, 7), ('window', 3, 1),
                  ('window', 9, 1), ('rug', 5, 5)],
        'wall': 'wood', 'floor': 'plank',
    },
    'cellar': {
        'rows': ['WWWWWWWWWW',
                 'WWWWWWWWUW',
                 'W........W',
                 'W........W',
                 'W........W',
                 'W........W',
                 'WWWWWWWWWW'],
        'decor': [('barrel', 1, 2), ('barrel', 2, 2), ('crate', 1, 5), ('crate', 2, 5), ('shelf3', 2, 1),
                  ('sacks', 7, 5), ('crate', 4, 4)],
        'wall': 'stone', 'floor': 'stone',
    },
    'store': {
        'rows': ['WWWWWWWWWWWW',
                 'WWWWWWWWWWWW',
                 'W..........W',
                 'W..........W',
                 'W..........W',
                 'W..........W',
                 'W..........W',
                 'WWWWWDWWWWWW'],
        'decor': [('counter4', 3, 3), ('shelf3', 1, 1), ('shelf3', 7, 1), ('window', 5, 1), ('barrel', 10, 5),
                  ('barrel', 10, 6), ('sacks', 1, 6), ('crate', 1, 5)],
        'wall': 'wood', 'floor': 'plank',
    },
    'workshop': {
        'rows': ['WWWWWWWWWWWW',
                 'WWWWWWWWWWWW',
                 'W..........W',
                 'W..........W',
                 'W..........W',
                 'W..........W',
                 'W..........W',
                 'WWWWWDWWWWWW'],
        'decor': [('bench3', 2, 3), ('boatmodel', 8, 3), ('planks', 10, 5), ('nets', 2, 1), ('window', 6, 1),
                  ('window', 9, 1), ('crate', 1, 6), ('barrel', 10, 2)],
        'wall': 'wood', 'floor': 'plank',
    },
    'fisher': {
        'rows': ['WWWWWWWWWW',
                 'WWWWWWWWWW',
                 'W........W',
                 'W........W',
                 'W........W',
                 'W........W',
                 'WWWWDWWWWW'],
        'decor': [('bed', 1, 3), ('stove', 7, 1), ('nets', 2, 1), ('table', 5, 3), ('window', 5, 1), ('barrel', 8, 5)],
        'wall': 'wood', 'floor': 'plank',
    },
    'museum': {
        'rows': ['WWWWWWWWWWWWWWWW',
                 'WWWWWWWWWWWWWWWW',
                 'W..............W',
                 'W..............W',
                 'W..............W',
                 'W..............W',
                 'W..............W',
                 'W..............W',
                 'W..............W',
                 'WWWWWWWDWWWWWWWW'],
        'decor': [('pedestal', 2, 3), ('pedestal', 4, 3), ('pedestal', 6, 3), ('pedestal', 9, 3), ('pedestal', 11, 3),
                  ('pedestal', 13, 3), ('pedestal', 2, 6), ('pedestal', 4, 6), ('pedestal', 11, 6), ('pedestal', 13, 6),
                  ('counter4', 6, 6), ('painting', 3, 1), ('painting', 12, 1), ('window', 7, 1), ('window', 8, 1),
                  ('rug', 6, 7)],
        'wall': 'wood', 'floor': 'stone',
    },
}

FOOT = {'counter4': [(0, 0), (1, 0), (2, 0), (3, 0)], 'table': [(0, 0), (1, 0)], 'bench3': [(0, 0), (1, 0), (2, 0)],
        'boatmodel': [(0, 0), (1, 0)], 'bed': [(0, 0), (0, -1)], 'barrel': [(0, 0)], 'crate': [(0, 0)], 'sacks': [(0, 0)],
        'planks': [(0, 0)], 'stool': [], 'shelf3': [], 'fireplace': [], 'window': [], 'nets': [], 'stove': [], 'rug': [],
        'crystal': [(0, 0)], 'boulder': [(0, 0)], 'pedestal': [(0, 0)], 'painting': []}


def room_json(rid, room):
    rows = room['rows']
    blocked = set()
    objs = []
    for (k, tx, ty) in room['decor']:
        objs.append({'kind': k, 'x': tx * 16 + 8, 'y': ty * 16 + 14})
        for (dx, dy) in FOOT[k]:
            blocked.add((tx + dx, ty + dy))
    return {'id': rid, 'kind': 'room', 'width': len(rows[0]), 'height': len(rows), 'terrain': rows,
            'objects': objs, 'blocked': sorted([list(b) for b in blocked]), 'wall': room['wall'], 'floor': room['floor']}


def cave_json():
    W, H = 40, 24
    g = [['W'] * W for _ in range(H)]

    def carve(x0, y0, x1, y1, c='.'):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                g[y][x] = c
    carve(32, 9, 37, 14)                    # east chamber (Sule Ness mouth)
    carve(21, 11, 31, 12)                   # long tunnel
    carve(13, 8, 22, 16)                    # pool hall
    carve(15, 11, 19, 13, '=')              # the pool
    carve(23, 4, 24, 10)                    # climb north
    carve(17, 1, 29, 5)                     # treasure chamber
    carve(6, 11, 12, 12)                    # west tunnel
    carve(6, 4, 7, 10)                      # north passage
    carve(2, 1, 9, 4)                       # north-west chamber (grove mouth)
    rng = np.random.default_rng(3)          # ragged walls
    for _ in range(40):
        x, y = int(rng.integers(1, W - 1)), int(rng.integers(1, H - 1))
        if g[y][x] == '.' and sum(g[y + dy][x + dx] == 'W' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 2:
            g[y][x] = 'W'
    for (x, y) in ((24, 7), (23, 7), (24, 8), (23, 8), (7, 7), (6, 7), (7, 8), (6, 8), (26, 11), (26, 12)):
        g[y][x] = '.'                       # keep the narrow passages open
    g[12][38] = 'A'                         # back to Sule Ness (step right)
    g[0][5] = 'B'                           # up to the Moonlit Grove (step up)
    rows = [''.join(r) for r in g]
    decor = [('crystal', 18, 2), ('crystal', 28, 3), ('crystal', 14, 9), ('crystal', 21, 15), ('boulder', 30, 10),
             ('boulder', 3, 3), ('crystal', 8, 2)]
    objs, blocked = [], set()
    for (k, tx, ty) in decor:
        objs.append({'kind': k, 'x': tx * 16 + 8, 'y': ty * 16 + 14})
        for (dx, dy) in FOOT[k]:
            blocked.add((tx + dx, ty + dy))
    return {'id': 'cave', 'kind': 'cave', 'width': W, 'height': H, 'terrain': rows, 'objects': objs,
            'blocked': sorted([list(b) for b in blocked]), 'dark': True,
            'lit_zones': [[37, 12, 3], [5, 1, 3]]}      # without a lantern you can only go this far from each mouth


def build():
    os.makedirs(OUT, exist_ok=True)
    maps = {rid: room_json(rid, r) for rid, r in ROOMS.items()}
    maps['cave'] = cave_json()
    for mid, m in maps.items():
        with open(os.path.join(OUT, f'{mid}.json'), 'w') as f:
            json.dump(m, f)
    return maps


if __name__ == '__main__':
    for mid, m in build().items():
        print(mid, m['width'], 'x', m['height'])
        if mid == 'cave':
            print('\n'.join(m['terrain']))
