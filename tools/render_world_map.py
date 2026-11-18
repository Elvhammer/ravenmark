"""Renders the Ravenmark world map as a pixel-art PNG (summer palette).

Base image: 1 px = 1 tile (800 x 400), upscaled 2x nearest-neighbour,
then labels are drawn with anti-aliasing off. Usage:
    python3 render_world_map.py [out.png]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import gen_world_map as M

CW, CH = 8, 16                      # base px per map cell
BW, BH = M.W * CW, M.H * CH         # 800 x 400
S = 2                               # upscale factor
rng = np.random.default_rng(11)


def hx(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.uint8)


P = {k: hx(v) for k, v in {
    'deep': '#3A5759', 'mid': '#45686A', 'shallow': '#5A8580', 'foam': '#DCD2B6', 'wave': '#628C86',
    'lake': '#5F887C', 'lake_edge': '#78A091', 'lake_hi': '#9CBFAE', 'reed': '#A3A15C', 'reed_dk': '#7D7E46',
    'grass': '#97A55A', 'grass_dk': '#83924C', 'grass_lt': '#AAB66A', 'flower': '#E8C9A0',
    'dry': '#C8A86C', 'dry_dk': '#B08E58', 'dry_lt': '#D9C08A', 'shrub': '#8C8A4A',
    'sand': '#DCC594', 'sand_dk': '#C8AE7C',
    'floor': '#55703C', 'pine_hi': '#7E9A4C', 'pine': '#557440', 'pine_dk': '#3F5833',
    'oak_hi': '#A1AE57', 'oak': '#768C45', 'oak_dk': '#566B37', 'tshadow': '#33402C',
    'rock': '#A8957A', 'rock_lt': '#CBB795', 'rock_dk': '#7A6852', 'snow': '#ECE6D8', 'snow_sh': '#C3BDCD',
    'canyon': '#B0603F', 'canyon_dk': '#8E4A33', 'canyon_lt': '#C97E55',
    'grey': '#8E8678', 'grey_dk': '#6E675C', 'ash': '#6A5E58', 'ash_lt': '#7C706A', 'volc': '#4E4240',
    'path': '#ECDDB0', 'path_sh': '#5E4E3C', 'ice': '#E3F2F3', 'ice_dk': '#86AEB6',
    'roof': '#B5523B', 'thatch': '#CFA650', 'slate': '#5E6372', 'copper': '#6F9C86', 'wood': '#8A5A3B',
    'wall': '#EADFC8', 'wall_dk': '#BFB197', 'ink': '#2F2A3A', 'gold': '#E2B84E', 'glow': '#E07A3A',
    'stone': '#D9D0BC',
}.items()}

# ---------------------------------------------------------------- cell grid
cells, _ = M.terrain(rivers=False)
cells[11][24] = '"'; cells[3][12] = '='; cells[8][8] = '^'
for (x, y) in M.GULLROCK + M.SEA_ARCH:
    cells[y][x] = 'g'
for y, (a, b) in M.EMBERKEY.items():
    for x in range(a, b + 1):
        cells[y][x] = 'v' if (x, y) in M.EMBER_PEAK else 'a'
for y, (a, b) in M.VELLMARCH_ISLE.items():
    for x in range(a, b + 1):
        cells[y][x] = ','
for (x, y) in M.VELLMARCH_CLIFFS:
    cells[y][x] = 'g'
for (x, y) in M.GANNET_CLIFFS:
    if M.is_land(x, y):
        cells[y][x] = 'g'
for y in range(M.H):
    for x in range(M.W):
        if cells[y][x] == '^' and y >= 14 and x <= 12:
            cells[y][x] = 'c'                      # red canyon rock

# soften straight biome borders: randomly trade cells along forest / dry edges
er = np.random.default_rng(5)
src = [row[:] for row in cells]
for y in range(M.H):
    for x in range(M.W):
        c = src[y][x]
        nb = [src[yy][xx] for (xx, yy) in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
              if 0 <= xx < M.W and 0 <= yy < M.H]
        if c == 'T' and ',' in nb and er.random() < 0.35:
            cells[y][x] = ','
        elif c == ',' and 'T' in nb and er.random() < 0.30:
            cells[y][x] = 'T'
        elif c == ':' and ',' in nb and er.random() < 0.30:
            cells[y][x] = ','
        elif c == ',' and ':' in nb and er.random() < 0.25:
            cells[y][x] = ':'
for (x, y) in [(91, 6), (92, 6), (93, 6), (90, 7), (91, 7), (92, 7), (95, 7), (96, 7), (89, 8), (90, 8),
               (89, 13), (90, 13), (91, 13), (90, 14), (91, 14), (92, 14), (96, 14), (97, 14), (96, 15)]:
    cells[y][x] = 'T'

ID = {'~': 0, '=': 1, '"': 2, '^': 3, 'c': 4, 'g': 5, 'T': 6, ',': 7, ':': 8, 'a': 9, 'v': 10, 's': 11}
grid = np.array([[ID[c] for c in row] for row in cells])


def smooth_noise(w, h, cell, seed):
    r = np.random.default_rng(seed)
    g = r.uniform(-1, 1, (h // cell + 3, w // cell + 3))
    ys, xs = np.arange(h) / cell, np.arange(w) / cell
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a, b = g[y0][:, x0], g[y0][:, x0 + 1]
    c, d = g[y0 + 1][:, x0], g[y0 + 1][:, x0 + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


# warp cell lookups so coasts and biome edges look hand-made, not blocky
wx = smooth_noise(BW, BH, 9, 1) * 6 + smooth_noise(BW, BH, 3, 2) * 1.2
wy = smooth_noise(BW, BH, 9, 3) * 7 + smooth_noise(BW, BH, 3, 4) * 1.5
YY, XX = np.mgrid[0:BH, 0:BW]
cx = np.clip(((XX + wx) // CW).astype(int), 0, M.W - 1)
cy = np.clip(((YY + wy) // CH).astype(int), 0, M.H - 1)
cls = grid[cy, cx]


def cpx(x, y):
    """cell -> base pixel centre"""
    return int(x * CW + CW // 2), int(y * CH + CH // 2)


land_big = cls != 0
# islets
islet_px = []
for (x, y) in M.ISLETS:
    px, py = cpx(x, y)
    px += int(rng.integers(-2, 3)); py += int(rng.integers(-3, 4))
    rx, ry = int(rng.integers(2, 4)), 2
    m = ((XX - px) / rx) ** 2 + ((YY - py) / ry) ** 2 <= 1.0
    cls[m] = ID[',']
    islet_px.append((px, py))


def dilate(mask, r):
    out = mask.copy()
    for _ in range(r):
        o = out.copy()
        o[1:] |= out[:-1]; o[:-1] |= out[1:]; o[:, 1:] |= out[:, :-1]; o[:, :-1] |= out[:, 1:]
        if _ % 2:
            o[1:, 1:] |= out[:-1, :-1]; o[:-1, :-1] |= out[1:, 1:]
            o[1:, :-1] |= out[:-1, 1:]; o[:-1, 1:] |= out[1:, :-1]
        out = o
    return out


sea = cls == 0
land = ~sea
beach = dilate(sea, 2) & np.isin(cls, [ID[','], ID[':']])
cls[beach] = ID['s']

# ---------------------------------------------------------------- base colours
img = np.zeros((BH, BW, 3), np.uint8)
R = rng.random((BH, BW))


def paint(mask, col):
    img[mask] = P[col]


near1 = dilate(land, 1) & sea
near4 = (dilate(land_big, 4) | dilate(land & ~land_big, 3)) & sea
near14 = dilate(land_big, 14) & sea
paint(sea, 'deep'); paint(near14, 'mid'); paint(near4, 'shallow'); paint(near1, 'foam')
for (yy, xx) in zip(*np.where(sea & ~near4 & (R < 0.004))):
    for d in range(3):
        if xx + d < BW and sea[yy, xx + d]:
            img[yy, xx + d] = P['wave']

lake = cls == 1
nonlake_land = land & ~lake & (cls != 2)
paint(lake, 'lake')
paint(lake & dilate(nonlake_land, 1), 'lake_edge')
for (yy, xx) in zip(*np.where(lake & (R < 0.006))):
    img[yy, xx:xx + 2] = P['lake_hi']
reeds = cls == 2
paint(reeds, 'lake_edge')
paint(reeds & (R < 0.30), 'reed')
paint(reeds & (R > 0.85), 'reed_dk')

for name, base, dk, lt in [(',', 'grass', 'grass_dk', 'grass_lt'), (':', 'dry', 'dry_dk', 'dry_lt'),
                           ('s', 'sand', 'sand_dk', 'sand'), ('^', 'rock', 'rock_dk', 'rock_lt'),
                           ('g', 'grey', 'grey_dk', 'rock_lt'), ('a', 'ash', 'volc', 'ash_lt'),
                           ('v', 'volc', 'ash', 'ash')]:
    m = cls == ID[name]
    paint(m, base); paint(m & (R < 0.10), dk); paint(m & (R > 0.93), lt)
grass = cls == ID[',']
paint(grass & (R > 0.997), 'flower')
paint((cls == ID[':']) & (R > 0.996), 'shrub')
canyon = cls == ID['c']
strata = ((YY + (smooth_noise(BW, BH, 6, 9) * 2).astype(int)) % 4) == 0
paint(canyon, 'canyon_dk'); paint(canyon & strata, 'canyon'); paint(canyon & (R > 0.95), 'canyon_lt')
forest = cls == ID['T']
paint(forest, 'floor')

# diorama drop shadow under rock and forest edges (down-right, dithered fringe)
tall = np.isin(cls, [ID['^'], ID['g'], ID['T'], ID['v']])
sh1 = np.zeros_like(tall); sh1[2:, 1:] = tall[:-2, :-1]
sh2 = np.zeros_like(tall); sh2[3:, 2:] = tall[:-3, :-2]
low = ~tall
dark1 = sh1 & low
dark2 = sh2 & low & ~dark1 & ((XX + YY) % 2 == 0)
img[dark1] = (img[dark1] * 0.72).astype(np.uint8)
img[dark2] = (img[dark2] * 0.80).astype(np.uint8)


def setp(x, y, col):
    if 0 <= x < BW and 0 <= y < BH:
        img[y, x] = P[col] if isinstance(col, str) else col


def shade(x, y, f=0.7):
    if 0 <= x < BW and 0 <= y < BH:
        img[y, x] = (img[y, x] * f).astype(np.uint8)


# ---------------------------------------------------------------- mountains
peaks = []
for gy in range(0, BH, 6):
    for gx in range(0, BW, 7):
        x = gx + int(rng.integers(-2, 3)) + (3 if (gy // 6) % 2 else 0)
        y = gy + int(rng.integers(-1, 2))
        h = int(rng.integers(5, 8))
        if not (0 <= x < BW and 0 <= y < BH - h):
            continue
        rocky = (ID['^'], ID['g'], ID['c'])
        ok = all(0 <= x + dx < BW and cls[y + h - 1, x + dx] in rocky for dx in (-h + 1, 0, h - 1)) \
            and cls[y, x] in rocky
        if ok:
            peaks.append((y, x, h, int(cls[y, x])))
for (y, x, h, kind) in sorted(peaks):
    grey, red = kind == ID['g'], kind == ID['c']
    snowy = (y < 110 and kind == ID['^'])
    for r in range(h):
        for dx in range(-r, r + 1):
            if red:                      # flat-topped mesa
                if r == 0 and abs(dx) > 0:
                    continue
                c = 'canyon_lt' if dx < 0 else ('canyon' if dx == 0 else 'canyon_dk')
                if r < 2:
                    c = 'canyon_lt'
            elif r <= 1 and snowy:
                c = 'snow' if dx <= 0 else 'snow_sh'
            elif grey:
                c = 'rock_lt' if dx < 0 else ('grey' if dx == 0 else 'grey_dk')
            else:
                c = 'rock_lt' if dx < 0 else ('rock' if dx == 0 else 'rock_dk')
            setp(x + dx, y + r, c)
        shade(x + r + 1, y + r, 0.75)

# ---------------------------------------------------------------- trees
trees = []
for gy in range(0, BH, 3):
    for gx in range(0, BW, 3):
        x = gx + int(rng.integers(-1, 2)); y = gy + int(rng.integers(-1, 2))
        if 0 <= x < BW - 3 and 0 <= y < BH - 4 and cls[y, x] == ID['T'] and cls[y + 2, x + 1] == ID['T']:
            trees.append((y, x))
for (y, x) in sorted(trees):
    pine = y < 8 * CH
    for (dx, dy) in [(1, 3), (2, 3), (3, 2), (3, 1)]:
        setp(x + dx, y + dy, 'tshadow')
    if pine:
        hi, md, dk = 'pine_hi', 'pine', 'pine_dk'
        for (dx, dy, c) in [(1, -1, md), (1, 0, hi), (0, 1, hi), (1, 1, md), (2, 1, dk),
                            (0, 2, md), (1, 2, dk), (2, 2, dk)]:
            setp(x + dx, y + dy, c)
    else:
        hi, md, dk = 'oak_hi', 'oak', 'oak_dk'
        for (dx, dy, c) in [(1, 0, hi), (0, 1, hi), (1, 1, md), (2, 1, dk), (0, 2, md), (1, 2, dk), (2, 2, dk)]:
            setp(x + dx, y + dy, c)
# a few trees on islets and Vellmarch isle
for (px, py) in islet_px[13:24]:
    for (dx, dy, c) in [(0, -1, 'oak_hi'), (-1, 0, 'oak_hi'), (0, 0, 'oak'), (1, 0, 'oak_dk'), (0, 1, 'oak_dk')]:
        setp(px + dx, py + dy - 1, c)


# ---------------------------------------------------------------- lines
def line_pts(a, b):
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        yield x0, y0
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy


def poly_pts(points):
    out = []
    for a, b in zip(points, points[1:]):
        seg = list(line_pts(a, b))
        out.extend(seg if not out else seg[1:])
    return out


def wobble(points, amt):
    """nudge interior points so straight cell-to-cell runs meander a little"""
    res = [points[0]]
    for p in points[1:-1]:
        res.append((p[0] + int(rng.integers(-amt, amt + 1)), p[1] + int(rng.integers(-amt, amt + 1))))
    res.append(points[-1])
    return res


def stroke(points, width, col, only=None, dash=None):
    for i, (x, y) in enumerate(poly_pts(points)):
        if dash and (i % dash[0]) >= dash[1]:
            continue
        for oy in range(width):
            for ox in range(width):
                xx, yy = x + ox - width // 2, y + oy - width // 2
                if 0 <= xx < BW and 0 <= yy < BH and (only is None or only[yy, xx]):
                    img[yy, xx] = P[col] if isinstance(col, str) else col


# rivers
for name, cells_ in M.RIVERS.items():
    a, b = M.RIVER_ENDS[name]
    pts = [cpx(*a)] + [cpx(*c) for c in cells_] + [cpx(*b)]
    pts = wobble(pts, 2)
    w = {'Sallow': 3, 'Candle Brook': 1}.get(name, 2)
    stroke(pts, w + 1, 'lake_edge')
    stroke(pts, w, 'lake')
# Tumble Falls
fx, fy = cpx(9, 8)
for dy in range(-4, 5):
    for dx in (-1, 0, 1):
        setp(fx + dx, fy + dy, 'foam' if (dy + dx) % 3 else 'lake_hi')
for dx in range(-3, 4):
    setp(fx + dx, fy + 5, 'foam')

# town anchor points (Emberkey's town sits on the west shore, crater to the east)
TPOS = {k: cpx(x, y) for k, (x, y, _) in M.TOWNS.items()}
TPOS['N'] = (77 * CW + 2, 19 * CH + 10)
LANDING = cpx(85, 11)
SUMMIT = cpx(6, 2)


def ends_for(rid, cells_):
    pool = {k: (x, y) for k, (x, y, _) in M.TOWNS.items()}
    others = [c for r, cs in {**M.ROUTES, **M.WINTER_ROUTES}.items() if r != rid for c in cs]

    def near(p):
        best = None
        for k, t in pool.items():
            d = max(abs(t[0] - p[0]), abs(t[1] - p[1]))
            if d <= 2 and (best is None or d < best[0]):
                best = (d, TPOS[k])
        if best:
            return best[1]
        for c in others:
            if max(abs(c[0] - p[0]), abs(c[1] - p[1])) <= 1:
                return cpx(*c)
        return None
    return near(cells_[0]), near(cells_[-1])


def route_points(rid, cells_):
    a, b = ends_for(rid, cells_)
    pts = [cpx(*c) for c in cells_]
    if rid == 15:
        b = SUMMIT
    if rid == 19:
        b = cpx(12, 3)
    return ([a] if a else []) + pts + ([b] if b else [])


# land routes (with drop shadow), island routes, winter ice paths
for rid, cs in M.ROUTES.items():
    pts = route_points(rid, cs)
    stroke([(x + 1, y + 1) for (x, y) in pts], 1, 'path_sh')
    stroke(pts, 1, 'path')
for pts in ([LANDING] + [cpx(*c) for c in M.ISLAND_ROUTES[30]] + [TPOS['O']],
            [TPOS['N'], cpx(79, 21), cpx(82, 21), cpx(81, 19)]):
    stroke([(x + 1, y + 1) for (x, y) in pts], 1, 'path_sh')
    stroke(pts, 1, 'path')
for rid, cs in M.WINTER_ROUTES.items():
    pts = route_points(rid, cs)
    stroke(pts, 1, 'ice_dk')
    stroke(pts, 1, 'ice', dash=(4, 2))

# sailing lanes: dotted, drawn on sea only
LANE_ENDS = {22: ('I', 'L'), 23: ('K', 'L'), 24: ('H', 'M'), 25: ('I', 'M'), 26: ('L', 'N'),
             28: ('M', LANDING), 29: ('N', LANDING)}
sea_now = cls == 0
for rid, cs in M.LANES.items():
    a, b = LANE_ENDS[rid]
    a = TPOS[a] if isinstance(a, str) else a
    b = TPOS[b] if isinstance(b, str) else b
    pts = [a] + [cpx(*c) for c in cs] + [b]
    stroke(pts, 1, 'foam', only=sea_now, dash=(5, 2))


# ---------------------------------------------------------------- sprites
def sprite(x, y, rows, pal):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.':
                setp(x + dx, y + dy, pal[ch])


def house(x, y, roof):
    for (dx, dy) in [(4, 1), (4, 2), (4, 3), (1, 4), (2, 4), (3, 4), (4, 4)]:
        shade(x + dx, y + dy, 0.65)
    sprite(x, y, ['.rr.', 'rrrr', 'wwww', 'wdww'],
           {'r': roof, 'w': 'wall', 'd': 'ink'})


CLUSTER = [(-2, -2), (2, -1), (-5, 1), (1, 2), (-2, 4), (4, 3), (-6, -3), (5, -4)]
TOWN_STYLE = {  # roof colour, house count
    'A': ('thatch', 2), 'B': ('wood', 3), 'C': ('roof', 4), 'D': ('canyon_dk', 3), 'E': ('roof', 3),
    'F': ('slate', 4), 'G': ('wood', 3), 'H': ('wood', 4), 'I': ('copper', 8), 'J': ('roof', 5),
    'K': ('roof', 4), 'L': ('slate', 3), 'M': ('wood', 3), 'N': ('roof', 3),
}
for k, (roof, n) in TOWN_STYLE.items():
    x, y = TPOS[k]
    for (dx, dy) in CLUSTER[:n]:
        if k == 'B':   # stilts over the water
            for s in (0, 3):
                setp(x + dx + s, y + dy + 4, 'ink'); setp(x + dx + s, y + dy + 5, 'ink')
        house(x + dx - 2, y + dy - 2, roof)
    if k == 'G':       # treetop village: giant trees around the houses
        for (dx, dy) in [(-6, -1), (5, 0), (0, -6)]:
            sprite(x + dx - 1, y + dy - 2, ['.h.', 'hmd', 'mdd', '.t.', '.t.'],
                   {'h': 'pine_hi', 'm': 'pine', 'd': 'pine_dk', 't': 'wood'})

# Thimbledown windmill
mx, my = TPOS['A'][0] + 5, TPOS['A'][1] - 6
sprite(mx - 3, my - 3, ['s.....s', '.s...s.', '..s.s..', '...h...', '..s.s..', '.s...s.', 's.....s'],
       {'s': 'wood', 'h': 'ink'})
sprite(mx - 1, my + 1, ['www', 'www', 'wdw'], {'w': 'wall', 'd': 'ink'})
# Copperhaven crane + piers
cx0, cy0 = TPOS['I']
sprite(cx0 + 5, cy0 - 7, ['wwww', 'w..i', 'w...', 'w...', 'w...'], {'w': 'wood', 'i': 'ink'})
for py in (cy0 + 2, cy0 + 6):
    for d in range(9, 14):
        setp(cx0 + d, py, 'wood')
# Keelwick dry dock with half-built hull
kx, ky = TPOS['H']
sprite(kx - 4, ky + 4, ['k.k.k.k.k', 'kkkkkkkkk', '.kkkkkkk.'], {'k': 'wood'})
# Vellmarch: towers and walls
vx, vy = TPOS['O']
for (dx, h) in [(-9, 6), (-5, 9), (-1, 12), (3, 8), (7, 10), (11, 5)]:
    tx, ty = vx + dx, vy + 4 - h
    setp(tx + 1, ty - 2, 'gold')
    sprite(tx, ty - 1, ['.s.', 'sss'], {'s': 'slate'})
    for r in range(h):
        sprite(tx, ty + 1 + r, ['wwd'], {'w': 'stone', 'd': 'wall_dk'})
    for r in range(h):
        shade(tx + 3, ty + 1 + r, 0.7)
for d in range(-10, 14):
    setp(vx + d, vy + 5, 'wall_dk')
# Gannet Head lighthouse
lx, ly = cpx(48, 7)
sprite(lx, ly - 9, ['.g.', 'iii', '.r.', '.w.', '.r.', '.w.', '.r.', 'www'],
       {'g': 'gold', 'i': 'ink', 'r': 'roof', 'w': 'wall'})
# Old Star Tower (ruined) on the summit
sx, sy = SUMMIT
sprite(sx - 1, sy - 7, ['s.s.', 'ssss', 'sdss', 'ssss', 'sdss', 'ssss'], {'s': 'stone', 'd': 'ink'})
# Reedholm bell tower (half sunk)
rx_, ry_ = cpx(24, 11)
sprite(rx_ - 3, ry_ + 1, ['.sssss.', 'sssssss'], {'s': 'sand'})
sprite(rx_ - 1, ry_ - 5, ['.s.', 'sss', 'sgs', 'sss', 'sss'], {'s': 'stone', 'g': 'gold'})
# sea arch "the Gate"
ax, ay = cpx(56, 1)
sprite(ax - 2, ay - 4, ['.gggggggg.', 'gggggggggg', 'gg......gg', 'gd......gd', 'gd......gd', 'gd......gd'],
       {'g': 'grey', 'd': 'grey_dk'})
# Drowned Spires
for (x, y) in M.SPIRES:
    px, py = cpx(x, y)
    sprite(px - 1, py - 3, ['.s.', '.s.', 'ttt', 'ttd'], {'s': 'slate', 't': 'stone', 'd': 'wall_dk'})
    setp(px - 2, py + 1, 'foam'); setp(px + 2, py + 1, 'foam')
# Maelstrom
mx_, my_ = cpx(*M.MAELSTROM)
for rad, gap in [(2, 0.0), (4, 1.0), (6, 2.2)]:
    for t in np.linspace(0, 2 * np.pi, 40):
        if (t + gap) % (2 * np.pi) < 4.6:
            setp(int(round(mx_ + rad * 1.4 * np.cos(t))), int(round(my_ + rad * np.sin(t))), 'foam')
setp(mx_, my_, 'ink')
# Emberkey volcano cone
ex, ey = cpx(81, 19)
for r in range(14):
    for dx in range(-r - 1, r + 2):
        c = 'ash_lt' if dx < -2 else ('ash' if dx < 2 else 'volc')
        if r < 2:
            c = 'canyon_dk'
        setp(ex + dx, ey - 1 + r, c)
    shade(ex + r + 2, ey - 1 + r, 0.7)
sprite(ex - 1, ey - 1, ['ogo', '.o.'], {'o': 'glow', 'g': 'gold'})
for (dx, dy) in [(0, -4), (1, -6), (-1, -8), (1, -10)]:
    sprite(ex + dx - 1, ey + dy, ['.a.', 'aaa', '.a.'], {'a': 'snow_sh'})
# winter-only spots: snowflake markers
for (x, y) in M.WINTER_SPOTS:
    px, py = cpx(x, y)
    if (x, y) == (24, 11):
        px, py = px + 5, py - 3
    sprite(px - 2, py - 2, ['..i..', '.iIi.', 'iIIIi', '.iIi.', '..i..'], {'i': 'ice_dk', 'I': 'ice'})

# ---------------------------------------------------------------- upscale + labels
big = Image.fromarray(img).resize((BW * S, BH * S), Image.NEAREST)
d = ImageDraw.Draw(big)
d.fontmode = '1'
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FS = '/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf'
f_town = ImageFont.truetype(F, 14)
f_tag = ImageFont.truetype(F, 10)
f_region = ImageFont.truetype(FS, 22)
f_region_s = ImageFont.truetype(FS, 15)
INK = tuple(int(v) for v in P['ink'])
CREAM = (246, 238, 220)

ANCHOR = {  # town label placement: (anchor, dx, dy) in final px
    'A': ('mt', 0, 14), 'B': ('rm', -16, 0), 'C': ('rm', -16, 0), 'D': ('mb', 0, -14),
    'E': ('mt', 0, 14), 'F': ('mb', 0, -16), 'G': ('mb', 0, -18), 'H': ('lm', 14, -6),
    'I': ('lm', 30, -14), 'J': ('lt', 10, 12), 'K': ('mt', 0, 16), 'L': ('lm', 22, 0),
    'M': ('mb', 0, -16), 'N': ('mt', 0, 26), 'O': ('mb', -6, -26),
}
for k, (_, _, name) in M.TOWNS.items():
    a, dx, dy = ANCHOR[k]
    x, y = TPOS[k]
    d.text((x * S + dx, y * S + dy), name, font=f_town, fill=CREAM, anchor=a, stroke_width=2, stroke_fill=INK)

TAG_COL = {'land': (59, 47, 42), 'winter': (62, 110, 124), 'sea': (36, 67, 77)}
for rid, (x, y) in M.LABELS.items():
    s = str(rid)
    kind = 'winter' if rid in M.WINTER_ROUTES or rid == 20 else ('sea' if rid in M.LANES else 'land')
    px = int((x + len(s) / 2) * CW * S)
    py = int((y * CH + CH // 2) * S)
    tw = 8 + 7 * len(s)
    d.rectangle([px - tw // 2 - 1, py - 8, px + tw // 2 + 1, py + 8], fill=INK)
    d.rectangle([px - tw // 2, py - 7, px + tw // 2, py + 7], fill=TAG_COL[kind])
    d.text((px, py), s, font=f_tag, fill=CREAM, anchor='mm')

for text, (x, y), font, col in [
        ('Speilmere', (444, 446), f_region, (214, 230, 214)),
        ('THE VIDSEA', (1150, 470), f_region, (200, 214, 200)),
        ('the Smaholms', (930, 236), f_region_s, (200, 214, 200)),
        ('Lyktmyr', (330, 222), f_region_s, (238, 230, 200)),
        ('Fjell Heights', (100, 100), f_region_s, (246, 238, 220)),
        ('Salt Flats', (180, 760), f_region_s, (110, 80, 50)),
        ('Lykt Landing', (1330, 330), f_region_s, (238, 230, 200))]:
    d.text((x, y), text, font=font, fill=col, anchor='mm')

# ---------------------------------------------------------------- frame, title, legend
MARGIN, TOP, LEG = 24, 70, 128
W2, H2 = BW * S + MARGIN * 2, TOP + BH * S + LEG
canvas = Image.new('RGB', (W2, H2), (43, 38, 34))
cd = ImageDraw.Draw(canvas)
cd.fontmode = '1'
cd.rectangle([MARGIN - 6, TOP - 6, MARGIN + BW * S + 5, TOP + BH * S + 5], fill=INK)
cd.rectangle([MARGIN - 3, TOP - 3, MARGIN + BW * S + 2, TOP + BH * S + 2], fill=(201, 168, 120))
canvas.paste(big, (MARGIN, TOP))
cd.text((MARGIN, 22), 'RAVENMARK', font=ImageFont.truetype(F, 28), fill=CREAM)
cd.text((MARGIN + BW * S, 34), 'World map · summer · 800 × 400 tiles · land west, sea east',
        font=ImageFont.truetype(F, 14), fill=(201, 168, 120), anchor='rm')

ly0 = TOP + BH * S + 22
f_leg = ImageFont.truetype(F, 13)


def leg_item(x, y, label, draw_icon):
    draw_icon(x, y)
    cd.text((x + 44, y + 8), label, font=f_leg, fill=CREAM, anchor='lm')


def px_block(x, y, col, w=2, h=2):
    cd.rectangle([x, y, x + w - 1, y + h - 1], fill=tuple(int(v) for v in P[col]) if isinstance(col, str) else col)


def ic_route(x, y):
    px_block(x + 2, y + 10, 'path_sh', 32, 2); px_block(x, y + 8, 'path', 32, 2)


def ic_lane(x, y):
    px_block(x, y + 2, 'deep', 34, 14)
    for i in range(0, 32, 7):
        px_block(x + 2 + i, y + 8, 'foam', 10 if i + 10 <= 32 else 32 - i, 2)


def ic_ice(x, y):
    px_block(x, y + 8, 'ice_dk', 32, 2)
    for i in range(0, 32, 6):
        px_block(x + i, y + 8, 'ice', 8 if i + 8 <= 32 else 32 - i, 2)


def ic_swatch(col, col2=None):
    def f(x, y):
        px_block(x, y + 1, 'ink', 32, 16); px_block(x + 2, y + 3, col, 28, 12)
        if col2:
            for i in range(0, 28, 4):
                px_block(x + 2 + i, y + 7, col2, 2, 4)
    return f


def ic_house(x, y):
    rows = ['.rr.', 'rrrr', 'wwww', 'wdww']
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.':
                px_block(x + 8 + dx * 4, y + dy * 4, {'r': 'roof', 'w': 'wall', 'd': 'ink'}[ch], 4, 4)


def ic_snow(x, y):
    rows = ['..i..', '.iIi.', 'iIIIi', '.iIi.', '..i..']
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.':
                px_block(x + 8 + dx * 3, y + 1 + dy * 3, 'ice_dk' if ch == 'i' else 'ice', 3, 3)


def ic_tag(col):
    def f(x, y):
        cd.rectangle([x + 4, y, x + 30, y + 16], fill=INK)
        cd.rectangle([x + 5, y + 1, x + 29, y + 15], fill=col)
        cd.text((x + 17, y + 8), '12', font=f_tag, fill=CREAM, anchor='mm')
    return f


cols = [MARGIN, MARGIN + 300, MARGIN + 620, MARGIN + 960, MARGIN + 1290]
rows_y = [ly0, ly0 + 30, ly0 + 60]
items = [
    ('Land route', ic_route), ('Sailing lane', ic_lane), ('Winter-only ice path', ic_ice),
    ('Settlement', ic_house), ('Winter-only spot', ic_snow), ('Route no. (land)', ic_tag(TAG_COL['land'])),
    ('Lake & rivers (freeze)', ic_swatch('lake', 'lake_hi')), ('Sea (never freezes)', ic_swatch('mid', 'wave')),
    ('Route no. (sea)', ic_tag(TAG_COL['sea'])),
    ('Reeds & marsh (walk when frozen)', ic_swatch('lake_edge', 'reed')),
    ('Forest', ic_swatch('oak', 'oak_hi')), ('Route no. (winter / lake)', ic_tag(TAG_COL['winter'])),
    ('Highlands & cliffs', ic_swatch('rock', 'rock_lt')), ('Dry lands & canyon', ic_swatch('dry', 'canyon')),
]
for i, (label, fn) in enumerate(items):
    leg_item(cols[i // 3], rows_y[i % 3], label, fn)
# scale bar: 5 screens wide = 100 tiles
sx0, sy0 = cols[4], ly0 + 66
cd.rectangle([sx0, sy0, sx0 + 100 * S, sy0 + 5], fill=INK)
for i in range(5):
    cd.rectangle([sx0 + i * 40 + 1, sy0 + 1, sx0 + i * 40 + 39, sy0 + 4],
                 fill=(236, 221, 176) if i % 2 == 0 else (94, 78, 60))
cd.text((sx0, sy0 + 16), '5 screens (100 tiles) across', font=f_leg, fill=CREAM, anchor='lm')

out = sys.argv[1] if len(sys.argv) > 1 else 'world_map.png'
canvas.save(out)
print('saved', out, canvas.size)
