"""Shared helpers for building outdoor region maps (same tile language as proto_map.py).

Tiles: , grass  : path  . sand  w planks  f flowers  T forest  = river (frozen in the north)  " reeds
       ~ sea  ! cold sea (seal)  O open ocean (whale)  ^ rock / cliff  v ledge  R ravine  b reef
       t secret forest path (looks like forest, walkable)
A region writes game/data/maps/<id>.json with: terrain, objects (decor), blocked, edges (links to other maps).
"""
import json
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MAPS = os.path.join(os.path.dirname(HERE), 'game', 'data', 'maps')
HOUSE_BLOCK = [(dx, dy) for dx in range(4) for dy in (-2, -1, 0)]


class Region:
    def __init__(self, rid, w, h, fill=',', seed=1, season_lock=None, scenery='home'):
        self.id, self.W, self.H = rid, w, h
        self.T = [[fill] * w for _ in range(h)]
        self.rng = np.random.default_rng(seed)
        self.objects = []
        self.blocked = set()
        self.edges = []
        self.season_lock = season_lock
        self.scenery = scenery

    # ---- terrain
    def put(self, x, y, c):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.T[y][x] = c

    def get(self, x, y):
        return self.T[y][x] if 0 <= x < self.W and 0 <= y < self.H else '^'

    def rect(self, x0, y0, x1, y1, c, only=None):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if only is None or self.get(x, y) in only:
                    self.put(x, y, c)

    def line(self, pts, r, c, only=None):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
            for t in np.linspace(0, 1, n):
                cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                for y in range(int(cy - r) - 1, int(cy + r) + 2):
                    for x in range(int(cx - r) - 1, int(cx + r) + 2):
                        if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.25 and (only is None or self.get(x, y) in only):
                            self.put(x, y, c)

    def blob(self, cx, cy, rx, ry, c, only=None, wobble=0.18, seed=0):
        rr = np.random.default_rng(seed)
        ph = rr.uniform(0, 6.28, 3)
        for y in range(int(cy - ry) - 2, int(cy + ry) + 3):
            for x in range(int(cx - rx) - 2, int(cx + rx) + 3):
                a = np.arctan2(y - cy, x - cx)
                k = 1 + wobble * (np.sin(3 * a + ph[0]) + 0.5 * np.sin(5 * a + ph[1]))
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= k * k and (only is None or self.get(x, y) in only):
                    self.put(x, y, c)

    # ---- objects
    def obj(self, kind, tx, ty, ox=8, oy=14, block=((0, 0),)):
        self.objects.append({'kind': kind, 'x': tx * 16 + ox, 'y': ty * 16 + oy})
        for (dx, dy) in block:
            self.blocked.add((tx + dx, ty + dy))

    def house(self, kind, tx, ty):
        """4 x 3 tile house; (tx, ty) = bottom-left tile; the door is at (tx + 2, ty)"""
        self.objects.append({'kind': kind, 'x': tx * 16, 'y': ty * 16 + 16})
        for (dx, dy) in HOUSE_BLOCK:
            self.blocked.add((tx + dx, ty + dy))

    def trees(self, kinds=(('pine', 0.5), ('oak', 0.35), ('oak_red', 0.15)), density=1.0, char='T'):
        """trees drawn on forest tiles (like the home coast)"""
        names = [k for k, _ in kinds]
        p = np.array([w for _, w in kinds], float)
        p /= p.sum()
        for ty in range(self.H):
            for tx in range(self.W):
                if self.T[ty][tx] == char and ((tx + ty * 2) % 3 == 0 or self.rng.random() < 0.18 * density):
                    k = names[int(self.rng.choice(len(names), p=p))]
                    self.objects.append({'kind': k, 'x': tx * 16 + 8 + int(self.rng.integers(-4, 5)),
                                         'y': ty * 16 + 12 + int(self.rng.integers(-3, 4))})

    def secret_trees(self):
        """the secret path ('t'): trees stand beside it, slightly offset, so a gap shows if you look closely"""
        for ty in range(self.H):
            for tx in range(self.W):
                if self.T[ty][tx] == 't' and (tx + ty) % 2 == 0:
                    self.objects.append({'kind': 'pine', 'x': tx * 16 + (1 if tx % 4 == 0 else 15), 'y': ty * 16 + 4})

    def edge(self, side, a, b, to, shift=0):
        """stepping off this side between a..b (inclusive) enters map `to`; the other coordinate maps 1:1 + shift"""
        self.edges.append({'side': side, 'a': a, 'b': b, 'to': to, 'shift': shift})

    # ---- output
    def data(self):
        d = {'id': self.id, 'kind': 'outdoor', 'width': self.W, 'height': self.H,
             'terrain': [''.join(r) for r in self.T], 'objects': self.objects,
             'blocked': sorted([list(b) for b in self.blocked]), 'edges': self.edges, 'scenery': self.scenery}
        if self.season_lock is not None:
            d['season_lock'] = self.season_lock
        return d

    def write(self):
        os.makedirs(MAPS, exist_ok=True)
        with open(os.path.join(MAPS, f'{self.id}.json'), 'w') as f:
            json.dump(self.data(), f)

    def ascii(self, marks=None):
        rows = [r[:] for r in self.T]
        for (x, y) in self.blocked:
            if 0 <= x < self.W and 0 <= y < self.H and rows[y][x] in ',:.f':
                rows[y][x] = '#'
        for (x, y), ch in (marks or {}).items():
            rows[y][x] = ch
        head = '    ' + ''.join(str(x % 10) for x in range(self.W))
        return head + '\n' + '\n'.join('%3d %s' % (y, ''.join(r)) for y, r in enumerate(rows))
