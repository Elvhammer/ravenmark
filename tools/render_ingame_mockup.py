"""Mock in-game frame: Fennick Run at the edge of Keelwick, summer.

Renders at the real game resolution (320x180, 16 px tiles), upscales 4x
nearest-neighbour, applies the tilt-shift blur to the top and bottom bands
only, then draws the (unblurred) HUD. Usage:
    python3 render_ingame_mockup.py [out.png]
"""
import colorsys
import sys
import numpy as np
from PIL import Image, ImageFilter

# Style knobs (set OPTS before running via runpy to render variants; see make_style_sheets.py)
OPTS = globals().get('OPTS') or {}
DETAIL = OPTS.get('detail', 'busy')            # busy | medium | clean | smooth
OUTLINE = OPTS.get('outline', 'selective')     # selective | bold
ART = OPTS.get('art', 2)                       # 1 = first-pass objects, 2 = redrawn objects + new hero
ZOOM = OPTS.get('zoom', 1)                     # 1 = 320x180 view, 2 = 160x90 view (bigger pixels)
D = {'busy': 1.0, 'medium': 0.4, 'clean': 0.0, 'smooth': 0.0}[DETAIL]      # surface texture amount
DA = {'busy': 1.0, 'medium': 0.45, 'clean': 0.0, 'smooth': 0.0}[DETAIL]    # dither amount

TS = 16
SCENE = OPTS.get('scene', 'fennick')   # fennick | canyon | sea | snow | forest
if SCENE == 'sea' and OPTS.get('sea_zoom'):   # old zoomed-out sea view (640 x 360 at 2x), kept for reference
    COLS, ROWS = 41, 23
    VW, VH, SCALE = 640, 360, 2
    CROP_X, CROP_Y = 8, 4
else:                                  # same scale everywhere: 320 x 180 view at 4x
    COLS, ROWS = 21, 12
    VW, VH, SCALE = 320, 180, 4
    CROP_X, CROP_Y = 8, 6
WW, HH = COLS * TS, ROWS * TS
rng = np.random.default_rng(3)


def hx(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.uint8)


P = {k: hx(v) for k, v in {
    'grass': '#97A55A', 'grass_dk': '#83924C', 'grass_dk2': '#6F7F42', 'grass_lt': '#AAB66A', 'grass_hi': '#BFC57A',
    'path': '#C9A878', 'path_dk': '#A8875E', 'path_lt': '#DCC394', 'path_md': '#BA9A6C',
    'sand': '#DCC594', 'sand_dk': '#C8AE7C', 'sand_lt': '#E8D6A8', 'sand_wet': '#C4A976',
    'sea': '#45686A', 'sea_dp': '#3A5759', 'sea_lt': '#5A8580', 'foam': '#E8E0C8', 'spark': '#9CBFAE',
    'river': '#5F887C', 'river_dp': '#557E72', 'river_lt': '#78A091', 'river_hi': '#9CC2AE',
    'bank': '#7A5A40', 'bank_dk': '#5E4532',
    'cliff': '#8C6A4A', 'cliff_dk': '#6E513A', 'cliff_lt': '#A07C58',
    'leaf_dk': '#435C31', 'leaf': '#5F7D3E', 'leaf_lt': '#7E9A4C', 'leaf_hi': '#A1AE57', 'leaf_ol': '#2F3B2A',
    'pine_dk': '#3B5232', 'pine': '#4F6B3A', 'pine_lt': '#6A8645',
    'trunk': '#6E4B33', 'trunk_dk': '#4E3424', 'trunk_lt': '#8A6244',
    'roof': '#B5523B', 'roof_dk': '#8E3F2E', 'roof_lt': '#CF6D4F', 'roof_ln': '#7A3628',
    'wall': '#EADFC8', 'wall_sh': '#CFC2A6', 'beam': '#6E4B33', 'door': '#5A3B28', 'door_lt': '#7A5236',
    'glass': '#3F5E62', 'glass_lt': '#9CBFAE', 'stone': '#9C8A70', 'stone_lt': '#BBA98C', 'stone_dk': '#76664F',
    'ink': '#2F2A3A', 'cream': '#F4EBD8', 'gold': '#E2B84E', 'glow': '#F2D28A',
    'flower_a': '#F0E2C0', 'flower_b': '#E2A08C', 'flower_c': '#E8C25A',
    'iron': '#4A4450', 'wood': '#9A6A44', 'wood_dk': '#6E4B33', 'wood_lt': '#B88458',
    # player
    'cap': '#D9A23E', 'cap_dk': '#B07E2E', 'brim': '#9C6A30', 'pom': '#F0E2C0',
    'skin': '#ECC096', 'skin_sh': '#CF9C74', 'blush': '#E09A80', 'hair': '#6E4B33',
    'scarf': '#B5523B', 'scarf_dk': '#8E3F2E', 'coat': '#4F6E78', 'coat_dk': '#3D5660', 'coat_lt': '#6B8A8F',
    'strap': '#8A5A3B', 'pants': '#5A4A3A', 'pants_dk': '#45392D', 'boot': '#3B2F2A',
}.items()}


def recolor(c, t):
    """palette transform: contrast, hue/sat/value, tint, lift toward white"""
    if not t:
        return c
    v = c.astype(float) / 255
    v = (v - 0.5) * t.get('contrast', 1) + 0.5
    h, sa, va = colorsys.rgb_to_hsv(*np.clip(v, 0, 1))
    r, g, b = colorsys.hsv_to_rgb((h + t.get('hue', 0)) % 1, min(1, sa * t.get('sat', 1)), min(1, va * t.get('val', 1)))
    v = np.array([r, g, b]) * np.array(t.get('tint', (1, 1, 1)))
    v = v * (1 - t.get('lift', 0)) + t.get('lift', 0)
    return (np.clip(v, 0, 1) * 255).round().astype(np.uint8)


P.update({k: hx(v) for k, v in {
    'eye': '#2F2A3A',
    'rtop': '#C98A55', 'rtop_lt': '#DDA36A', 'rtop_dk': '#AE7045',
    'face': '#A85A3A', 'face_lt': '#C4704A', 'face_dk': '#8A4530', 'face_ln': '#6A3224',
    'dust': '#D6A870', 'dust_lt': '#E4BE88', 'dust_dk': '#BE905C', 'dust_md': '#CC9C64',
    'trail': '#E6CC98', 'trail_dk': '#CDAE7A', 'rail': '#A8A2AC', 'rail_dk': '#5E5866',
    'ore': '#E0843E', 'ore_lt': '#F2B05A', 'tin': '#A3A7AE', 'tin_dk': '#767B86', 'tin_lt': '#C6C9CE',
    'wall_dk': '#A89A80', 'shut': '#4E8C95', 'shut_dk': '#2E5466',
    'hat': '#A8693F', 'hat_dk': '#7A4B33', 'hat_lt': '#C98A55', 'band': '#B8483A',
    'feather': '#F2E3B3', 'feather_dk': '#C9B98A', 'hair2': '#4B3238',
    'coat2': '#4E8C95', 'coat2_dk': '#2E5466', 'coat2_lt': '#7FB3B0', 'button': '#E0A256',
    'scarf2': '#B8483A', 'scarf2_dk': '#8E3F2E', 'satchel': '#8A5A3B', 'satchel_dk': '#6E4A35',
    'tube': '#F2E3B3', 'tube_dk': '#C9B98A', 'cap_red': '#B8483A',
    'pants2': '#3D3550', 'pants2_dk': '#2A2438', 'boot2': '#6E4A35', 'boot2_dk': '#4B3238',
    'snow': '#F4F1EA', 'snow_lt': '#FFFFFF', 'snow_sh': '#C9D3DC', 'snow_dk': '#A3AEBD',
    'frz': '#6FA8AE', 'frz_dk': '#3F6E78', 'frz_hi': '#BFE0E0', 'crack': '#2E5466',
    'slate': '#5E6372', 'slate_lt': '#7A8090', 'slate_dk': '#454A58', 'win_glow': '#F2C14E',
    'mb_skin': '#8C8A76', 'mb_skin_dk': '#5E5C50', 'mb_skin_lt': '#B0AC92',
    'bark_lt': '#A8693F', 'bark': '#6E4A35', 'bark_dk': '#3D3550',
    'floor': '#55703C', 'floor_dk': '#34452C', 'litter': '#8E7A4A', 'moss': '#6E8A3E',
    'otter': '#8A5A3B', 'otter_lt': '#B07E50', 'otter_dk': '#5E3E2A', 'muzzle': '#E8D2A8',
    'seal': '#8A8496', 'seal_lt': '#B8B4C4', 'seal_dk': '#5E5870',
    'thatch': '#CFA650', 'thatch_dk': '#A8823E', 'thatch_lt': '#E2C070',
    'shell': '#8A6A3E', 'shell_lt': '#B08A52', 'shell_dk': '#5E4630', 'shell_rim': '#C9A060',
    'tskin': '#6E8A48', 'tskin_dk': '#44603A', 'tskin_lt': '#9DB060',
    'whale': '#7A7690', 'whale_lt': '#A9C8C8', 'whale_dk': '#4A4060',
    'manta': '#463C58', 'manta_lt': '#8A8496', 'manta_dk': '#2A2438',
    'crab': '#C4583E', 'crab_dk': '#8E3F2E', 'crab_lt': '#E08A60',
    'saddle': '#8A5A3B', 'blanket': '#B8483A', 'blanket_lt': '#E48A73',
    'plank': '#9A6A44', 'plank_dk': '#744E33', 'plank_lt': '#B88458',
    'shrub': '#8E8C4C', 'shrub_dk': '#64633A', 'shrub_lt': '#B4AE66', 'mine': '#1E1B2C',
}.items()})
P = {k: recolor(v, OPTS.get('palette')) for k, v in P.items()}

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
img = np.zeros((HH, WW, 3), np.uint8)
YY, XX = np.mgrid[0:HH, 0:WW]
BAY = BAYER[YY % 4, XX % 4]
R = rng.random((HH, WW))


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


def tmask(ch):
    return np.kron((TG == ch).astype(np.uint8), np.ones((TS, TS), np.uint8)).astype(bool)


def offsets(r):
    return [(dx, dy) for dy in range(-r, r + 1) for dx in range(-r, r + 1) if dx * dx + dy * dy <= r * r + 0.5]


def look(m, dx, dy, r):
    p = np.pad(m, r, mode='edge')
    return p[r + dy:r + dy + m.shape[0], r + dx:r + dx + m.shape[1]]


def dil(m, r):
    o = np.zeros_like(m)
    for dx, dy in offsets(r):
        o |= look(m, dx, dy, r)
    return o


def ero(m, r):
    o = np.ones_like(m)
    for dx, dy in offsets(r):
        o &= look(m, dx, dy, r)
    return o


def rounded(m, r):
    return dil(ero(dil(ero(m, r), r), r), r)


def warp(m, amp, cell, seed):
    dx = (smooth_noise(WW, HH, cell, seed) * amp).round().astype(int)
    dy = (smooth_noise(WW, HH, cell, seed + 1) * amp).round().astype(int)
    return m[np.clip(YY + dy, 0, HH - 1), np.clip(XX + dx, 0, WW - 1)]


def paint(m, col):
    img[m] = P[col]


def blob(cx, cy, rx, ry, seed, amp=0.25):
    n = smooth_noise(WW, HH, 12, seed)
    return ((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2 < 1 + n * amp * 2


def thick_poly(pts, r):
    m = np.zeros((HH, WW), bool)
    for a, b in zip(pts, pts[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
        for t in np.linspace(0, 1, n):
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            m |= (XX - x) ** 2 + (YY - y) ** 2 <= r * r
    return m


def dist_from(m, n):
    """0 inside m, then 1..n rings outward (n+1 beyond)"""
    d = np.full(m.shape, n + 1)
    d[m] = 0
    cur = m.copy()
    for i in range(1, n + 1):
        cur = dil(cur, 1)
        d[(d == n + 1) & cur] = i
    return d


# ------------------------------------------------------------------ scene ground
if SCENE == 'fennick':
    # ------------------------------------------------------------------ tile map
    T = [['g'] * COLS for _ in range(ROWS)]
    for r in range(0, 7):
        T[r][3] = T[r][4] = 'w'
    for c in (2, 3, 4):
        T[7][c] = 'w'
    for c in (1, 2, 3, 4):
        T[8][c] = 'w'
    for c in range(0, 5):
        T[9][c] = 'w'
    for c in range(COLS):
        if T[4][c] != 'w':
            T[4][c] = 'p'
    for r in (5, 6, 7, 8):
        T[r][10] = 'p'
    for c in range(5, COLS):
        T[9][c] = 's'
    for c in range(8, COLS):
        T[10][c] = 's'
    for c in range(0, 8):
        T[10][c] = 'o'
    for c in range(13, COLS):
        T[11][c] = 's'
    for c in range(0, 13):
        T[11][c] = 'o'
    TG = np.array(T)


    water = warp(rounded(tmask('w'), 5), 2, 7, 10)
    sea = warp(rounded(tmask('o'), 6), 3, 9, 20)
    sand = warp(rounded(tmask('s') | tmask('o'), 6), 3, 9, 20) & ~sea
    path = warp(rounded(tmask('p'), 4), 1.5, 6, 30) & ~water & ~sea & ~sand
    grass = ~(water | sea | sand | path)
    fresh = water & ~sea


    # ------------------------------------------------------------------ ground
    mott = smooth_noise(WW, HH, 10, 40) * 0.6 + smooth_noise(WW, HH, 4, 41) * 0.4 * (DA > 0)
    lo, hi = {'busy': (-0.32, 0.38), 'medium': (-0.4, 0.45), 'clean': (-0.38, 9), 'smooth': (-0.28, 0.3)}[DETAIL]
    paint(grass, 'grass')
    paint(grass & (mott + (BAY - 0.5) * 0.35 * DA < lo), 'grass_dk')
    paint(grass & (mott + (BAY - 0.5) * 0.35 * DA > hi), 'grass_lt')
    paint(grass & (R < 0.02 * D), 'grass_dk2')

    paint(path, 'path')
    pn = smooth_noise(WW, HH, 5, 50)
    paint(path & (pn + (BAY - 0.5) * 0.4 * DA < (-0.6 if DETAIL == 'medium' else -0.35) - (0.3 if ART >= 2 else 0)), 'path_md')
    paint(path & (R < 0.03 * D), 'path_dk')
    paint(path & (R > 1 - 0.025 * D), 'path_lt')
    path_edge = path & dil(grass, 1)
    paint(path_edge, 'path_dk')

    paint(sand, 'sand')
    paint(sand & (R < 0.06 * D), 'sand_dk')
    paint(sand & (R > 1 - 0.05 * D), 'sand_lt')
    paint(sand & dil(sea, 4) & ~dil(sea, 1), 'sand_wet')
    if ART >= 2:   # wind ripples in the dry sand
        rip = sand & ~dil(sea, 6) & (((YY + np.round(2 * np.sin(XX / 7.0)).astype(int)) % 8) == 0) \
            & (np.sin(XX / 5.0 + YY) > -0.3)
        paint(rip, 'path')

    dist_sand = np.zeros((HH, WW), int)
    m = sand | grass | path
    for i in range(1, 16):
        m = dil(m, 1)
        dist_sand[(dist_sand == 0) & m & sea] = i
    paint(sea, 'sea')
    paint(sea & (dist_sand == 0), 'sea_dp')
    paint(sea & (dist_sand > 10) & ((BAY < 0.5) if DA else (dist_sand > 12)), 'sea_dp')
    waveband = sea & ((YY + (smooth_noise(WW, HH, 8, 60) * 3).astype(int)) % 7 == 0) & (R < 0.55 * max(D, 0.5))
    paint(waveband, 'sea_lt')
    paint(sea & (R > 1 - 0.004 * D), 'spark')
    foam = sea & (dist_sand >= 1) & (dist_sand <= 2) & ((XX // 3 + YY) % 5 != 0)
    paint(foam, 'foam')
    foam2 = sea & (dist_sand == 5) & (np.sin(XX / 3.0 + YY) > 0.2)
    paint(foam2, 'foam')

    paint(fresh, 'river')
    paint(fresh & ~dil(~fresh, 4), 'river_dp')
    paint(fresh & dil(~fresh, 1), 'river_lt')
    for (yy, xx) in zip(*np.where(fresh & (R < 0.012 * max(D, 0.3)))):
        for k in range(4):
            if yy + k < HH and fresh[yy + k, xx]:
                img[yy + k, xx] = P['river_hi']
    land = ~(fresh | sea)
    # bank face: water directly below land shows the earth bank (depth)
    above1 = np.zeros_like(land); above1[1:] = land[:-1]
    above3 = np.zeros_like(land); above3[3:] = land[:-3]
    paint(fresh & above1, 'bank')
    paint(fresh & above3 & ~above1, 'bank_dk')

    # ledge (one-way, hop down onto the beach): rows 8 cols 5.., face in bottom of tile
    lip_y = 8 * TS + 9 + np.round(np.sin(np.arange(WW) / 9.0)).astype(int)
    lnoise = smooth_noise(WW, 1, 7, 80)[0]
    for x in range(5 * TS + 3, WW):
        if fresh[lip_y[x] - 2, x]:
            continue
        y0 = lip_y[x]
        img[y0 - 1, x] = P['grass_hi']
        fh = 7 if ART >= 2 else 6
        for y in range(y0, y0 + fh):
            if 0 <= y < HH:
                if ART >= 2:   # irregular earth strata instead of block stripes
                    k = y - y0
                    streak = (k + int(round(2.5 * lnoise[x]))) % 3 == 0
                    c = 'cliff_lt' if k == 0 else ('cliff_dk' if k == fh - 1 or (streak and k > 1) else 'cliff')
                    if 2 <= k <= 4 and R[y, x] > 0.985:
                        c = 'stone_lt'
                else:
                    c = 'cliff_lt' if y == y0 else ('cliff_dk' if (x % 5 == 0 or y == y0 + 5) else 'cliff')
                img[y, x] = P[c]
        if ART >= 2 and R[y0, x] < 0.3:      # grass hanging over the lip
            img[y0, x] = P['grass']
            if R[y0, x] < 0.12:
                img[y0 + 1, x] = P['grass_dk']
        for y in (y0 + fh, y0 + fh + 1):
            if y < HH and sand[y, x]:
                img[y, x] = (img[y, x] * 0.72).astype(np.uint8)
        if y0 + fh + 2 < HH and sand[y0 + fh + 2, x] and (x + y0) % 2 == 0:
            img[y0 + fh + 2, x] = (img[y0 + fh + 2, x] * 0.82).astype(np.uint8)


elif SCENE == 'canyon':
    # north cliff (plateau top + tall striated face), south-west mesa, dusty floor with a trail
    FACE_H = 30
    edge_n = (30 + 3 * np.sin(np.arange(WW) / 13.0) + smooth_noise(WW, 1, 9, 70)[0] * 3).round().astype(int)
    E = edge_n[None, :]
    top_n = YY < E
    face_n = ~top_n & (YY < E + FACE_H)
    mesa_x = (66 + smooth_noise(1, HH, 8, 71)[:, 0] * 5).round().astype(int)[:, None]
    top_sw = (XX < mesa_x) & (YY >= 146) & (YY < 170)
    face_sw = (XX < mesa_x) & (YY >= 170)
    floor = ~(top_n | face_n | top_sw | face_sw)
    tr = np.zeros((HH, WW), bool)
    tr[70:HH, 158:178] = True
    tr[60:76, 62:290] = True
    trail = warp(rounded(tr, 5), 1.5, 6, 72) & floor
    tops = top_n | top_sw
    tn = smooth_noise(WW, HH, 7, 73)
    paint(tops, 'rtop')
    paint(tops & (tn + (BAY - 0.5) * 0.4 * DA < -0.35), 'rtop_dk')
    paint(tops & (tn + (BAY - 0.5) * 0.4 * DA > 0.4), 'rtop_lt')
    paint(tops & (R < 0.03 * D), 'rtop_dk')
    paint(top_n & (YY >= E - 1), 'rtop_lt')
    paint(top_sw & (YY < 148), 'rtop_lt')
    paint(top_sw & (XX >= mesa_x - 2), 'rtop_dk')

    def strata(face, y0):
        d = YY - y0 + np.round(2 * np.sin(XX / 11.0)).astype(int)
        paint(face, 'face')
        paint(face & ((d // 6) % 2 == 1), 'face_dk')
        paint(face & (d % 6 == 0), 'face_ln')
        paint(face & (d < 2), 'face_lt')
        paint(face & (R < 0.04 * max(D, 0.5)), 'face_lt')
    strata(face_n, E)
    strata(face_sw, 170)
    for x in range(WW):
        if R[0, x] < 0.05:
            y0 = edge_n[x] + 4 + int(R[1, x] * 10)
            for y in range(y0, min(y0 + 6 + int(R[2, x] * 10), edge_n[x] + FACE_H)):
                img[y, x] = P['face_ln']
    fn_ = smooth_noise(WW, HH, 9, 74)
    paint(floor, 'dust')
    paint(floor & (fn_ + (BAY - 0.5) * 0.4 * DA < -0.3), 'dust_md')
    paint(floor & (fn_ + (BAY - 0.5) * 0.4 * DA > (0.85 if DETAIL == 'medium' else 0.42)), 'dust_lt')
    paint(floor & (R < 0.025 * D), 'dust_dk')
    paint(trail, 'trail')
    paint(trail & dil(floor & ~trail, 1), 'trail_dk')
    paint(trail & (R < 0.02 * D), 'trail_dk')
    MX0, MX1 = 198, 226
    mtop = int(edge_n[212]) + 8
    mbot = int(edge_n[212]) + FACE_H
    mine = ((XX - (MX0 + MX1) / 2) / ((MX1 - MX0) / 2)) ** 2 + ((YY - (mtop + 10)) / 10) ** 2 <= 1
    mine |= (XX >= MX0) & (XX <= MX1) & (YY >= mtop + 10) & (YY < mbot)
    paint(mine & face_n, 'mine')
elif SCENE == 'sea':
    # The Scatterlings: islets, a sandbar, sea stacks; depth from distance to land
    if WW > 400:
        isA = blob(118, 92, 88, 50, 101)
        isB = blob(505, 66, 40, 24, 102)
        isC = blob(604, 112, 34, 22, 103)
        isD = blob(566, 290, 62, 34, 104)
        sandbar = blob(150, 304, 74, 13, 105, 0.15)
        stack_bases = blob(386, 92, 13, 5, 106, 0.05) | blob(252, 322, 10, 4, 107, 0.05) | blob(452, 346, 8, 4, 108, 0.05)
        islands = isA | isB | isC | isD
    else:
        isA = blob(30, 34, 70, 34, 101)
        isB = blob(318, 26, 44, 26, 102)
        sandbar = blob(56, 174, 66, 12, 105, 0.15)
        stack_bases = blob(262, 94, 10, 4, 106, 0.05) | blob(292, 171, 7, 3, 107, 0.05)
        islands = isA | isB
    land = islands | sandbar | stack_bases
    sea = ~land
    dsea = dist_from(land, 24)
    dland = dist_from(sea, 6)
    MOSS = smooth_noise(WW, HH, 4, 402)
    paint(sea, 'sea_dp')
    paint(sea & (dsea <= 16), 'sea')
    if DA:
        paint(sea & (dsea > 16) & (dsea <= 19) & (BAY < 0.5), 'sea')
    paint(sea & (dsea <= 6), 'sea_lt')
    swell = sea & (dsea > 8) & (((YY + np.round(4 * np.sin(XX / 23.0)).astype(int)) % 19) == 0) & (R < 0.6)
    paint(swell & (dsea > 16), 'sea')
    paint(swell & (dsea <= 16), 'sea_lt')
    for (yy, xx) in zip(*np.where(sea & (dsea > 6) & (R < 0.0025))):
        for k in range(3):
            if xx + k < WW and sea[yy, xx + k]:
                img[yy, xx + k] = P['sea_lt']
    paint(sea & (R > 0.9985), 'spark')
    paint(sea & (dsea <= 2) & ((XX // 3 + YY) % 5 != 0), 'foam')
    paint(sea & (dsea == 5) & (np.sin(XX / 3.0 + YY) > 0.3), 'foam')
    mi = smooth_noise(WW, HH, 10, 140)
    paint(islands, 'grass')
    paint(islands & (mi + (BAY - 0.5) * 0.35 * DA < -0.4), 'grass_dk')
    paint(islands & (mi + (BAY - 0.5) * 0.35 * DA > 0.45), 'grass_lt')
    paint(islands & (dland <= 3), 'sand')
    paint((islands | sandbar) & (dland == 1), 'sand_wet')
    paint(sandbar & (dland > 1), 'sand')
    paint(stack_bases, 'stone_dk')

elif SCENE == 'snow':
    # Hightarn in winter: snowfields, a trampled trail, the frozen tarn (walkable) with Tarn Isle
    tarn = blob(66, 172, 100, 42, 201, 0.15)
    isle = blob(58, 170, 15, 8, 202, 0.1)
    ice = tarn & ~isle
    trail = thick_poly([(166, -4), (166, 60), (165, 100), (150, 124), (126, 146)], 8) | thick_poly([(40, 66), (300, 72)], 6)
    trail = warp(trail, 1.5, 6, 203) & ~ice
    snow_m = ~ice
    sn = smooth_noise(WW, HH, 11, 204)
    paint(snow_m, 'snow')
    paint(snow_m & (sn + (BAY - 0.5) * 0.4 * DA > 0.4), 'snow_lt')
    paint(snow_m & (R > 0.997), 'snow_lt')
    paint(trail, 'snow_sh')
    paint(trail & (R < 0.06 * max(D, 0.5)), 'snow_dk')
    above = np.zeros_like(trail)
    above[1:] = ~trail[:-1] & snow_m[:-1]
    paint(trail & above, 'snow_dk')
    paint(ice, 'frz')
    paint(ice & ((((XX - YY) % 29) < 2) | (((XX - YY + 11) % 41) == 0)) & (smooth_noise(WW, HH, 8, 205) > -0.2), 'frz_hi')
    paint(ice & (R < 0.01), 'frz_hi')
    cr = np.random.default_rng(206)
    for _ in range(8):
        x, y = int(cr.integers(10, 150)), int(cr.integers(140, 190))
        for k in range(int(cr.integers(10, 30))):
            if 0 <= x < WW and 0 <= y < HH and ice[y, x]:
                img[y, x] = P['crack']
            x += int(cr.integers(-1, 2)); y += int(cr.choice([-1, 0, 0, 1]))
    paint(ice & (smooth_noise(WW, HH, 6, 207) > 0.55), 'snow')
    paint(ice & dil(snow_m, 1), 'frz_dk')
    bank = np.zeros_like(ice)
    bank[:-1] = ice[1:]
    paint(snow_m & bank, 'snow_sh')

elif SCENE == 'forest':
    # Hollowood: shady forest floor, sun-dappled patches, a narrow path into the hollow oak
    fpath = warp(thick_poly([(172, 196), (166, 150), (172, 112), (165, 76), (168, 40)], 7), 2, 6, 301)
    floor = ~fpath
    MOSSF = smooth_noise(WW, HH, 5, 304)
    fn2 = smooth_noise(WW, HH, 22, 302) * 0.8 + smooth_noise(WW, HH, 9, 303) * 0.2
    # calm floor: one dark tone, a few large soft sunlit pools (no speckle, no dither), a grassy verge by the path
    paint(floor, 'floor_dk')
    paint(floor & (fn2 > 0.32), 'floor')
    paint(floor & dil(fpath, 3) & ~dil(fpath, 1), 'floor')
    paint(fpath, 'path')
    paint(fpath & dil(floor, 1), 'path_dk')
    for (xa, ya, xb, yb) in [(150, 122, 186, 127), (146, 150, 184, 144)]:     # roots across the path
        n = xb - xa
        for k in range(n + 1):
            x, y = xa + k, int(round(ya + (yb - ya) * k / n + np.sin(k / 4.0)))
            img[y, x] = P['trunk_dk']
            img[y - 1, x] = P['trunk']

# ------------------------------------------------------------------ helpers
OBJ = np.zeros((HH, WW), bool)
OUTL = np.zeros((HH, WW), bool)
OUT_KEYS = ('ink', 'leaf_ol')
REC = [False]
ST = np.array(OPTS.get('shadow_tint', (1, 1, 1)), float)


def setp(x, y, col):
    if 0 <= x < WW and 0 <= y < HH:
        img[y, x] = P[col] if isinstance(col, str) else col
        if REC[0]:
            OBJ[y, x] = True
            OUTL[y, x] = isinstance(col, str) and col in OUT_KEYS


def shade(x, y, f):
    if 0 <= x < WW and 0 <= y < HH:
        img[y, x] = np.clip(img[y, x] * f * (ST if f < 0.95 else 1), 0, 255).astype(np.uint8)


def shade_mask(m, f):
    img[m] = np.clip(img[m] * f * ST, 0, 255).astype(np.uint8)


def sprite(x, y, rows, pal):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.':
                setp(x + dx, y + dy, pal[ch])


def drop_shadow(cx, cy, rx, ry):
    """pixel drop shadow: solid core, dithered rim"""
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if not (0 <= x < WW and 0 <= y < HH):
                continue
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= (0.8 if DETAIL == 'clean' else 0.62):
                shade(x, y, 0.66)
            elif DETAIL == 'smooth' and d <= 1.0:
                shade(x, y, 0.82)
            elif DA and d <= 1.0 and (x + y) % 2 == 0:
                shade(x, y, 0.78)


if SCENE == 'fennick':
    # grass decoration: tufts, flowers, reeds, pebbles
    for (yy, xx) in zip(*np.where(grass & (R > 1 - 0.012 * max(D, 0.25)))):
        sprite(xx - 1, yy - 2, ['d.d', '.D.'] if R[yy, xx] > 0.994 else ['l.l', 'dld'],
               {'d': 'grass_dk2', 'D': 'grass_dk', 'l': 'grass_hi'})
    for (fx, fy) in [(104, 98), (132, 118), (220, 102), (250, 110), (60, 30), (150, 36), (300, 92), (20, 112)]:
        for _ in range(6):
            x, y = fx + int(rng.integers(-6, 7)), fy + int(rng.integers(-4, 5))
            if 0 <= x < WW and 0 <= y < HH and grass[y, x]:
                col = ['flower_a', 'flower_b', 'flower_c'][int(rng.integers(0, 3))]
                setp(x, y, col); setp(x, y + 1, 'grass_dk2')
    for (yy, xx) in zip(*np.where(grass & dil(fresh, 1) & (R < 0.18 * max(D, 0.4)))):
        for k in range(3):
            setp(xx, yy - k, 'grass_dk2' if k == 0 else ('grass_hi' if k == 2 else 'leaf'))
    for (yy, xx) in zip(*np.where(path & ~path_edge & (R > 1 - 0.008 * D))):
        sprite(xx, yy, ['ll', 'dd'], {'l': 'path_lt', 'd': 'path_dk'})
    for (yy, xx) in zip(*np.where(sand & (R > 1 - 0.003 * max(D, 0.3)))):
        sprite(xx, yy, ['f.', '.d'], {'f': 'flower_a', 'd': 'sand_dk'})

elif SCENE == 'canyon':
    # contact shadow where the cliff face meets the floor
    shade_mask(floor & (YY >= E + FACE_H) & (YY < E + FACE_H + 3), 0.7)
    shade_mask(floor & (YY >= E + FACE_H + 3) & (YY < E + FACE_H + 5) & ((XX + YY) % 2 == 0), 0.84)
    # mine rails: straight run, a curve, then up into the mine
    for x in range(0, 197, 5):
        for xx in (x, x + 1):
            for y in range(119, 130):
                setp(xx, y, 'plank' if xx == x else 'plank_dk')
    for t in np.radians(np.arange(90, -1, -15)):
        for r in np.arange(11, 22, 0.5):
            setp(int(round(196 + r * np.cos(t))), int(round(108 + r * np.sin(t))), 'plank_dk')
    rail_top = int(edge_n[212]) + FACE_H - 4
    for y in range(rail_top, 109, 5):
        for yy in (y, y + 1):
            for x in range(207, 218):
                setp(x, yy, 'plank' if yy == y else 'plank_dk')
    for x in range(0, 197):
        for (y, c) in ((121, 'rail'), (122, 'rail_dk'), (127, 'rail'), (128, 'rail_dk')):
            setp(x, y, c)
    for t in np.linspace(np.pi / 2, 0, 160):
        for r in (13, 19):
            x, y = int(round(196 + r * np.cos(t))), int(round(108 + r * np.sin(t)))
            setp(x, y, 'rail'); setp(x, y + 1, 'rail_dk')
    for y in range(rail_top, 109):
        for (x, c) in ((209, 'rail'), (210, 'rail_dk'), (215, 'rail'), (216, 'rail_dk')):
            setp(x, y, c)
    # dry grass tufts and pebbles
    R2 = np.random.default_rng(9).random((HH, WW))
    for (yy, xx) in zip(*np.where(floor & ~trail & (R2 > 1 - 0.007 * max(D, 0.3)))):
        sprite(xx - 1, yy - 2, ['d.d', '.d.'], {'d': 'shrub_dk'})
    for (yy, xx) in zip(*np.where((floor | tops) & (R2 < 0.004 * max(D, 0.3)))):
        sprite(xx, yy, ['ll', 'dd'], {'l': 'dust_lt', 'd': 'face_dk'})
elif SCENE == 'sea':
    for (yy, xx) in zip(*np.where(islands & (dland > 3) & (R > 1 - 0.012 * max(D, 0.25)))):
        sprite(xx - 1, yy - 2, ['l.l', 'dld'], {'d': 'grass_dk2', 'l': 'grass_hi'})
    for (yy, xx) in zip(*np.where((islands | sandbar) & (dland <= 3) & (R > 0.996))):
        sprite(xx, yy, ['f.', '.d'], {'f': 'flower_a', 'd': 'sand_dk'})
elif SCENE == 'snow':
    for i, y in enumerate(range(8, 92, 7)):                 # footprints down the trail behind the player
        x = 163 + (4 if i % 2 else 0)
        sprite(x, y, ['dd', 'sd', '.s'], {'d': 'snow_dk', 's': 'snow_sh'})
    R2 = np.random.default_rng(209).random((HH, WW))
    for (yy, xx) in zip(*np.where(snow_m & ~trail & (R2 > 0.997))):
        sprite(xx - 1, yy - 2, ['d.d', '.d.'], {'d': 'pine_dk'})   # dry grass poking through snow
elif SCENE == 'forest':
    for (yy, xx) in zip(*np.where(floor & (fn2 > 0.32) & (R > 0.9975))):
        sprite(xx - 1, yy - 2, ['l.l', '.l.'], {'l': 'leaf_lt'})

# ------------------------------------------------------------------ objects
def mix(a, b, t):
    return (P[a] * (1 - t) + P[b] * t).round().astype(np.uint8)


if DETAIL == 'smooth':      # more tones, no dither
    LEAF_TONES = [P['leaf_dk'], mix('leaf_dk', 'leaf', 0.5), P['leaf'], mix('leaf', 'leaf_lt', 0.5),
                  P['leaf_lt'], mix('leaf_lt', 'leaf_hi', 0.5), P['leaf_hi']]
elif DETAIL == 'clean':     # fewer tones, no dither
    LEAF_TONES = ['leaf_dk', 'leaf', 'leaf_lt']
else:
    LEAF_TONES = ['leaf_dk', 'leaf', 'leaf_lt', 'leaf_hi']
objects = []   # (sort_y, draw_fn)
shadows = []   # (cx, cy, rx, ry)


def tree(bx, by, s=1.0):
    th = int(9 * s)
    cy = by - th - int(11 * s)
    clumps = [(0, -7, 10), (-9, -1, 8), (9, -1, 8), (-5, -13, 7), (6, -12, 7), (0, 3, 9)]
    shadows.append((bx + 7 * s, by + 1, 14 * s, 5 * s))

    def draw():
        for y in range(by - th, by):
            for x in range(bx - 3, bx + 3):
                c = 'trunk_lt' if x == bx - 3 else ('trunk_dk' if x >= bx + 1 else 'trunk')
                setp(x, y, c)
        sprite(bx - 4, by - 2, ['t......t', 'tt....tt'], {'t': 'trunk_dk'})
        mask = {}
        for (ox, oy, r) in sorted(clumps, key=lambda c: c[1]):
            ccx, ccy, rr = bx + ox * s, cy + oy * s, r * s
            for y in range(int(ccy - rr), int(ccy + rr) + 1):
                for x in range(int(ccx - rr), int(ccx + rr) + 1):
                    nx, ny = (x - ccx) / rr, (y - ccy) / rr
                    if nx * nx + ny * ny > 1.0:
                        continue
                    lgt = -(0.55 * nx + 0.85 * ny) * 0.5 + 0.5 - (y - cy) / (40 * s)
                    v = lgt + (BAYER[y % 4, x % 4] - 0.5) * 0.3 * DA
                    tone = LEAF_TONES[int(np.clip(v * len(LEAF_TONES), 0, len(LEAF_TONES) - 1))]
                    setp(x, y, tone)
                    mask[(x, y)] = True
        for (x, y) in list(mask):
            if (x + 1, y) not in mask or (x, y + 1) not in mask:
                setp(x, y, 'leaf_ol')
            elif (x - 1, y) not in mask or (x, y - 1) not in mask:
                setp(x, y, 'leaf_dk')
    objects.append((by, draw))


def pine(bx, by, s=1.0):
    shadows.append((bx + 6 * s, by + 1, 10 * s, 4 * s))

    def draw():
        for y in range(by - 6, by):
            for x in range(bx - 2, bx + 2):
                setp(x, y, 'trunk_dk' if x >= bx else 'trunk')
        tiers = [(by - 6, 11), (by - 14, 9), (by - 21, 7), (by - 27, 4)]
        for (ty, half) in tiers:
            h = int(half * 1.1 * s) + 3
            for r in range(h):
                w = int((r + 1) / h * half * s)
                y = ty - h + r
                for dx in range(-w, w + 1):
                    if dx == w or r == h - 1:
                        c = 'leaf_ol'
                    elif dx < -w // 3:
                        c = 'pine_lt' if (dx + y) % 3 else 'pine'
                    elif dx < w // 3:
                        c = 'pine'
                    else:
                        c = 'pine_dk'
                    setp(bx + dx, y, c)
    objects.append((by, draw))


def bush(bx, by):
    shadows.append((bx + 4, by, 8, 3))

    def draw():
        for (ox, oy, r) in [(-4, -3, 4), (4, -3, 4), (0, -5, 5)]:
            for y in range(by + oy - r, by + oy + r + 1):
                for x in range(bx + ox - r, bx + ox + r + 1):
                    nx, ny = (x - bx - ox) / r, (y - by - oy) / r
                    if nx * nx + ny * ny <= 1:
                        v = -(0.6 * nx + 0.8 * ny) * 0.5 + 0.5 + (BAYER[y % 4, x % 4] - 0.5) * 0.3 * DA
                        setp(x, y, ['leaf_dk', 'leaf', 'leaf_lt'][int(np.clip(v * 3, 0, 2))])
        for (x, y) in [(bx - 2, by - 6), (bx + 3, by - 4), (bx - 5, by - 3)]:
            setp(x, y, 'flower_b')
    objects.append((by, draw))


def rock(bx, by, w=7, h=5):
    shadows.append((bx + 3, by, w * 0.8, 2))

    def draw():
        for y in range(by - h, by):
            for x in range(bx - w // 2, bx + w // 2 + 1):
                nx, ny = (x - bx) / (w / 2 + 0.5), (y - (by - h / 2)) / (h / 2 + 0.5)
                if nx * nx + ny * ny <= 1:
                    v = -(0.6 * nx + 0.8 * ny)
                    setp(x, y, 'stone_lt' if v > 0.25 else ('stone' if v > -0.35 else 'stone_dk'))
    objects.append((by, draw))


def house(x0, y0):
    W_, H_ = 64, 48
    for y in range(y0 + 30, y0 + H_ + 3):
        for x in range(x0 + W_ - 2, x0 + W_ + 5 - max(0, y - y0 - H_)):
            if x < x0 + W_ + 2:
                shade(x, y, 0.72)
            elif (x + y) % 2 == 0:
                shade(x, y, 0.84)
    for x in range(x0 + 2, x0 + W_ + 6):
        for y in (y0 + H_, y0 + H_ + 1):
            shade(x, y, 0.7)

    def draw():
        # walls (timber frame)
        for y in range(y0 + 28, y0 + H_):
            for x in range(x0 + 2, x0 + W_ - 2):
                c = 'wall' if x < x0 + 40 else 'wall_sh'
                if x in (x0 + 2, x0 + 3, x0 + 31, x0 + 32, x0 + W_ - 4, x0 + W_ - 3) or y in (y0 + 38, y0 + H_ - 1):
                    c = 'beam'
                setp(x, y, c)
        for x in range(x0 + 2, x0 + W_ - 2):
            setp(x, y0 + 28, 'roof_ln'); setp(x, y0 + 29, 'beam')
            shade(x, y0 + 30, 0.8)
        # door
        for y in range(y0 + 33, y0 + H_):
            for x in range(x0 + 27, x0 + 37):
                c = 'door' if (x - x0) % 3 else 'door_lt'
                if x in (x0 + 27, x0 + 36) or y == y0 + 33:
                    c = 'beam'
                setp(x, y, c)
        setp(x0 + 34, y0 + 41, 'gold')
        # windows
        for wx in (x0 + 9, x0 + 45):
            for y in range(y0 + 31, y0 + 37):
                for x in range(wx, wx + 9):
                    c = 'glass'
                    if x in (wx, wx + 8) or y in (y0 + 31, y0 + 36):
                        c = 'beam'
                    elif x == wx + 4 or y == y0 + 33:
                        c = 'beam'
                    elif (x - wx) + (y - y0 - 31) <= 3:
                        c = 'glass_lt'
                    setp(x, y, c)
            for x in range(wx - 1, wx + 10):
                setp(x, y0 + 37, 'wood_dk')
        for x in range(x0 + 8, x0 + 19):
            setp(x, y0 + 38, 'wood')
            setp(x, y0 + 37, ['flower_b', 'leaf', 'flower_c', 'leaf_lt'][x % 4])
        # roof
        for y in range(y0, y0 + 28):
            inset = max(0, 6 - y + y0) if y < y0 + 6 else 0
            for x in range(x0 - 2 + inset, x0 + W_ + 2 - inset):
                back = y < y0 + 10
                c = ('roof_lt' if x < x0 + 30 else 'roof') if back else ('roof' if x < x0 + 30 else 'roof_dk')
                if (y - y0) % 4 == 3:
                    c = 'roof_ln'
                elif (x + ((y - y0) // 4) * 3) % 7 == 0:
                    c = 'roof_dk' if not back else 'roof'
                if y == y0 + 10:
                    c = 'roof_ln'
                if x in (x0 - 2 + inset, x0 + W_ + 1 - inset) or y == y0:
                    c = 'ink'
                setp(x, y, c)
        for x in range(x0 - 2, x0 + W_ + 2):
            setp(x, y0 + 27, 'ink')
        # chimney
        sprite(x0 + 46, y0 - 6, ['kkkkkkk', 'sslssdk', 'slssdsk', 'sssldsk', 'slssssk', 'ssssdsk'],
               {'k': 'ink', 's': 'stone', 'l': 'stone_lt', 'd': 'stone_dk'})
        sprite(x0 + 47, y0 - 10, ['.cc.', 'cccc', '.cc.'], {'c': 'cream'})
    objects.append((y0 + H_, draw))


def barrel(bx, by):
    shadows.append((bx + 3, by, 5, 2))
    objects.append((by, lambda: sprite(bx - 4, by - 11, [
        '.kkkkkk.', 'kwwlwwdk', 'kiiiiiik', 'kwlwwwdk', 'kwlwwwdk', 'kiiiiiik',
        'kwlwwwdk', 'kwlwwwdk', 'kiiiiiik', 'kwwlwwdk', '.kkkkkk.'],
        {'k': 'ink', 'w': 'wood', 'l': 'wood_lt', 'd': 'wood_dk', 'i': 'iron'})))


def crate(bx, by):
    shadows.append((bx + 4, by, 7, 2))
    objects.append((by, lambda: sprite(bx - 5, by - 10, [
        'kkkkkkkkkk', 'kllllllllk', 'klwwwwwwdk', 'kwdwwwwdwk', 'kwwdwwdwwk', 'kwwwddwwwk',
        'kwwdwwdwwk', 'kwdwwwwdwk', 'kddddddddk', 'kkkkkkkkkk'],
        {'k': 'ink', 'w': 'wood', 'l': 'wood_lt', 'd': 'wood_dk'})))


def logs(bx, by):
    shadows.append((bx + 6, by, 12, 3))
    objects.append((by, lambda: sprite(bx - 12, by - 12, [
        '.....kkkk.kkkk.......', '....kllldklllk.......', '....klrldklrlk.......',
        '..kkkllldkkllldkkk...', '.klllkkkklllkkklllk..', '.klrlddk.klrldklrldk.',
        '.klllddk.kllldklllddk', '..kkkkk...kkkk.kkkkk.', '.....................'],
        {'k': 'ink', 'l': 'wood_lt', 'r': 'trunk', 'd': 'wood_dk'})))


def signpost(bx, by):
    shadows.append((bx + 3, by, 4, 2))
    objects.append((by, lambda: sprite(bx - 2, by - 16, [
        'kkkkkkkkkk..', 'kllllllllkk.', 'klwwdwwwwwlk', 'kwwwwwwwwwdk', 'kddddddddkk.',
        'kkkkddkkkk..', '....dd......', '....dd......', '....dd......', '....dd......',
        '....dd......', '....dd......', '....dd......', '...dddd.....', '...kkkk.....', '............'],
        {'k': 'ink', 'w': 'wood', 'l': 'wood_lt', 'd': 'wood_dk'})))


def lantern(bx, by):
    shadows.append((bx + 3, by, 3, 1.5))
    objects.append((by, lambda: sprite(bx - 3, by - 22, [
        '..kkk..', '.kiiik.', 'kiggyik', 'kigyyik', 'kiyyyik', '.kiiik.', '..kik..',
        '...i...', '...i...', '...i...', '...i...', '...i...', '...i...', '...i...', '...i...',
        '...i...', '...i...', '...i...', '...i...', '..iii..', '.iiiii.', '.kkkkk.'],
        {'k': 'ink', 'i': 'iron', 'g': 'cream', 'y': 'glow'})))


def fence(x0, x1, y):
    def draw():
        for x in range(x0, x1):
            setp(x, y - 6, 'wood_lt'); setp(x, y - 5, 'wood_dk')
            setp(x, y - 3, 'wood_lt'); setp(x, y - 2, 'wood_dk')
        for x in range(x0, x1, 10):
            sprite(x, y - 9, ['ll', 'lw', 'lw', 'lw', 'lw', 'lw', 'lw', 'lw', 'dd'],
                   {'l': 'wood_lt', 'w': 'wood', 'd': 'wood_dk'})
            shade(x + 2, y, 0.7); shade(x + 3, y, 0.7)
    objects.append((y, draw))


def bridge(x0, x1, y0, y1):
    def draw():
        for x in range(x0, x1):
            for y in (y1, y1 + 1, y1 + 2):
                if fresh[y, x]:
                    shade(x, y, 0.62 if y < y1 + 2 or x % 2 else 0.8)
        for y in range(y0, y1):
            for x in range(x0, x1):
                c = 'wood' if (x - x0) % 4 else 'wood_dk'
                if (x - x0) % 4 == 1:
                    c = 'wood_lt'
                if y in (y0, y1 - 1):
                    c = 'wood_dk'
                setp(x, y, c)
        for x in range(x0 - 1, x1 + 1):
            setp(x, y0 - 3, 'wood_lt'); setp(x, y0 - 2, 'wood_dk')
            setp(x, y1 + 1, 'wood_lt'); setp(x, y1 + 2, 'wood_dk')
        for x in (x0 - 1, x0 + 17, x1 - 1):
            sprite(x, y0 - 5, ['ll', 'lw', 'lw', 'dd'], {'l': 'wood_lt', 'w': 'wood', 'd': 'wood_dk'})
            sprite(x, y1 - 1, ['ll', 'lw', 'lw', 'dd'], {'l': 'wood_lt', 'w': 'wood', 'd': 'wood_dk'})
    return draw


def rowboat(bx, by):
    def draw():
        for y in range(by - 5, by + 6):
            for x in range(bx - 12, bx + 13):
                d = ((x - bx) / 12.5) ** 2 + ((y - by) / 5.5) ** 2
                if d <= 1:
                    c = 'wood_dk' if d > 0.7 else ('trunk' if d > 0.45 else 'wood')
                    if d <= 0.45 and (x - bx) % 6 == 0:
                        c = 'wood_lt'
                    setp(x, y, c)
        for x in range(bx - 12, bx + 13):
            if sea[min(by + 6, HH - 1), x]:
                setp(x, by + 6, 'sea_dp')
        for k in range(10):
            setp(bx + 4 + k, by - 6 - k // 2, 'wood_lt')
    objects.append((by + 6, draw))


def jetty(x0, y0, y1):
    def draw():
        for y in range(y0, y1):
            for x in range(x0, x0 + 14):
                c = 'wood' if (y - y0) % 4 else 'wood_dk'
                if (y - y0) % 4 == 1:
                    c = 'wood_lt'
                setp(x, y, c)
            setp(x0 + 14, y, 'sea_dp'); setp(x0 + 15, y, 'sea_dp')
        for y in range(y0 + 2, y1, 8):
            for x in (x0 - 1, x0 + 14):
                sprite(x, y, ['k', 'k', 'k'], {'k': 'trunk_dk'})
    objects.append((y0, draw))


PLAYER = [
    '......oppo......',
    '.....occcCo.....',
    '....occwcCCo....',
    '...occccccCCo...',
    '..obbbbbbbbBBo..',
    '...ohssssssho...',
    '...ohessseShho..',
    '...oqsssssSqo...',
    '....osssssSo....',
    '...orrrrrrRRo...',
    '..ozrrrrrrRRzo..',
    '.oszlzzzgzzZZso.',
    '.oSozzzgzzzZoSo.',
    '..ozzzgzzzzZZo..',
    '...ottttttTTo...',
    '...ott.oTTTo....',
    '...ott..oTo.....',
    '..okkko.okko....',
    '..oooo...ooo....',
]
for row in PLAYER:
    assert len(row) == 16, (row, len(row))
PPAL = {'o': 'ink', 'p': 'pom', 'c': 'cap', 'C': 'cap_dk', 'w': 'pom', 'b': 'brim', 'B': 'cap_dk',
        'h': 'hair', 's': 'skin', 'S': 'skin_sh', 'e': 'eye', 'q': 'blush', 'r': 'scarf', 'R': 'scarf_dk',
        'z': 'coat', 'Z': 'coat_dk', 'l': 'coat_lt', 'g': 'strap', 't': 'pants', 'T': 'pants_dk', 'k': 'boot'}


PLAYER_TALL = [
    '......oooo......',
    '.....owwwwo.....',
    '....occccccCo...',
    '...occcwcccCCo..',
    '...obbbbbbbbBo..',
    '...ohsssssssho..',
    '...osessssesSo..',
    '...osqsssssqSo..',
    '....ossssssSo...',
    '.....oSSSSSo....',
    '....orrrrrrRo...',
    '...ozrrrrrrRRo..',
    '..ozzlzzzzgzZZo.',
    '.oszzlzzzgzzZZso',
    '.oszzlzzgzzzZZso',
    '.oSozlzgzzzzZoSo',
    '..oozzgzzzzzZoo.',
    '...ozgzzzzzZZo..',
    '...ottttttTTo...',
    '...otto.oTTo....',
    '...otto.oTTo....',
    '...otto..oTo....',
    '..okkko.okko....',
    '..ooooo.oooo....',
]
for row in PLAYER_TALL:
    assert len(row) == 16, (row, len(row))


def player(cx, feet_y):
    spr = PLAYER_TALL if OPTS.get('hero') == 'tall' else PLAYER
    shadows.append((cx + 1, feet_y, 6, 2))
    objects.append((feet_y, lambda: sprite(cx - 8, feet_y - len(spr) + 1, spr, PPAL)))


def shack(x0, y0, w, h):
    for y in range(y0 + 14, y0 + h + 2):
        for x in range(x0 + w, x0 + w + 5):
            if x < x0 + w + 3 or (x + y) % 2 == 0:
                shade(x, y, 0.7)
    for x in range(x0 + 2, x0 + w + 4):
        shade(x, y0 + h, 0.72)

    def draw():
        rh = 12
        for y in range(y0 + rh, y0 + h):
            for x in range(x0, x0 + w):
                k = (x - x0) % 5
                c = 'plank_lt' if k == 0 else ('plank_dk' if k == 4 else 'plank')
                if x in (x0, x0 + w - 1) or y == y0 + h - 1:
                    c = 'ink'
                setp(x, y, c)
        dx0 = x0 + w // 2 - 5
        for y in range(y0 + h - 16, y0 + h - 1):
            for x in range(dx0, dx0 + 10):
                setp(x, y, 'ink' if x in (dx0, dx0 + 9) or y == y0 + h - 16 else 'door')
        setp(dx0 + 7, y0 + h - 8, 'gold')
        wx = x0 + 6
        for y in range(y0 + rh + 4, y0 + rh + 11):
            for x in range(wx, wx + 9):
                c = 'glass' if (x - wx) + (y - y0 - rh - 4) > 3 else 'glass_lt'
                if x in (wx, wx + 8) or y in (y0 + rh + 4, y0 + rh + 10) or x == wx + 4:
                    c = 'ink'
                setp(x, y, c)
        for y in range(y0, y0 + rh):
            for x in range(x0 - 3, x0 + w + 3):
                k = (x - x0) % 3
                c = 'tin_lt' if k == 0 else ('tin' if k == 1 else 'tin_dk')
                if y == y0 or x in (x0 - 3, x0 + w + 2) or y == y0 + rh - 1:
                    c = 'ink'
                elif (x * 7 + y * 3) % 29 == 0:
                    c = 'rtop_dk'
                setp(x, y, c)
    objects.append((y0 + h, draw))


def ladder(x, ytop, ybot):
    def draw():
        for y in range(ytop, ybot):
            setp(x, y, 'plank_lt'); setp(x + 1, y, 'plank_dk')
            setp(x + 7, y, 'plank_lt'); setp(x + 8, y, 'plank_dk')
            if (y - ytop) % 4 == 2:
                for xx in range(x + 2, x + 7):
                    setp(xx, y, 'plank_lt')
            shade(x + 9, y, 0.75)
    objects.append((ybot, draw))


def mine_frame(x0, x1, ytop, ybot):
    def draw():
        for y in range(ytop, ybot):
            for x in (x0 - 3, x0 - 2, x0 - 1, x1 + 1, x1 + 2, x1 + 3):
                c = 'plank_lt' if x in (x0 - 3, x1 + 1) else ('plank_dk' if x in (x0 - 1, x1 + 3) else 'plank')
                setp(x, y, c)
        for y in range(ytop - 4, ytop):
            for x in range(x0 - 5, x1 + 6):
                setp(x, y, 'plank_lt' if y == ytop - 4 else ('plank_dk' if y == ytop - 1 else 'plank'))
        sprite((x0 + x1) // 2 - 1, ytop, ['.i.', 'kyk', 'kyk', '.k.'], {'k': 'iron', 'i': 'iron', 'y': 'glow'})
    objects.append((ybot, draw))


def water_tower(cx, by):
    shadows.append((cx + 12, by + 1, 16, 4))

    def draw():
        legs_top = by - 30
        for y in range(legs_top, by):
            for x in (cx - 12, cx - 11, cx + 10, cx + 11, cx - 4, cx + 3):
                setp(x, y, 'plank_dk' if x in (cx + 11, cx + 3) else 'plank')
        for k in range(22):
            setp(cx - 11 + k, legs_top + 6 + k // 2, 'plank_dk')
            setp(cx + 11 - k, legs_top + 6 + k // 2, 'plank_dk')
        tank_top = legs_top - 22
        for y in range(tank_top, legs_top + 1):
            for x in range(cx - 14, cx + 15):
                c = 'plank_lt' if x < cx - 6 else ('plank' if x < cx + 7 else 'plank_dk')
                if (x - cx + 14) % 4 == 0:
                    c = 'plank_dk'
                if (y - tank_top) in (4, 16):
                    c = 'iron'
                if x in (cx - 14, cx + 14) or y == legs_top:
                    c = 'ink'
                setp(x, y, c)
        for r in range(9):
            w = 2 + r * 2
            for x in range(cx - w, cx + w + 1):
                c = 'tin_lt' if x < cx - 2 else ('tin' if x < cx + 3 else 'tin_dk')
                if x in (cx - w, cx + w) or r == 8:
                    c = 'ink'
                setp(x, tank_top - 9 + r, c)
    objects.append((by, draw))


def minecart(cx, by):
    shadows.append((cx + 4, by + 1, 12, 2))

    def draw():
        top = by - 13
        for (ox, hgt) in [(-8, 1), (-6, 2), (-4, 3), (-2, 3), (0, 4), (2, 3), (4, 2), (6, 2), (8, 1)]:
            for k in range(hgt):
                setp(cx + ox, top - k, 'ore_lt' if k == hgt - 1 else 'ore')
                setp(cx + ox + 1, top - k, 'ore' if k == hgt - 1 else 'face_dk')
        for y in range(top, by - 3):
            inset = (y - top) // 4
            for x in range(cx - 11 + inset, cx + 11 - inset):
                c = 'tin' if x < cx + 3 else 'tin_dk'
                if y == top:
                    c = 'tin_lt'
                if (x - cx) % 7 == 0 and top < y < by - 4:
                    c = 'iron'
                if x in (cx - 11 + inset, cx + 10 - inset) or y == by - 4:
                    c = 'ink'
                setp(x, y, c)
        for wx in (cx - 7, cx + 6):
            sprite(wx - 2, by - 4, ['.kk.', 'kiik', 'kiik', '.kk.'], {'k': 'ink', 'i': 'iron'})
    objects.append((by, draw))


def ore_pile(cx, by):
    shadows.append((cx + 3, by, 8, 2))

    def draw():
        for (ox, oy, r) in [(-4, -3, 3), (3, -3, 3), (0, -5, 3), (-1, -2, 2)]:
            for y in range(by + oy - r, by + oy + r + 1):
                for x in range(cx + ox - r, cx + ox + r + 1):
                    nx, ny = (x - cx - ox) / r, (y - by - oy) / r
                    if nx * nx + ny * ny <= 1:
                        v = -(0.6 * nx + 0.8 * ny)
                        setp(x, y, 'ore_lt' if v > 0.3 else ('ore' if v > -0.3 else 'face_dk'))
    objects.append((by, draw))


def dry_shrub(cx, by):
    shadows.append((cx + 3, by, 6, 2))
    objects.append((by, lambda: sprite(cx - 4, by - 6, [
        '..l..l...', 'l.dl.d.l.', '.dl.ldd..', '..ddldl.l', '.dddddld.', '..ddddd..', '...ttt...'],
        {'l': 'shrub_lt', 'd': 'shrub', 't': 'trunk_dk'})))
# ------------------------------------------------------------------ redrawn objects (ART 2)
def _window(wx, wy, ww, wh, shutters=True):
    for y in range(wy, wy + wh):
        for x in range(wx, wx + ww):
            edge = x in (wx, wx + ww - 1) or y in (wy, wy + wh - 1)
            mull = x == wx + ww // 2 or y == wy + wh // 2
            d = (x - wx) + (y - wy)
            c = 'beam' if edge or mull else ('glass_lt' if d <= 3 or d == 6 else 'glass')
            setp(x, y, c)
    for x in range(wx - 1, wx + ww + 1):
        setp(x, wy + wh, 'wood_lt'); setp(x, wy + wh + 1, 'wood_dk')
    if shutters:
        for sx in (wx - 4, wx + ww + 1):
            for y in range(wy, wy + wh):
                for x in range(sx, sx + 3):
                    c = 'shut_dk' if (y - wy) % 2 == 1 or x == sx + 2 else 'shut'
                    setp(x, y, c)


def house_v2(x0, y0):
    """boatwright's cottage: shingled roof with dormer, clapboard walls, shutters, stone base"""
    W_ = 64
    RT, RB = y0, y0 + 27
    WT, WB = y0 + 26, y0 + 49
    for y in range(WT + 2, WB + 3):
        for x in range(x0 + W_, x0 + W_ + 7):
            if x < x0 + W_ + 3:
                shade(x, y, 0.7)
            elif (x + y) % 2 == 0:
                shade(x, y, 0.82)
    for x in range(x0 + 1, x0 + W_ + 3):
        shade(x, WB + 1, 0.72)
        if (x + WB) % 2 == 0:
            shade(x, WB + 2, 0.84)

    def draw():
        for y in range(WT, WB - 2):                       # clapboard walls
            band = (y - WT) % 3
            for x in range(x0, x0 + W_):
                right = x >= x0 + int(W_ * 0.72)
                c = ('wall' if band < 2 else 'wall_sh') if not right else ('wall_sh' if band < 2 else 'wall_dk')
                setp(x, y, c)
            for x, c in ((x0, 'ink'), (x0 + 1, 'beam'), (x0 + 2, 'wood'),
                         (x0 + W_ - 3, 'beam'), (x0 + W_ - 2, 'wood_dk'), (x0 + W_ - 1, 'ink')):
                setp(x, y, c)
        for y in range(WB - 2, WB + 1):                   # stone foundation
            for x in range(x0, x0 + W_):
                off = 3 if y == WB - 1 else 0
                c = 'stone_lt' if y == WB - 2 else 'stone'
                if (x - x0 + off) % 6 == 0:
                    c = 'stone_dk'
                if y == WB or x in (x0, x0 + W_ - 1):
                    c = 'ink'
                setp(x, y, c)
        _window(x0 + 9, WT + 8, 12, 9)                    # left window, shutters + flower box
        for x in range(x0 + 7, x0 + 23):
            setp(x, WT + 19, ['flower_b', 'leaf', 'flower_c', 'leaf_lt', 'flower_a'][x % 5])
            setp(x, WT + 20, 'wood'); setp(x, WT + 21, 'wood_dk')
        _window(x0 + 51, WT + 8, 9, 9, shutters=False)
        dx0, dy0 = x0 + 37, WT + 7                        # door with awning + step + lamp
        for y in range(dy0, WB - 2):
            for x in range(dx0, dx0 + 10):
                c = 'door' if (x - dx0) % 3 else 'door_lt'
                if x in (dx0, dx0 + 9) or y == dy0:
                    c = 'beam'
                setp(x, y, c)
        setp(dx0 + 7, dy0 + 8, 'gold')
        for y in range(dy0 - 4, dy0):
            for x in range(dx0 - 3, dx0 + 13):
                c = 'roof_lt' if y == dy0 - 4 else ('roof' if y < dy0 - 1 else 'roof_ln')
                if x in (dx0 - 3, dx0 + 12):
                    c = 'ink'
                setp(x, y, c)
        for x in range(dx0 - 2, dx0 + 12):
            shade(x, dy0, 0.75)
        sprite(dx0 + 13, dy0 + 1, ['.k.', 'kyk', 'kyk', '.k.'], {'k': 'iron', 'y': 'glow'})
        for y, c in ((WB + 1, 'stone_lt'), (WB + 2, 'stone_dk')):
            for x in range(dx0 - 2, dx0 + 12):
                setp(x, y, c)
        for y in range(RT, RB + 1):                       # shingled roof
            r = y - RT
            for x in range(x0 - 3, x0 + W_ + 3):
                shadow_side = x >= x0 + int(W_ * 0.72)
                if r == 0:
                    c = 'ink'
                elif r == 1:
                    c = 'roof_lt'
                elif r == 2:
                    c = 'roof_ln'
                elif y == RB:
                    c = 'ink'
                elif y == RB - 1:
                    c = 'roof_ln'
                else:
                    rr, ln = (r - 3) // 4, (r - 3) % 4
                    off = 3 if rr % 2 else 0
                    if ln == 0:
                        c = 'roof' if shadow_side else 'roof_lt'
                    elif ln == 3:
                        c = 'roof_ln'
                    else:
                        c = 'roof_dk' if shadow_side else 'roof'
                    if ln in (1, 2) and (x + off) % 6 == 0:
                        c = 'roof_ln'
                if x in (x0 - 3, x0 + W_ + 2):
                    c = 'ink'
                elif x in (x0 - 2, x0 + W_ + 1) and 0 < r < RB - RT:
                    c = 'wood_dk'
                setp(x, y, c)
        d0, dw = x0 + 10, 14                              # dormer
        dtop, dwt, dwb = RT + 4, RT + 13, RT + 23
        for y in range(dwt, dwb):
            for x in range(d0, d0 + dw):
                c = 'wall' if x < d0 + dw - 4 else 'wall_sh'
                if x in (d0, d0 + dw - 1) or y == dwb - 1:
                    c = 'ink'
                setp(x, y, c)
        _window(d0 + 4, dwt + 2, 6, 6, shutters=False)
        for y in range(dwt, dwb):
            shade(d0 + dw, y, 0.7); shade(d0 + dw + 1, y, 0.8)
        dcx = d0 + dw // 2
        for r in range(dwt + 2 - dtop):
            y, half = dtop + r, r + 1
            for x in range(dcx - half, dcx + half + 1):
                c = 'roof_lt' if x < dcx else ('roof' if x == dcx else 'roof_dk')
                if x in (dcx - half, dcx + half) or r == dwt + 1 - dtop:
                    c = 'ink'
                setp(x, y, c)
        cx0 = x0 + 46                                     # chimney + smoke
        for y in range(RT - 8, RT + 9):
            for x in range(cx0, cx0 + 8):
                c = 'stone_lt' if x < cx0 + 3 else ('stone' if x < cx0 + 6 else 'stone_dk')
                if (y - RT) % 3 == 0 or (x - cx0 + (2 if ((y - RT) // 3) % 2 else 0)) % 4 == 0:
                    c = 'stone_dk'
                if x in (cx0, cx0 + 7):
                    c = 'ink'
                setp(x, y, c)
        for x in range(cx0 - 1, cx0 + 9):
            setp(x, RT - 9, 'ink'); setp(x, RT - 8, 'stone_lt')
        for y in range(RT, RT + 9):
            shade(cx0 + 8, y, 0.7); shade(cx0 + 9, y, 0.82)
        for (sx, sy, rows) in [(cx0 + 2, RT - 14, ['.cc.', 'cccs', '.ss.']), (cx0 + 5, RT - 19, ['.c.', 'ccs', '.s.']),
                               (cx0 + 2, RT - 23, ['cc', 'cs'])]:
            sprite(sx, sy, rows, {'c': 'cream', 's': 'wall_sh'})
    objects.append((WB + 2, draw))


def bridge_v2(x0, x1, y0, y1):
    def draw():
        for x in range(x0, x1):
            for y in range(y1 + 3, y1 + 7):
                if fresh[y, x] and (y < y1 + 6 or (x + y) % 2 == 0):
                    shade(x, y, 0.65 if y < y1 + 5 else 0.8)
        for px in (x0 + 5, x0 + 18, x1 - 8):              # pilings
            for y in range(y1 + 3, y1 + 8):
                setp(px, y, 'trunk'); setp(px + 1, y, 'trunk_dk'); setp(px + 2, y, 'trunk_dk')
            setp(px - 1, y1 + 8, 'river_hi'); setp(px + 3, y1 + 8, 'river_hi')
        for y in range(y0, y1):                           # deck boards
            for x in range(x0, x1):
                k = (x - x0) % 4
                c = 'wood_lt' if k == 0 else ('wood_dk' if k == 3 else 'wood')
                if k == 2 and ((x - x0) // 4) % 3 == 1 and (y - y0) % 5 == 2:
                    c = 'wood_dk'                         # nail heads / knots
                setp(x, y, c)
        for x in range(x0 - 1, x1 + 1):                   # deck edge (thickness)
            setp(x, y1, 'wood_dk'); setp(x, y1 + 1, 'trunk'); setp(x, y1 + 2, 'ink')

        def rail(yb):
            for x in range(x0 - 1, x1 + 1):
                setp(x, yb - 5, 'wood_lt'); setp(x, yb - 4, 'wood_dk')
            for px in (x0 - 1, x0 + (x1 - x0) // 2 - 1, x1 - 2):
                for y in range(yb - 7, yb + 1):
                    for i, c in enumerate(('wood_lt', 'wood', 'wood_dk')):
                        setp(px + i, y, c)
                setp(px + 1, yb - 8, 'wood_lt')
        rail(y0 + 1)
        rail(y1 + 1)
    return draw


def fence_v2(x0, x1, y):
    def draw():
        for (ry, sag) in ((y - 8, 0), (y - 4, 1)):
            for x in range(x0, x1):
                s_ = int(round(sag * np.sin(np.pi * ((x - x0) % 14) / 14)))
                setp(x, ry + s_, 'wood_lt'); setp(x, ry + s_ + 1, 'wood_dk')
        for px in range(x0, x1, 14):
            for yy in range(y - 11, y + 1):
                for i, c in enumerate(('wood_lt', 'wood', 'wood_dk')):
                    setp(px + i, yy, c)
            setp(px + 1, y - 12, 'wood_lt')
            shade(px + 3, y, 0.7); shade(px + 4, y, 0.8); shade(px + 3, y - 1, 0.8)
    objects.append((y, draw))


BARREL = ['..kkkkkk..', '.kttttTTk.', 'kitttttTik', 'kiiiiiiiik', 'kWwwdwwdDk', 'kWwwdwwdDk',
          'kIiiiiiiik', 'kWwwdwwdDk', 'kWwwdwwdDk', 'kIiiiiiiik', 'kWwwdwwdDk', '.kwwdwwdk.', '..kkkkkk..']


def barrel_v2(bx, by):
    shadows.append((bx + 4, by, 6, 2))
    objects.append((by, lambda: sprite(bx - 5, by - 12, BARREL, {
        'k': 'ink', 't': 'wood_lt', 'T': 'wood', 'i': 'iron', 'I': 'tin_lt', 'W': 'wood_lt', 'w': 'wood',
        'd': 'wood_dk', 'D': 'trunk_dk'})))


def logs_v2(bx, by):
    shadows.append((bx + 8, by, 14, 3))
    ends = [(-8, -4), (0, -4), (8, -4), (-4, -11), (4, -11)]

    def draw():
        for (ox, oy) in sorted(ends, key=lambda e: e[1]):
            for y in range(by + oy - 7, by + oy):
                for x in range(bx + ox - 4, bx + ox + 5):
                    c = 'trunk_lt' if x < bx + ox - 1 else ('trunk' if x < bx + ox + 3 else 'trunk_dk')
                    if x in (bx + ox - 4, bx + ox + 4) or y == by + oy - 7:
                        c = 'ink'
                    setp(x, y, c)
        for (ox, oy) in sorted(ends, key=lambda e: e[1]):
            cx_, cy_ = bx + ox, by + oy
            for y in range(cy_ - 4, cy_ + 5):
                for x in range(cx_ - 4, cx_ + 5):
                    d = ((x - cx_) ** 2 + (y - cy_) ** 2) ** 0.5
                    if d > 4.5:
                        continue
                    c = 'ink' if d > 3.8 else ('trunk' if d > 3.0 else ('wood_lt' if d > 0.7 else 'wood_dk'))
                    if 1.6 < d < 2.3:
                        c = 'wood'
                    setp(x, y, c)
    objects.append((by, draw))


def rowboat_v2(bx, by):
    def draw():
        x0 = bx - 15

        def half(i):
            return min(5, 3 + i) if i < 20 else max(1, round(5 * (29 - i) / 9))
        for i in range(30):
            h = half(i)
            for dy in (h + 1, h + 2):
                if by + dy < HH and sea[by + dy, x0 + i] and (dy == h + 1 or (i + dy) % 2 == 0):
                    shade(x0 + i, by + dy, 0.7)
        for i in range(30):
            h = half(i)
            for dy in range(-h, h + 1):
                a = abs(dy)
                if a == h or i == 0:
                    c = 'ink'
                elif a == h - 1:
                    c = 'wood_lt' if dy < 0 else 'wood_dk'
                else:
                    c = 'trunk'
                    if i in (9, 10, 18, 19):
                        c = 'wood_lt' if i in (9, 18) else 'wood'
                    elif dy == 0:
                        c = 'trunk_dk'
                setp(x0 + i, by + dy, c)
        for k in range(12):
            setp(x0 + 13 - k, by - 1 - k // 2, 'wood_lt')
        sprite(x0, by - 9, ['ww', 'ww', 'dd'], {'w': 'wood', 'd': 'wood_dk'})
        setp(x0 + 30, by, 'foam'); setp(x0 + 30, by - 1, 'foam'); setp(x0 + 31, by + 1, 'foam')
    objects.append((by + 6, draw))


def jetty_v2(x0, y0, y1):
    def draw():
        for y in range(y0, y1):
            k = (y - y0) % 4
            for x in range(x0, x0 + 16):
                c = 'wood_lt' if k == 0 else ('wood_dk' if k == 3 else 'wood')
                if x in (x0, x0 + 15):
                    c = 'ink'
                setp(x, y, c)
            for x in (x0 + 16, x0 + 17, x0 + 18):
                if 0 <= y < HH and sea[y, x] and (x < x0 + 18 or y % 2 == 0):
                    shade(x, y, 0.7)
        for py in range(y0 + 4, y1, 10):
            for px in (x0 - 2, x0 + 15):
                sprite(px, py - 3, ['lll', 'ttd', 'ttd', 'ttd'], {'l': 'wood_lt', 't': 'trunk', 'd': 'trunk_dk'})
    objects.append((y0, draw))


SIGN_PICK = ['kkkkkkkkkkkkk', 'klliiiiiiillk', 'kllllldlllllk', 'kllllldlllllk', 'kkkkkkkkkkkkk']
SIGN_CROSS = ['kkkkkkkkkkkkk', 'kliilllllliik', 'kllldllldlllk', 'klllldldllllk', 'kllllldlllllk',
              'klllldldllllk', 'kkkkkkkkkkkkk']


def shack_v2(x0, y0, w, h):
    """miner's cabin: corrugated lean-to roof, weathered boards, Z-brace door, porch, stovepipe"""
    rh, base = 14, y0 + h
    for y in range(y0 + rh, base + 5):
        for x in range(x0 + w + 1, x0 + w + 7):
            if x < x0 + w + 4:
                shade(x, y, 0.7)
            elif (x + y) % 2 == 0:
                shade(x, y, 0.84)
    for x in range(x0 - 1, x0 + w + 3):
        shade(x, base + 5, 0.72)

    def draw():
        for y in range(base, base + 5):                   # porch boards
            for x in range(x0 - 2, x0 + w + 2):
                k = (y - base) % 3
                c = 'plank_lt' if k == 0 else ('plank' if k == 1 else 'plank_dk')
                if x in (x0 - 2, x0 + w + 1) or y == base + 4:
                    c = 'ink'
                setp(x, y, c)
        for y in range(y0 + rh - 2, base):                # weathered vertical boards
            for x in range(x0, x0 + w):
                k, board = (x - x0) % 4, (x - x0) // 4
                c = 'plank_lt' if k == 0 else ('plank_dk' if k == 3 else 'plank')
                if board % 3 == 2 and k in (1, 2) and (y * 3 + board) % 11 == 0:
                    c = 'plank_dk'
                if x in (x0, x0 + w - 1):
                    c = 'ink'
                setp(x, y, c)
        dx0, dy0 = x0 + w // 2 - 6, base - 17             # Z-brace door
        for y in range(dy0, base):
            for x in range(dx0, dx0 + 12):
                c = 'plank' if (x - dx0) % 3 else 'plank_lt'
                if x in (dx0, dx0 + 11) or y == dy0:
                    c = 'ink'
                elif y in (dy0 + 2, base - 3):
                    c = 'plank_dk'
                setp(x, y, c)
        n = base - 3 - (dy0 + 2)
        for k in range(n):
            setp(dx0 + 2 + int(k * 7 / n), base - 4 - k, 'plank_lt')
        setp(dx0 + 9, dy0 + 9, 'iron')
        sprite(dx0 - 1, dy0 - 7, SIGN_PICK, {'k': 'ink', 'l': 'plank_lt', 'i': 'iron', 'd': 'plank_dk'})
        wx, wy = x0 + 5, y0 + rh + 4                      # window + crooked shutter
        for y in range(wy, wy + 8):
            for x in range(wx, wx + 9):
                c = 'glass' if (x - wx) + (y - wy) > 4 else 'glass_lt'
                if x in (wx, wx + 8) or y in (wy, wy + 7) or x == wx + 4:
                    c = 'ink'
                setp(x, y, c)
        for y in range(wy + 1, wy + 9):
            for x in range(wx + 9, wx + 12):
                setp(x, y + (1 if x == wx + 11 else 0), 'plank_dk' if x == wx + 11 else 'plank')
        for y in range(y0, y0 + rh):                      # corrugated tin roof
            for x in range(x0 - 3, x0 + w + 3):
                k = (x - x0) % 3
                c = 'tin_lt' if k == 0 else ('tin' if k == 1 else 'tin_dk')
                if y == y0 + rh // 2 and k == 0:
                    c = 'tin'
                if y > y0 + rh - 6 and (x * 13) % 11 == 0:
                    c = 'rtop_dk'                         # rust streaks
                if y == y0 or x in (x0 - 3, x0 + w + 2):
                    c = 'ink'
                setp(x, y, c)
        for x in range(x0 - 3, x0 + w + 3):               # scalloped eave
            k = (x - x0) % 3
            setp(x, y0 + rh - 1, 'ink' if k == 2 else 'tin_dk')
            if k == 2:
                setp(x, y0 + rh, 'ink')
        for x in range(x0 + 1, x0 + w - 1):
            shade(x, y0 + rh + 1, 0.72)
            if (x + y0) % 2 == 0:
                shade(x, y0 + rh + 2, 0.85)
        px = x0 + w - 9                                   # stovepipe + smoke
        for y in range(y0 - 9, y0 + 3):
            setp(px, y, 'tin_lt'); setp(px + 1, y, 'iron'); setp(px + 2, y, 'rail_dk')
        for x in range(px - 1, px + 4):
            setp(x, y0 - 10, 'ink')
        for (sx, sy, rows) in [(px - 1, y0 - 15, ['.cc.', 'ccss', '.ss.']), (px + 2, y0 - 20, ['.c.', 'css'])]:
            sprite(sx, sy, rows, {'c': 'tin_lt', 's': 'tin'})
    objects.append((base + 5, draw))


def mine_frame_v2(x0, x1, ytop, ybot):
    def draw():
        for y in range(ytop + 3, ybot):                   # inner frame (depth)
            setp(x0 + 4, y, 'face_dk'); setp(x1 - 4, y, 'face_dk')
        for x in range(x0 + 4, x1 - 3):
            setp(x, ytop + 3, 'face_dk')
        for y in range(ytop - 2, ybot + 1):               # posts
            for i, c in enumerate(('plank_lt', 'plank', 'plank', 'plank_dk')):
                setp(x0 - 4 + i, y, c); setp(x1 + 1 + i, y, c)
        for k in range(6):                                # knee braces
            setp(x0 + k, ytop + 5 - k, 'plank'); setp(x0 + k, ytop + 6 - k, 'plank_dk')
            setp(x1 - k, ytop + 5 - k, 'plank'); setp(x1 - k, ytop + 6 - k, 'plank_dk')
        for y in range(ytop - 6, ytop):                   # lintel
            for x in range(x0 - 7, x1 + 8):
                c = 'plank_lt' if y == ytop - 6 else ('plank_dk' if y == ytop - 1 else 'plank')
                if x in (x0 - 7, x1 + 7):
                    c = 'ink'
                setp(x, y, c)
        for bxp in (x0 - 2, x1 + 3):
            setp(bxp, ytop - 3, 'iron')
        sprite((x0 + x1) // 2 - 6, ytop - 13, SIGN_CROSS, {'k': 'ink', 'l': 'plank_lt', 'i': 'iron', 'd': 'plank_dk'})
        sprite((x0 + x1) // 2 - 1, ytop, ['.i.', 'kyk', 'kyk', '.k.'], {'k': 'iron', 'i': 'iron', 'y': 'glow'})
    objects.append((ybot, draw))


def ladder_v2(x, ytop, ybot):
    def draw():
        for y in range(ytop, ybot):
            shade(x + 9, y + 1, 0.75)
            for xx, c in ((x, 'plank_lt'), (x + 1, 'plank_dk'), (x + 7, 'plank_lt'), (x + 8, 'plank_dk')):
                setp(xx, y, c)
            if (y - ytop) % 5 == 3:
                for xx in range(x + 2, x + 7):
                    setp(xx, y, 'plank_lt'); shade(xx, y + 1, 0.8)
        setp(x, ytop - 1, 'plank_lt'); setp(x + 7, ytop - 1, 'plank_lt')
    objects.append((ybot, draw))


def water_tower_v2(cx, by):
    shadows.append((cx + 16, by + 1, 18, 4))

    def draw():
        legs_top = by - 28
        tank_b = legs_top + 2
        tank_t = tank_b - 22
        for y in range(legs_top - 2, by - 5):             # back legs
            for x in (cx - 9, cx - 8, cx + 7, cx + 8):
                setp(x, y, 'plank_dk')
        for k in range(24):                               # X bracing
            yy = legs_top + 4 + k
            setp(cx - 11 + k * 21 // 23, yy, 'plank_dk')
            setp(cx + 10 - k * 21 // 23, yy, 'plank_dk')
        for x in range(cx - 11, cx + 11):
            setp(x, legs_top + 15, 'plank'); setp(x, legs_top + 16, 'plank_dk')
        for y in range(legs_top, by):                     # front legs
            for i, c in enumerate(('plank_lt', 'plank', 'plank_dk')):
                setp(cx - 13 + i, y, c); setp(cx + 10 + i, y, c)
        for y in range(legs_top - 2, by):                 # ladder
            setp(cx - 6, y, 'plank_lt'); setp(cx - 2, y, 'plank_dk')
            if (y - legs_top) % 4 == 0:
                for x in range(cx - 5, cx - 2):
                    setp(x, y, 'plank_lt')
        for y in range(tank_t, tank_b + 1):               # tank (cylinder shading)
            for x in range(cx - 15, cx + 16):
                t = (x - (cx - 15)) / 30
                c = 'plank_lt' if t < 0.25 else ('plank' if t < 0.7 else 'plank_dk')
                if (x - cx) % 4 == 0:
                    c = 'plank' if t < 0.25 else 'plank_dk'
                if (y - tank_t) in (3, 11, 19):
                    c = 'tin_lt' if t < 0.3 else ('iron' if t < 0.75 else 'rail_dk')
                if x in (cx - 15, cx + 15) or y == tank_b:
                    c = 'ink'
                setp(x, y, c)
        for r in range(11):                               # conical roof
            y, w_ = tank_t - 10 + r, 2 + int(r * 1.6)
            for x in range(cx - w_, cx + w_ + 1):
                t = (x - (cx - w_)) / max(1, 2 * w_)
                c = 'tin_lt' if t < 0.35 else ('tin' if t < 0.7 else 'tin_dk')
                if (x - cx) % 5 == 0 and r > 2:
                    c = 'tin' if t < 0.35 else 'tin_dk'
                if x in (cx - w_, cx + w_) or r == 10:
                    c = 'ink'
                setp(x, y, c)
        setp(cx, tank_t - 11, 'ink'); setp(cx, tank_t - 12, 'iron')
        for y in range(tank_b + 1, tank_b + 7):           # spout
            setp(cx + 12, y, 'iron'); setp(cx + 13, y, 'rail_dk')
        for x in range(cx + 12, cx + 17):
            setp(x, tank_b + 7, 'iron')
        setp(cx + 16, tank_b + 9, 'river_lt')
    objects.append((by, draw))


def minecart_v2(cx, by):
    shadows.append((cx + 4, by + 1, 13, 2))

    def draw():
        top, bot = by - 15, by - 5
        for y in range(top - 6, top + 1):                 # ore heap inside the rim
            for x in range(cx - 10, cx + 11):
                hgt = max(2, 6 - abs(x - cx) // 2)
                if y >= top - hgt:
                    k = (x * 7 + y * 3) % 5
                    c = 'ore_lt' if (y == top - hgt or k == 0) else ('face' if k < 2 else ('ore' if k == 2 else 'face_dk'))
                    if (x * 11 + y * 5) % 17 == 0:
                        c = 'gold'
                    setp(x, y, c)
        for y in range(top, bot + 1):                     # riveted iron body
            t = (y - top) / (bot - top)
            xl, xr = cx - 12 + int(round(t * 3)), cx + 11 - int(round(t * 3))
            for x in range(xl, xr + 1):
                c = 'tin' if x < cx + 4 else 'tin_dk'
                if y == top:
                    c = 'ink'
                elif y == top + 1:
                    c = 'tin_lt'
                elif (x - cx) in (-5, 5) or y == top + 6:
                    c = 'rail_dk'
                if (x - cx) in (-5, 5) and y in (top + 3, top + 9):
                    c = 'tin_lt'
                if x in (xl, xr) or y == bot:
                    c = 'ink'
                setp(x, y, c)
        for wx in (cx - 8, cx + 7):
            sprite(wx - 2, by - 6, ['.kkk.', 'kiIik', 'kIkIk', 'kiIik', '.kkk.'], {'k': 'ink', 'i': 'rail_dk', 'I': 'iron'})
    objects.append((by, draw))


def ore_pile_v2(cx, by):
    shadows.append((cx + 4, by, 10, 2))
    rocks = [(-5, -3, 3.2), (4, -3, 3.4), (0, -6, 3.2), (-2, -1, 2.4), (6, -1, 2.0)]

    def draw():
        for (ox, oy, r) in sorted(rocks, key=lambda q: q[1]):
            for y in range(int(by + oy - r), int(by + oy + r) + 1):
                for x in range(int(cx + ox - r), int(cx + ox + r) + 1):
                    nx, ny = (x - cx - ox) / r, (y - by - oy) / r
                    d = nx * nx + ny * ny
                    if d > 1:
                        continue
                    v = -(0.6 * nx + 0.8 * ny)
                    c = 'face_lt' if v > 0.35 else ('face' if v > -0.25 else 'face_dk')
                    if (x * 5 + y * 3) % 7 == 0:
                        c = 'ore_lt' if v > 0 else 'ore'
                    if (x * 11 + y * 7) % 19 == 0:
                        c = 'gold'
                    if d > 0.75 and v < -0.2:
                        c = 'ink'
                    setp(x, y, c)
    objects.append((by, draw))


CART_W, CART_H = 20, 24


def _cart_grid():
    g = [['.'] * CART_W for _ in range(CART_H)]

    def put(x, y, c):
        if 0 <= x < CART_W and 0 <= y < CART_H:
            g[y][x] = c

    def rect(x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                put(x, y, c)
    return g, put, rect


def _auto_outline(g, only=None):
    """outline empty cells next to filled ones; `only` limits which filled cells get outlined"""
    src = [r[:] for r in g]
    for y in range(CART_H):
        for x in range(CART_W):
            if src[y][x] != '.':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < CART_W and 0 <= yy < CART_H and src[yy][xx] != '.' and (only is None or (xx, yy) in only):
                    g[y][x] = 'o'
                    break
    return g


def cart_body():
    """young mapmaker, no equipment: wide-brim hat, wind-blown scarf, coat with belt"""
    g, put, rect = _cart_grid()
    rect(6, 19, 8, 20, 'p'); put(8, 19, 'P'); put(8, 20, 'P')         # legs (mid-step)
    rect(11, 19, 13, 19, 'p'); put(13, 19, 'P')
    rect(5, 21, 8, 22, 'w'); put(8, 22, 'W')                          # boots
    rect(11, 20, 13, 21, 'w'); put(13, 21, 'W')
    for y in range(13, 19):                                           # coat
        xl, xr = (5, 14) if y < 17 else (4, 15)
        for x in range(xl, xr + 1):
            put(x, y, 'l' if x <= xl + 1 else ('C' if x >= xr - 1 else 'c'))
    for y in range(14, 19):
        put(10, y, 'C')
    put(9, 15, 'b')
    rect(5, 17, 14, 17, 'g'); put(9, 17, 'b')                         # belt + buckle
    rect(3, 13, 4, 17, 'c'); put(3, 13, 'l'); put(3, 14, 'l'); put(3, 15, 'l')   # left arm swinging forward
    rect(3, 18, 4, 18, 's')
    rect(15, 13, 16, 16, 'C'); rect(15, 17, 16, 17, 's')              # right arm back
    rect(5, 8, 14, 11, 's')                                           # head
    for y in range(9, 12):
        put(14, y, 'S')
    put(5, 11, '.'); put(14, 11, '.')
    for x in (5, 6, 9, 10, 13, 14):                                   # hair: sides + fringe tuft
        put(x, 8, 'k')
    put(5, 9, 'k'); put(14, 9, 'k')
    for y in (9, 10):                                                 # eyes + blush
        put(7, y, 'e'); put(12, y, 'e')
    put(6, 11, 'q'); put(13, 11, 'q')
    rect(5, 12, 14, 12, 'y'); put(6, 13, 'y'); put(7, 13, 'Y')        # scarf + knot
    for (x, y, c) in [(4, 12, 'y'), (3, 12, 'y'), (3, 13, 'Y'), (2, 13, 'y'), (1, 14, 'y'), (2, 14, 'Y'), (1, 15, 'Y')]:
        put(x, y, c)                                                  # tail blowing in the wind
    rect(7, 2, 12, 2, 'H'); rect(6, 3, 13, 4, 'H')                    # hat crown + band + brim
    put(6, 3, 'L'); put(6, 4, 'L'); put(7, 2, 'L'); put(13, 3, 'h'); put(13, 4, 'h'); put(12, 2, 'h')
    rect(6, 5, 13, 5, 'r')
    rect(2, 6, 17, 6, 'H'); rect(2, 6, 6, 6, 'L'); put(17, 6, 'h')
    rect(3, 7, 16, 7, 'h')
    return _auto_outline(g)


def cart_stick():
    """equippable: walking stick / map tube slung behind the right shoulder (drawn BEHIND the body)"""
    g, put, rect = _cart_grid()
    for k in range(8):
        x, y = 13 + round(k * 4 / 7), 15 - k
        put(x, y, 'm'); put(x + 1, y, 'M')
    put(17, 7, 'x'); put(18, 7, 'x'); put(17, 8, 'x'); put(18, 8, 'x')
    return _auto_outline(g)


def cart_pouch():
    """equippable: shoulder strap + pouch on the right hip (drawn IN FRONT of the body)"""
    g, put, rect = _cart_grid()
    for k in range(6):
        put(6 + k, 13 + k * 4 // 5, 't')
    rect(12, 16, 15, 18, 'g'); rect(12, 16, 15, 16, 'G'); put(13, 17, 'b')
    bag = {(x, y) for x in range(12, 16) for y in range(16, 19)}
    g = _auto_outline(g, only=bag)
    for y in range(CART_H):                                           # no outline over the right hand side
        if g[y][16] == 'o':
            g[y][16] = '.'
    return g


EQUIP_LAYERS = {'stick': ('back', cart_stick), 'pouch': ('front', cart_pouch)}


def build_cartographer(equip=('pouch',)):
    """compose: back equipment -> body -> front equipment. Unequipped items are simply not drawn."""
    back = [fn() for name, (side, fn) in EQUIP_LAYERS.items() if name in equip and side == 'back']
    front = [fn() for name, (side, fn) in EQUIP_LAYERS.items() if name in equip and side == 'front']
    out = [['.'] * CART_W for _ in range(CART_H)]
    for layer in back + [cart_body()] + front:
        for y in range(CART_H):
            for x in range(CART_W):
                if layer[y][x] != '.':
                    out[y][x] = layer[y][x]
    return [''.join(r) for r in out]


CARTOGRAPHER = build_cartographer(tuple(OPTS.get('equip', ('pouch',))))
CPAL = {'o': 'ink', 'H': 'hat', 'h': 'hat_dk', 'L': 'hat_lt', 'r': 'band', 'f': 'feather', 'F': 'feather_dk',
        'k': 'hair2', 's': 'skin', 'S': 'skin_sh', 'e': 'eye', 'q': 'blush', 'y': 'scarf2', 'Y': 'scarf2_dk',
        'c': 'coat2', 'C': 'coat2_dk', 'l': 'coat2_lt', 'b': 'button', 't': 'satchel_dk', 'g': 'satchel',
        'G': 'satchel_dk', 'm': 'tube', 'M': 'tube_dk', 'x': 'cap_red', 'p': 'pants2', 'P': 'pants2_dk',
        'w': 'boot2', 'W': 'boot2_dk'}


def player_v2(cx, feet_y):
    shadows.append((cx + 1, feet_y, 7, 2))
    objects.append((feet_y, lambda: sprite(cx - 10, feet_y - len(CARTOGRAPHER) + 1, CARTOGRAPHER, CPAL)))


if ART >= 2:
    house, bridge, fence, barrel, logs, rowboat, jetty = house_v2, bridge_v2, fence_v2, barrel_v2, logs_v2, rowboat_v2, jetty_v2
    shack, mine_frame, ladder, water_tower, minecart, ore_pile = shack_v2, mine_frame_v2, ladder_v2, water_tower_v2, minecart_v2, ore_pile_v2
    if OPTS.get('hero') != 'tall':
        player = player_v2


# ------------------------------------------------------------------ sea props + sailing mount
def sea_stack(cx, by, w, h):
    sr = np.random.default_rng(cx * 7 + by)
    halves = [w / 2 * (0.55 + 0.45 * k / h) + sr.uniform(-1.3, 1.3) for k in range(h + 1)]
    lean = np.cumsum(sr.integers(-1, 2, h + 1)) * 0.3

    def draw():
        for x in range(int(cx - w / 2) + 2, int(cx + w / 2) + 8):
            for y in (by + 1, by + 2):
                if 0 <= x < WW and sea[y, x] and (y == by + 1 or (x + y) % 2 == 0):
                    shade(x, y, 0.7)
        for k in range(h + 1):
            y = by - h + k
            xl, xr = int(round(cx + lean[k] - halves[k])), int(round(cx + lean[k] + halves[k]))
            for x in range(xl, xr + 1):
                t = (x - xl) / max(1, xr - xl)
                if k < 3:
                    c = 'grass_lt' if t < 0.4 else ('grass' if t < 0.75 else 'grass_dk')
                else:
                    c = 'stone_lt' if t < 0.3 else ('stone' if t < 0.7 else 'stone_dk')
                    if (y + int(round(2 * np.sin(x / 4.0)))) % 6 == 0:
                        c = 'stone_dk'
                    if (x * 5 + k) % 13 == 0 and t > 0.2:
                        c = 'slate_dk'
                    if (x * 7 + y * 3) % 23 == 0 and t < 0.7:
                        c = 'cream'
                if x in (xl, xr) or k == h:
                    c = 'ink'
                setp(x, y, c)
            if k == 0:
                for x in range(xl, xr + 1):
                    setp(x, y - 1, 'ink')
        for x in range(int(cx - w / 2) - 3, int(cx + w / 2) + 4):
            if x % 3:
                setp(x, by + 1, 'foam')
    objects.append((by, draw))


def stilt_hut(x0, base):
    w = 26
    wall_b = base - 8
    wall_t = wall_b - 12
    roof_t = wall_t - 10

    def draw():
        for x in range(x0, x0 + w + 4):
            for y in (base + 1, base + 2):
                if sea[y, x] and (y == base + 1 or (x + y) % 2 == 0):
                    shade(x, y, 0.72)
        for sx in (x0 + 2, x0 + 10, x0 + 16, x0 + 23):
            for y in range(wall_b, base + 1):
                setp(sx, y, 'trunk'); setp(sx + 1, y, 'trunk_dk')
            setp(sx - 1, base + 1, 'foam'); setp(sx + 2, base + 1, 'foam')
        for y in (wall_b, wall_b + 1):
            for x in range(x0 - 2, x0 + w + 2):
                setp(x, y, 'wood_lt' if y == wall_b else 'wood_dk')
        for y in range(wall_t, wall_b):
            for x in range(x0, x0 + w):
                k = (x - x0) % 4
                c = 'plank_lt' if k == 0 else ('plank_dk' if k == 3 else 'plank')
                if x in (x0, x0 + w - 1):
                    c = 'ink'
                setp(x, y, c)
        for y in range(wall_t + 3, wall_b):
            for x in range(x0 + 15, x0 + 22):
                setp(x, y, 'ink' if x in (x0 + 15, x0 + 21) or y == wall_t + 3 else 'door')
        for y in range(wall_t + 3, wall_t + 9):
            for x in range(x0 + 4, x0 + 11):
                c = 'glass' if (x - x0 - 4) + (y - wall_t - 3) > 3 else 'glass_lt'
                if x in (x0 + 4, x0 + 10) or y in (wall_t + 3, wall_t + 8):
                    c = 'ink'
                setp(x, y, c)
        for y in range(roof_t, wall_t + 2):
            r = y - roof_t
            inset = max(0, 3 - r)
            for x in range(x0 - 3 + inset, x0 + w + 3 - inset):
                c = 'thatch' if (x + r * 2) % 3 else 'thatch_dk'
                if r % 4 == 3:
                    c = 'thatch_dk'
                if x < x0 + 6 and c == 'thatch':
                    c = 'thatch_lt'
                if r == 0 or x in (x0 - 3 + inset, x0 + w + 2 - inset) or y == wall_t + 1:
                    c = 'ink'
                setp(x, y, c)
        for k in range(10):                                   # fish-drying line
            setp(x0 + w + 2 + k, wall_t + 2 + (1 if 2 < k < 7 else 0), 'trunk_lt')
        for k in (3, 6):
            sprite(x0 + w + 1 + k, wall_t + 3, ['s', 's'], {'s': 'stone_lt'})
    objects.append((base + 1, draw))


def rope_bridge(a, b, sag=4):
    def draw():
        (x0, y0), (x1, y1) = a, b
        L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        px, py = -(y1 - y0) / L, (x1 - x0) / L
        n = int(L)
        shaded = set()
        for i in range(n + 1):
            t = i / n
            cx_, cy_ = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + sag * np.sin(np.pi * t)
            for k in range(-3, 4):
                p = (int(round(cx_ + px * k + 3)), int(round(cy_ + py * k + 7)))
                if p not in shaded and 0 <= p[0] < WW and 0 <= p[1] < HH and sea[p[1], p[0]]:
                    shaded.add(p); shade(p[0], p[1], 0.75)
        for i in range(n + 1):
            t = i / n
            cx_, cy_ = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + sag * np.sin(np.pi * t)
            if i % 3 != 2:
                for k in range(-3, 4):
                    setp(int(round(cx_ + px * k)), int(round(cy_ + py * k)), 'wood_lt' if i % 3 == 0 else 'wood')
            for side in (-4, 4):
                setp(int(round(cx_ + px * side)), int(round(cy_ + py * side - 3)), 'trunk_lt')
        for (ex, ey) in (a, b):
            for side in (-4, 4):
                sprite(int(round(ex + px * side)) - 1, int(round(ey + py * side)) - 6,
                       ['ll', 'ld', 'ld', 'ld', 'ld', 'dd'], {'l': 'wood_lt', 'd': 'wood_dk'})
    objects.append((max(a[1], b[1]), draw))


def buoy(cx, cy):
    def draw():
        for x in range(cx - 5, cx + 6):
            if (x + cy) % 2 == 0:
                setp(x, cy + 3, 'foam')
        shade(cx + 3, cy + 2, 0.7); shade(cx + 4, cy + 2, 0.7)
        sprite(cx - 2, cy - 7, ['..k..', '.kgk.', '..k..', '.kkk.', 'krrrk', 'kwwwk', 'krrrk', 'kwwwk', '.kkk.'],
               {'k': 'ink', 'g': 'gold', 'r': 'band', 'w': 'cream'})
    objects.append((cy + 3, draw))


def wreck(cx, by):
    def draw():
        for x in range(cx - 24, cx + 22):
            setp(x, by, 'trunk_dk'); setp(x, by - 1, 'trunk')
        for i in range(6):
            x0 = cx - 20 + i * 8
            hgt = 9 - abs(i - 2) * 2
            for k in range(hgt):
                x = x0 + int(round(2 * np.sin(k / 4.0)))
                setp(x, by - 2 - k, 'trunk' if k < hgt - 1 else 'trunk_lt'); setp(x + 1, by - 2 - k, 'trunk_dk')
            shade(x0 + 2, by + 1, 0.75)
    objects.append((by, draw))


def gull(cx, cy):
    def draw():
        for (dx, dy) in ((0, 0), (1, 1), (2, 2), (3, 1), (4, 0)):
            shade(cx + dx + 7, cy + dy + 12, 0.72)
        sprite(cx, cy, ['w...w', '.w.w.', '..k..'], {'w': 'cream', 'k': 'stone'})
    objects.append((cy + 40, draw))


def mossback(cx, cy, k=1.45):
    """sailing concept 1: an ancient wandering creature carrying a moss garden, lantern and saddle basket"""
    def K(n):
        return int(round(n * k))

    def draw():
        wake = set()
        for i in range(K(70)):
            spread = K(4) + i * 0.33
            for sgn in (-1, 1):
                for th in (0, 1):
                    if i % 4 != 3:
                        wake.add((cx - K(32) - i, int(round(cy + K(3) + sgn * (spread + th)))))
        for (x, y) in wake:
            if 0 <= x < WW and 0 <= y < HH and sea[y, x]:
                setp(x, y, 'foam')
        wr = np.random.default_rng(401)
        for _ in range(140):
            x, y = cx - K(32) - int(wr.integers(0, K(26))), cy + int(wr.integers(-K(4), K(12)))
            if sea[y, x]:
                setp(x, y, 'foam' if wr.random() < 0.6 else 'sea_lt')
        for y in range(cy - K(3), cy + K(15)):
            for x in range(cx - K(37), cx + K(41)):
                if ((x - cx - K(2)) / K(37)) ** 2 + ((y - cy - K(4)) / K(10)) ** 2 <= 1 and sea[y, x]:
                    shade(x, y, 0.72)
        for (fx, fy, rx, ry) in ((cx + K(21), cy + K(7), K(7), K(3)), (cx - K(23), cy + K(6), K(6), K(3))):
            for y in range(fy - ry, fy + ry + 1):
                for x in range(fx - rx, fx + rx + 1):
                    if ((x - fx) / rx) ** 2 + ((y - fy) / ry) ** 2 <= 1:
                        c = 'mb_skin_dk' if y > fy else 'mb_skin'
                        if ((x - fx) / rx) ** 2 + ((y - fy) / ry) ** 2 > 0.75 and y >= fy:
                            c = 'ink'
                        setp(x, y, c)
            for (dx, dy) in ((rx + 1, 0), (rx, ry), (-rx - 1, 1), (rx + 2, -1)):
                setp(fx + dx, fy + dy, 'foam')
        hx_, hy_, hrx, hry = cx + K(31), cy - K(1), K(9), K(7)
        for y in range(hy_ - hry, hy_ + hry + 1):
            for x in range(hx_ - hrx, hx_ + hrx + 1):
                nx, ny = (x - hx_) / hrx, (y - hy_) / hry
                if nx * nx + ny * ny <= 1:
                    v = -(0.6 * nx + 0.8 * ny)
                    c = 'mb_skin_lt' if v > 0.35 else ('mb_skin' if v > -0.3 else 'mb_skin_dk')
                    if nx * nx + ny * ny > 0.82:
                        c = 'ink'
                    setp(x, y, c)
        sprite(hx_ + K(2), hy_ - K(4), ['kke', 'kkk', '.k.'], {'k': 'eye', 'e': 'snow_lt'})
        for i in range(K(6)):
            setp(hx_ + K(2) + i, hy_ + K(4) - (i // 4), 'mb_skin_dk')
        setp(hx_ + hrx - 2, hy_ - 1, 'mb_skin_dk')
        for x in range(hx_ - hrx + 1, hx_ + hrx, 2):
            setp(x, hy_ + hry + 1, 'foam')
        sx, sy, srx, sry = cx - K(2), cy + K(2), K(27), K(14)
        wl = cy + K(4)
        for y in range(sy - sry, wl + 1):
            for x in range(sx - srx, sx + srx + 1):
                nx, ny = (x - sx) / srx, (y - sy) / sry
                d = nx * nx + ny * ny
                if d > 1:
                    continue
                v = -(0.55 * nx + 0.85 * ny)
                if y >= wl - 4:
                    c = 'mb_skin_dk' if y >= wl - 1 else 'cliff'
                    if (x * 7 + y) % 9 == 0:
                        c = 'foam'
                    if d > 0.93 or y == wl:
                        c = 'ink'
                else:
                    c = 'grass_lt' if v > 0.45 else ('grass' if v > -0.05 else 'grass_dk')
                    if MOSS[y % HH, x % WW] > 0.5:
                        c = 'leaf_lt' if v > 0 else 'leaf'
                    if (x * 13 + y * 7) % 41 == 0:
                        c = 'flower_b'
                    if d > 0.9:
                        c = 'ink'
                setp(x, y, c)
        for x in range(sx - srx + 2, sx + srx - 1):
            if x % 3 != 1:
                setp(x, wl + 1, 'foam')
        tx, ty = sx - K(15), sy - K(6)
        for i in range(K(9)):
            o = 1 if i > K(5) else 0
            setp(tx + o, ty - i, 'trunk'); setp(tx + 1 + o, ty - i, 'trunk_dk')
        for (ox, oy, r) in ((0, -K(12), K(5)), (-K(4), -K(9), K(4)), (K(4), -K(10), K(4))):
            for y in range(ty + oy - r, ty + oy + r + 1):
                for x in range(tx + ox - r, tx + ox + r + 1):
                    nx, ny = (x - tx - ox) / r, (y - ty - oy) / r
                    if nx * nx + ny * ny <= 1:
                        v = -(0.6 * nx + 0.8 * ny)
                        setp(x, y, 'leaf_hi' if v > 0.5 else ('leaf_lt' if v > 0 else ('leaf' if v > -0.5 else 'leaf_dk')))
        lx, ly = sx + K(16), sy - K(5)
        for y in range(ly - K(12), ly):
            setp(lx, y, 'trunk_dk'); setp(lx + 1, y, 'trunk')
        sprite(lx - 2, ly - K(12) - 5, ['.kkk.', 'kyyyk', 'kygyk', 'kyyyk', '.kkk.'], {'k': 'iron', 'y': 'glow', 'g': 'cream'})
        bx_, btop = sx + 1, sy - K(8)
        sprite(bx_ - 10, btop - 14, CARTOGRAPHER[:14], CPAL)
        for y in range(btop, btop + 7):
            for x in range(bx_ - 9, bx_ + 10):
                c = 'wood_lt' if (x + y) % 2 == 0 else 'wood'
                if y == btop:
                    c = 'wood_dk'
                if x in (bx_ - 9, bx_ + 9) or y == btop + 6:
                    c = 'ink'
                setp(x, y, c)
    objects.append((cy + K(14), draw))


# ------------------------------------------------------------------ winter props
def stone_cottage(x0, y0, w):
    RT, RH = y0, 24
    WT = RT + RH - 2
    WB = WT + 19
    for y in range(WT + 2, WB + 3):
        for x in range(x0 + w, x0 + w + 7):
            if x < x0 + w + 3:
                shade(x, y, 0.72)
            elif (x + y) % 2 == 0:
                shade(x, y, 0.84)
    for x in range(x0 + 1, x0 + w + 3):
        shade(x, WB + 1, 0.74)

    def draw():
        split = x0 + int(w * 0.7)
        for y in range(WT, WB + 1):                           # stone walls
            row, ln = (y - WT) // 4, (y - WT) % 4
            for x in range(x0, x0 + w):
                lit = x < split
                c = ('stone_lt' if ln == 0 else 'stone') if lit else ('stone' if ln == 0 else 'stone_dk')
                if ln == 3 or (x - x0 + (4 if row % 2 else 0)) % 8 == 0:
                    c = 'slate_dk'
                if x in (x0, x0 + w - 1) or y == WB:
                    c = 'ink'
                setp(x, y, c)
        dx0 = x0 + w // 2 - 5                                 # arched door
        for y in range(WT + 6, WB):
            for x in range(dx0, dx0 + 10):
                if y == WT + 6 and x in (dx0, dx0 + 1, dx0 + 8, dx0 + 9):
                    continue
                c = 'door' if (x - dx0) % 3 else 'door_lt'
                if x in (dx0, dx0 + 9) or y == WT + 6 or (y == WT + 7 and x in (dx0 + 1, dx0 + 8)):
                    c = 'ink'
                setp(x, y, c)
        setp(dx0 + 7, WT + 13, 'gold')
        for wx in (x0 + 7, x0 + w - 15):                      # warm lit windows, snowy sills
            for y in range(WT + 6, WT + 13):
                for x in range(wx, wx + 8):
                    c = 'win_glow'
                    if x in (wx, wx + 7) or y in (WT + 6, WT + 12) or x == wx + 4 or y == WT + 9:
                        c = 'wood_dk'
                    setp(x, y, c)
            for x in range(wx - 1, wx + 9):
                setp(x, WT + 13, 'snow'); setp(x, WT + 14, 'snow_sh')
        for y in range(RT, RT + RH):                          # slate roof
            for x in range(x0 - 3, x0 + w + 3):
                ln = (y - RT) % 4
                c = 'slate_lt' if ln == 0 else ('slate' if ln < 3 else 'slate_dk')
                if x in (x0 - 3, x0 + w + 2) or y == RT:
                    c = 'ink'
                setp(x, y, c)
        for x in range(x0 - 3, x0 + w + 3):                   # snow on the upper roof, slate showing below
            edge = RT + RH // 2 - 1 + int(round(2 * np.sin(x / 4.0) + np.sin(x / 1.7)))
            for y in range(RT - 3, edge + 1):
                c = 'snow_lt' if y <= RT - 1 else ('snow' if x < split else 'snow_sh')
                if y == edge:
                    c = 'snow_sh'
                if y == RT - 3 or x in (x0 - 3, x0 + w + 2):
                    c = 'ink'
                setp(x, y, c)
        for x in range(x0 - 3, x0 + w + 3):
            setp(x, RT + RH - 1, 'ink')
        for x in range(x0 - 1, x0 + w + 1, 3):                # icicles
            for k in range(1 + (x * 7) % 4):
                setp(x, RT + RH + k, 'frz_hi' if k == 0 else 'frz')
        cx0 = x0 + w - 16                                     # chimney, snow cap, smoke
        for y in range(RT - 10, RT + 4):
            for x in range(cx0, cx0 + 7):
                c = 'stone_lt' if x < cx0 + 3 else 'stone_dk'
                if (y - RT) % 3 == 0:
                    c = 'slate_dk'
                if x in (cx0, cx0 + 6):
                    c = 'ink'
                setp(x, y, c)
        for x in range(cx0 - 1, cx0 + 8):
            setp(x, RT - 12, 'ink'); setp(x, RT - 11, 'snow')
        for (sx, sy, rows) in [(cx0 + 1, RT - 17, ['.cc.', 'cccs', '.ss.']), (cx0 + 4, RT - 22, ['.c.', 'ccs', '.s.']),
                               (cx0 + 1, RT - 26, ['cc', 'cs'])]:
            sprite(sx, sy, rows, {'c': 'snow_lt', 's': 'snow_sh'})
    objects.append((WB + 1, draw))


def pine_snow(bx, by, s=1.0):
    shadows.append((bx + 6 * s, by + 1, 10 * s, 4 * s))

    def draw():
        for y in range(by - 6, by):
            for x in range(bx - 2, bx + 2):
                setp(x, y, 'trunk_dk' if x >= bx else 'trunk')
        for (ty, half) in [(by - 6, 11), (by - 14, 9), (by - 21, 7), (by - 27, 4)]:
            h = int(half * 1.1 * s) + 3
            for r in range(h):
                w_ = int((r + 1) / h * half * s)
                y = ty - h + r
                for dx in range(-w_, w_ + 1):
                    if dx == w_ or r == h - 1:
                        c = 'leaf_ol'
                    elif dx < -w_ // 3:
                        c = 'pine_lt' if (dx + y) % 3 else 'pine'
                    elif dx < w_ // 3:
                        c = 'pine'
                    else:
                        c = 'pine_dk'
                    if c != 'leaf_ol':
                        if r <= 1:
                            c = 'snow' if dx <= 0 else 'snow_sh'
                        elif r == h - 2 and dx < 0 and dx % 3 != 0:
                            c = 'snow'
                        elif dx < -w_ // 2 and (r + dx) % 4 == 0:
                            c = 'snow'
                    setp(bx + dx, y, c)
    objects.append((by, draw))


def wall_snow(x0, x1, y):
    def draw():
        for x in range(x0, x1):
            shade(x, y + 1, 0.75)
            for yy in range(y - 6, y + 1):
                k = (x + (2 if (yy // 3) % 2 else 0)) % 5
                c = 'stone_lt' if yy == y - 6 else ('stone' if k else 'stone_dk')
                if (yy - y) % 3 == 0:
                    c = 'stone_dk'
                if yy == y:
                    c = 'ink'
                setp(x, yy, c)
            for yy in (y - 9, y - 8, y - 7):
                if yy == y - 9 and (x * 3) % 7 == 0:
                    continue
                setp(x, yy, 'snow_lt' if yy == y - 9 else ('snow' if x % 7 else 'snow_sh'))
        for x in (x0 - 1, x1):
            for yy in range(y - 8, y + 1):
                setp(x, yy, 'ink')
    objects.append((y, draw))


def well(cx, by):
    shadows.append((cx + 6, by + 1, 11, 3))

    def draw():
        for y in range(by - 7, by + 1):
            for x in range(cx - 9, cx + 10):
                c = 'stone_lt' if x < cx - 3 else ('stone' if x < cx + 5 else 'stone_dk')
                if (x + (2 if ((y - by) // 3) % 2 else 0)) % 5 == 0 or (y - by) % 3 == 0:
                    c = 'slate_dk'
                if x in (cx - 9, cx + 9) or y == by:
                    c = 'ink'
                setp(x, y, c)
        for y in range(by - 11, by - 5):
            for x in range(cx - 9, cx + 10):
                d = ((x - cx) / 9.5) ** 2 + ((y - (by - 8)) / 3.2) ** 2
                if d <= 1:
                    setp(x, y, 'ink' if d > 0.88 else ('snow' if d > 0.55 else 'frz'))
        for px in (cx - 8, cx + 7):
            for y in range(by - 24, by - 8):
                setp(px, y, 'wood'); setp(px + 1, y, 'wood_dk')
        for r in range(6):
            y, w_ = by - 30 + r, 4 + r * 2
            for x in range(cx - w_, cx + w_ + 1):
                c = 'snow' if r < 3 else ('wood' if x < cx + 3 else 'wood_dk')
                if r == 2 and x > cx:
                    c = 'snow_sh'
                if x in (cx - w_, cx + w_) or r == 5:
                    c = 'ink'
                setp(x, y, c)
        for x in range(cx - 7, cx + 7):
            setp(x, by - 20, 'trunk_dk')
        for y in range(by - 19, by - 14):
            setp(cx, y, 'rail_dk')
        sprite(cx - 2, by - 14, ['kkkk', 'kwwk', '.kk.'], {'k': 'ink', 'w': 'wood'})
    objects.append((by, draw))


def sled(cx, by):
    shadows.append((cx + 3, by + 1, 10, 2))
    objects.append((by, lambda: sprite(cx - 9, by - 5, [
        '.kkkkkkkkkkkkk....', 'klwlwlwlwlwlwlk...', 'kwwwwwwwwwwwwwk...', '.k.k.......k.k....',
        'kddddddddddddddkd.', '.kkkkkkkkkkkkkkk..'], {'k': 'ink', 'l': 'wood_lt', 'w': 'wood', 'd': 'rail_dk'})))


def rock_snow(bx, by, w=8, h=5):
    shadows.append((bx + 3, by, w * 0.8, 2))

    def draw():
        for y in range(by - h, by):
            for x in range(bx - w // 2, bx + w // 2 + 1):
                nx, ny = (x - bx) / (w / 2 + 0.5), (y - (by - h / 2)) / (h / 2 + 0.5)
                if nx * nx + ny * ny <= 1:
                    v = -(0.6 * nx + 0.8 * ny)
                    c = 'stone_lt' if v > 0.25 else ('stone' if v > -0.35 else 'stone_dk')
                    if ny < -0.15 + 0.2 * np.sin(x):
                        c = 'snow' if nx < 0.3 else 'snow_sh'
                    setp(x, y, c)
    objects.append((by, draw))


def cairn(cx, by):
    shadows.append((cx + 3, by, 6, 2))
    objects.append((by, lambda: sprite(cx - 4, by - 10, [
        '...p....', '...prrr.', '...prr..', '...p....', '..kpk...', '.knnnk..', '.kkkkk..',
        'knlsssk.', 'kkkkkkk.', 'klssssdk', 'kkkkkkkk'],
        {'p': 'wood_dk', 'r': 'band', 'k': 'ink', 'n': 'snow', 'l': 'stone_lt', 's': 'stone', 'd': 'stone_dk'})))


# ------------------------------------------------------------------ forest props
def fern(cx, by):
    objects.append((by, lambda: sprite(cx - 4, by - 4, ['...l.l...', '.l.lml.l.', 'lmlmdmlml', '.mdmdmdm.', '..ddddd..'],
                                        {'l': 'leaf_lt', 'm': 'leaf', 'd': 'leaf_dk'})))


def mushrooms(cx, by):
    shadows.append((cx + 2, by, 4, 1.5))
    objects.append((by, lambda: sprite(cx - 3, by - 5, ['.rr....', 'rrwr.rr', 'rrrrrwr', '.cc.rrr', '.cc..c.', '.....c.'],
                                        {'r': 'band', 'w': 'cream', 'c': 'wall'})))


def fallen_log(x0, x1, by):
    shadows.append(((x0 + x1) / 2 + 3, by + 1, (x1 - x0) / 2 + 3, 2.5))

    def draw():
        for x in range(x0, x1):
            setp(x, by - 9, 'ink')
            for y in range(by - 8, by + 1):
                k = y - (by - 8)
                c = 'trunk_lt' if k < 3 else ('trunk' if k < 6 else 'trunk_dk')
                if (x * 3 + k) % 11 == 0:
                    c = 'trunk_dk'
                if k <= 2 and MOSSF[y % HH, x % WW] > 0.15:
                    c = 'leaf_lt' if k == 0 else 'leaf'
                if y == by or x == x0:
                    c = 'ink'
                setp(x, y, c)
        cx_, cy_ = x1, by - 4
        for y in range(cy_ - 4, cy_ + 5):
            for x in range(cx_ - 4, cx_ + 5):
                d = ((x - cx_) ** 2 + (y - cy_) ** 2) ** 0.5
                if d <= 4.5:
                    c = 'ink' if d > 3.8 else ('trunk' if d > 3.0 else ('wood_lt' if d > 0.7 else 'wood_dk'))
                    if 1.6 < d < 2.3:
                        c = 'wood'
                    setp(x, y, c)
        sprite(x0 + 9, by - 12, ['.rr.', 'rwrr', '.cc.'], {'r': 'band', 'w': 'cream', 'c': 'wall'})
    objects.append((by, draw))


def stump(cx, by):
    shadows.append((cx + 5, by, 9, 3))

    def draw():
        for y in range(by - 6, by + 1):
            for x in range(cx - 7, cx + 8):
                c = 'trunk_lt' if x < cx - 2 else ('trunk' if x < cx + 4 else 'trunk_dk')
                if (x + y) % 4 == 0 and x > cx - 5:
                    c = 'trunk_dk'
                if x in (cx - 7, cx + 7) or y == by:
                    c = 'ink'
                setp(x, y, c)
        for y in range(by - 10, by - 2):
            for x in range(cx - 7, cx + 8):
                d = ((x - cx) / 7.5) ** 2 + ((y - (by - 6.5)) / 3.4) ** 2
                if d <= 1:
                    c = 'wood_lt' if d < 0.7 else 'wood'
                    if 0.3 < d < 0.42 or d < 0.06:
                        c = 'wood_dk'
                    if d > 0.85:
                        c = 'ink'
                    setp(x, y, c)
    objects.append((by, draw))


def hollow_oak(cx, by):
    """Hollowood's signature: a giant hollow oak the path runs straight through"""
    shadows.append((cx + 34, by + 2, 56, 7))

    def draw():
        L, Rr = cx - 46, cx + 46
        for y in range(-4, by):                               # trunk with bark ridges + moss
            fl = max(0, y - (by - 16)) // 2
            xl, xr = L - fl, Rr + fl
            for x in range(xl, xr + 1):
                t = (x - xl) / (xr - xl)
                ridge = (x + int(round(3 * np.sin(y / 9.0 + x * 0.21)))) % 7
                c = 'bark_lt' if t < 0.22 else ('bark' if t < 0.9 else 'bark_dk')
                if ridge == 0:
                    c = 'bark_dk' if t > 0.15 else 'bark'
                elif ridge in (1, 2) and t < 0.55:
                    c = 'bark_lt'
                if MOSSF[y % HH, x % WW] > 0.6 and t < 0.35 and y > by - 12:
                    c = 'leaf' if ridge < 3 else 'leaf_dk'
                if x in (xl, xr):
                    c = 'ink'
                setp(x, y, c)
        def opening(x, y, grow=0.0):
            """organic hollow: narrow at the top, widening toward the ground, slightly crooked edges"""
            top = by - 38 - grow
            if y < top or y > by:
                return False
            t = (y - top) / (by - top)
            half = 5 + 12 * t ** 0.55 + grow + 1.2 * np.sin(y / 2.7)
            return abs(x - (cx + 2.0 * np.sin(y / 8.0))) <= half
        for y in range(by - 44, by + 1):
            for x in range(cx - 24, cx + 25):
                if opening(x, y):
                    c = 'mine'                                        # deep dark interior
                    if not opening(x - 3, y):
                        c = 'bark_dk'                                 # faint inner wall on the lit side
                    if y > by - 5:
                        c = 'path_dk' if abs(x - cx) < 5 - (by - y) // 2 + 2 else c   # path fading inside
                    setp(x, y, c)
                elif opening(x, y, 2.2):
                    setp(x, y, 'bark_lt' if x < cx else 'bark_dk')    # thick bark lip
        for k, ox in enumerate((-3, 0, 2, 5)):                       # little roots hanging over the opening
            for j in range(2 + (k * 2) % 3):
                setp(cx + ox, by - 37 + j, 'trunk')
        for (gx, gy) in ((cx - 9, by - 3), (cx + 8, by - 2)):        # glowing mushrooms just inside
            sprite(gx - 1, gy - 2, ['ggg', '.w.'], {'g': 'glow', 'w': 'cream'})
        for (sx, sgn) in ((L + 6, -1), (Rr - 6, 1)):          # roots fanning out
            for k in range(18):
                yb = by - 8 + k // 3
                for t in range(-2, 3):
                    setp(sx + sgn * k, yb + t, 'trunk_dk' if t > 0 else ('trunk' if t > -2 else 'trunk_lt'))
                setp(sx + sgn * k, yb + 3, 'ink')
        for (sx, sgn) in ((L + 22, -1), (Rr - 20, 1)):
            for k in range(10):
                for t in range(-2, 2):
                    setp(sx + sgn * k // 2 + t, by - 4 + k, 'trunk' if t < 1 else 'trunk_dk')
        for (ox, oy, r) in ((-44, -2, 15), (-14, 2, 13), (18, -1, 15), (46, 3, 12), (0, -6, 12)):   # canopy above
            for y in range(oy - r, oy + r + 1):
                for x in range(cx + ox - r, cx + ox + r + 1):
                    nx, ny = (x - cx - ox) / r, (y - oy) / r
                    if nx * nx + ny * ny <= 1:
                        v = -(0.55 * nx + 0.85 * ny) * 0.5 + 0.5 + (BAYER[y % 4, x % 4] - 0.5) * 0.3 * DA
                        setp(x, y, LEAF_TONES[int(np.clip(v * len(LEAF_TONES), 0, len(LEAF_TONES) - 1))])
    objects.append((by, draw))


# ------------------------------------------------------------------ sailing mount options
def _in_sea(x, y):
    return 0 <= x < WW and 0 <= y < HH and sea[y, x]


def _wake(sx, sy, length, spread0, rate, seed):
    pts = set()
    for i in range(length):
        sp = spread0 + i * rate
        for sgn in (-1, 1):
            for th in (0, 1):
                if i % 4 != 3:
                    pts.add((sx - i, int(round(sy + sgn * (sp + th)))))
    for (x, y) in pts:
        if _in_sea(x, y):
            setp(x, y, 'foam')
    wr = np.random.default_rng(seed)
    for _ in range(110):
        x, y = sx - int(wr.integers(0, 22)), sy + int(wr.integers(-6, 7))
        if _in_sea(x, y):
            setp(x, y, 'foam' if wr.random() < 0.6 else 'sea_lt')


def _underwater(cx, cy, rx, ry, f=0.7):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1 and _in_sea(x, y):
                shade(x, y, f)


def _shape(pix, colour, outline=True):
    """paint a pixel set: colour(x, y) per pixel, then an ink outline on the silhouette edge"""
    for (x, y) in pix:
        setp(x, y, colour(x, y))
    if outline:
        for (x, y) in pix:
            if any((x + dx, y + dy) not in pix for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                setp(x, y, 'ink')


def _ellipse_pix(cx, cy, rx, ry, ymax=None):
    return {(x, y) for y in range(int(cy - ry), int(cy + ry) + 1) for x in range(int(cx - rx), int(cx + rx) + 1)
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1 and (ymax is None or y <= ymax)}


def _limb_pix(x0, y0, x1, y1, w0, w1, bend=0.0):
    pix = set()
    n = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t - (y1 - y0) * bend * np.sin(np.pi * t)
        y = y0 + (y1 - y0) * t + (x1 - x0) * bend * np.sin(np.pi * t)
        r = w0 + (w1 - w0) * t
        for yy in range(int(y - r) - 1, int(y + r) + 2):
            for xx in range(int(x - r) - 1, int(x + r) + 2):
                if (xx - x) ** 2 + (yy - y) ** 2 <= r * r:
                    pix.add((xx, yy))
    return pix


def _lit(pix, lt, md, dk):
    ys = [p[1] for p in pix]
    y0, y1 = min(ys), max(ys)

    def col(x, y):
        t = (y - y0) / max(1, y1 - y0)
        return lt if t < 0.3 else (md if t < 0.7 else dk)
    return col


def _rider(bx, seat_y):
    """rider's upper body seated with the bottom of the sprite slice at seat_y, plus a striped saddle blanket"""
    sprite(bx - 10, seat_y - 14, CARTOGRAPHER[:14], CPAL)
    for yy in range(seat_y, seat_y + 5):
        for x in range(bx - 9, bx + 10):
            c = 'blanket' if (yy - seat_y) % 2 == 0 else 'blanket_lt'
            if yy == seat_y:
                c = 'saddle'
            if x in (bx - 9, bx + 9) or yy == seat_y + 4:
                c = 'ink'
            setp(x, yy, c)


def _waterline(x0, x1, y):
    for x in range(x0, x1):
        if x % 3 != 1:
            setp(x, y, 'foam')


def mount_turtle(cx, cy):
    """giant sea turtle with a plated shell, moss patches, saddle and pennant"""
    def draw():
        wl = cy + 7
        _wake(cx - 34, wl - 1, 64, 4, 0.33, 501)
        _underwater(cx - 2, wl + 2, 40, 10)
        for (a, b, w0, w1, far) in [((cx + 12, cy - 8), (cx + 30, cy - 20), 4.5, 1.5, True),
                                    ((cx - 22, cy - 6), (cx - 32, cy - 13), 3.0, 1.2, True),
                                    ((cx + 12, cy + 6), (cx + 31, cy + 15), 4.5, 1.5, False),
                                    ((cx - 22, cy + 6), (cx - 32, cy + 12), 3.0, 1.2, False)]:
            pix = _limb_pix(a[0], a[1], b[0], b[1], w0, w1, bend=0.12 if far else -0.12)
            _shape(pix, _lit(pix, 'tskin_lt', 'tskin', 'tskin_dk'))
            if not far:
                for (x, y) in pix:
                    shade(x, y, 0.8)
                setp(b[0] + 2, b[1], 'foam'); setp(b[0] + 1, b[1] + 2, 'foam'); setp(b[0] - 2, b[1] + 2, 'foam')
        neck = _ellipse_pix(cx + 25, cy - 1, 8, 5)
        _shape(neck, _lit(neck, 'tskin_lt', 'tskin', 'tskin_dk'))
        hx_, hy_ = cx + 36, cy - 3
        head = _ellipse_pix(hx_, hy_, 10, 7)

        def hcol(x, y):
            nx, ny = (x - hx_) / 10, (y - hy_) / 7
            v = -(0.6 * nx + 0.8 * ny)
            c = 'tskin_lt' if v > 0.3 else ('tskin' if v > -0.35 else 'tskin_dk')
            if (x * 5 + y * 3) % 11 == 0 and v < 0.6:
                c = 'tskin_dk'
            return c
        _shape(head, hcol)
        sprite(hx_ + 2, hy_ - 4, ['kke', 'kkk'], {'k': 'eye', 'e': 'snow_lt'})
        for i in range(6):
            setp(hx_ + 4 + i, hy_ + 3 - i // 4, 'tskin_dk')
        sx, sy, rx, ry = cx - 4, cy - 2, 30, 16
        seeds = [(-14, -6), (0, -9), (14, -6), (-18, 4), (-4, 2), (10, 3), (22, -1)]
        shell = _ellipse_pix(sx, sy, rx, ry, ymax=wl)

        def scol(x, y):
            nx, ny = (x - sx) / rx, (y - sy) / ry
            d = nx * nx + ny * ny
            v = -(0.55 * nx + 0.85 * ny)
            if d > 0.74:
                ang = np.arctan2(ny, nx) * 7 / np.pi
                if abs(ang - round(ang)) < 0.12:
                    return 'shell_dk'
                return 'shell_rim' if v > 0 else 'shell'
            dd = sorted(((x - sx - px) ** 2 + ((y - sy - py) * 1.6) ** 2) ** 0.5 for (px, py) in seeds)
            if dd[1] - dd[0] < 1.6:
                return 'shell_dk'
            c = 'shell_lt' if v > 0.15 else ('shell' if v > -0.45 else 'shell_dk')
            if dd[0] < 2.5 and v > -0.3:
                c = 'shell_rim'
            if MOSS[y % HH, x % WW] > 0.6 and v > -0.2:
                c = 'leaf_lt' if v > 0.3 else 'leaf'
            return c
        _shape(shell, scol)
        _waterline(sx - rx + 3, sx + rx - 2, wl + 1)
        for y in range(sy - 22, sy - 8):                               # pennant on a pole at the back
            setp(sx - 20, y, 'trunk_dk')
        sprite(sx - 19, sy - 22, ['rrrr.', 'rrr..', 'rr...'], {'r': 'blanket'})
        _rider(cx, sy - 7)
    objects.append((cy + 18, draw))


def mount_whale(cx, cy):
    """gentle whale: tapered back above the water, rounded head, raised tail fluke, blowhole spout"""
    def draw():
        wl = cy + 4
        x0b, x1b, H = cx - 48, cx + 46, 17

        def half(x):
            u = (x - x0b) / (x1b - x0b)
            if u >= 0.6:
                return H * max(0.0, 1 - ((u - 0.6) / 0.4) ** 2) ** 0.5
            return H * (0.28 + 0.72 * np.sin(np.pi / 2 * u / 0.6))
        _wake(x0b - 6, wl, 40, 3, 0.3, 502)
        _underwater(cx - 2, wl + 3, 54, 11)
        sx_, sy_ = x0b - 9, cy - 6                                       # raised tail: stem + two lobes
        stem = _limb_pix(x0b + 3, cy - 2, sx_, sy_, 4, 3)
        lobes = _limb_pix(sx_, sy_, sx_ - 8, sy_ - 14, 4, 1.4, bend=0.18) | _limb_pix(sx_, sy_, sx_ - 8, sy_ + 11, 4, 1.4, bend=-0.18)
        tail = stem | lobes
        _shape(tail, lambda x, y: 'whale_lt' if y < sy_ - 6 else ('whale' if y < sy_ + 3 else 'whale_dk'))
        for (dx, dy) in ((-8, 9), (-4, 11), (0, 10), (-10, 7), (2, 8), (-6, 12)):
            setp(sx_ + dx, sy_ + dy, 'foam')
        body = set()
        for x in range(x0b, x1b + 1):
            h = half(x)
            for y in range(int(round(cy - h)), wl + 1):
                if y <= cy + h:
                    body.add((x, y))

        def bcol(x, y):
            h = max(1.0, half(x))
            ny = (y - cy) / h
            u = (x - x0b) / (x1b - x0b)
            c = 'whale_lt' if ny < -0.62 else ('whale' if ny < 0.05 else 'whale_dk')
            if (x * 7 + y * 3) % 19 == 0 and ny < 0.05:
                c = 'whale_lt'
            if u > 0.78 and ny < -0.3 and (x * 5 + y) % 5 == 0:
                c = 'cream'                                               # barnacles on the head
            return c
        _shape(body, bcol)
        for i, x in enumerate(range(cx - 40, cx - 12, 6)):              # knuckles along the spine
            yt = int(round(cy - half(x)))
            setp(x, yt + 2, 'whale_lt'); setp(x + 1, yt + 2, 'whale_lt'); setp(x + 1, yt + 3, 'whale_dk')
        ex = x1b - 9
        sprite(ex, wl - 4, ['kke', 'kkk'], {'k': 'eye', 'e': 'snow_lt'})
        for x in range(ex - 10, x1b - 1):
            setp(x, wl - 1, 'whale_dk')
        _waterline(x0b + 2, x1b, wl + 1)
        sp = np.random.default_rng(503)
        bh = x1b - 22
        for k in range(16):
            for _ in range(3):
                x = bh + int(round(sp.normal(0, 0.4 + k * 0.28)))
                setp(x, int(cy - half(bh)) - 2 - k, 'snow_lt' if k < 10 else 'foam')
        _rider(cx + 4, int(round(cy - half(cx + 4))) + 3)
    objects.append((cy + 18, draw))


def mount_manta(cx, cy):
    """manta ray gliding flat on the surface: wide wings, curled head fins, long tail"""
    def draw():
        _wake(cx - 18, cy, 50, 6, 0.4, 504)
        span = 30

        def inside(x, y):
            a = abs(y - cy) / span
            if a > 1:
                return False
            xf = cx + 24 - 26 * a ** 1.4
            xb = cx - 16 + 14 * a ** 0.8
            return xb <= x <= xf
        body = {(x, y) for y in range(cy - span, cy + span + 1) for x in range(cx - 20, cx + 26) if inside(x, y)}
        for (x, y) in body:                                               # its shadow in the water
            if _in_sea(x + 2, y + 4):
                shade(x + 2, y + 4, 0.72)
        for k in range(32):                                               # whip tail
            setp(cx - 16 - k, cy + int(round(k * 0.1 + np.sin(k / 6.0))), 'manta_dk')

        def mcol(x, y):
            c = 'manta'
            if not inside(x + 3, y):
                c = 'manta_lt'                                            # leading edge catches the light
            elif not inside(x - 3, y):
                c = 'manta_dk'                                            # trailing edge
            for (px, py) in ((-6, -9), (-6, 9), (-11, -4), (-11, 4)):
                if (x - cx - px) ** 2 + (y - cy - py) ** 2 <= 2:
                    c = 'cream'
            return c
        _shape(body, mcol)
        for sgn in (-1, 1):                                               # short forward head lobes
            lobe = _limb_pix(cx + 21, cy + sgn * 4, cx + 27, cy + sgn * 4, 1.7, 1.4)
            _shape(lobe, lambda x, y: 'manta_lt')
            sprite(cx + 18, cy + sgn * 7, ['ke'], {'k': 'eye', 'e': 'snow_lt'})
        for (tx, ty) in ((cx - 2, cy - span), (cx - 2, cy + span)):     # spray at the lifted wingtips
            for (dx, dy) in ((-2, 0), (0, -2), (1, 1), (-3, 2), (2, -1)):
                setp(tx + dx, ty + dy + (1 if ty > cy else -1), 'foam')
        for y in range(cy - span + 4, cy + span - 3):                    # foam along the trailing edge
            a = abs(y - cy) / span
            xb = int(round(cx - 16 + 14 * a ** 0.8))
            if y % 2 == 0:
                setp(xb - 1, y, 'foam')
        _rider(cx + 2, cy - 2)
    objects.append((cy + 32, draw))


def mount_crab(cx, cy):
    """giant hermit crab wearing an old ferry cabin; rider sits on the roof"""
    def draw():
        wl = cy + 6
        _wake(cx - 30, wl, 36, 4, 0.3, 505)
        _underwater(cx - 2, wl + 4, 38, 12)
        for side in (-1, 1):                                              # four jointed legs per side
            for i, lx in enumerate((cx - 18, cx - 8, cx + 2, cx + 12)):
                ky = cy + side * 12
                kx = lx + (i - 1.5) * 4
                fy = wl + (10 if side > 0 else -16) + (2 if i % 2 else 0)
                fx = kx + (i - 1.5) * 5
                for (a, b) in (((lx, cy), (kx, ky - 6)), ((kx, ky - 6), (fx, fy))):
                    pix = _limb_pix(a[0], a[1], b[0], b[1], 2.0, 1.4)
                    _shape(pix, _lit(pix, 'crab_lt', 'crab', 'crab_dk'))
                if side > 0:
                    setp(int(fx) - 1, int(fy) + 2, 'foam'); setp(int(fx) + 2, int(fy) + 2, 'foam')
        big = _ellipse_pix(cx + 32, cy + 6, 8, 6) | _limb_pix(cx + 14, cy + 2, cx + 26, cy + 6, 3, 3)
        _shape(big, _lit(big, 'crab_lt', 'crab', 'crab_dk'))
        for x in range(cx + 33, cx + 41):
            setp(x, cy + 6, 'ink')                                        # pincer gap
        small = _ellipse_pix(cx + 26, cy - 8, 5, 4) | _limb_pix(cx + 12, cy - 4, cx + 22, cy - 7, 2, 2)
        _shape(small, _lit(small, 'crab_lt', 'crab', 'crab_dk'))
        for (ex, top) in ((cx + 12, cy - 30), (cx + 17, cy - 28)):       # eyestalks
            for y in range(top + 3, cy - 18):
                setp(ex, y, 'crab_dk')
            sprite(ex - 1, top, ['kk', 'ke', 'kk'], {'k': 'eye', 'e': 'snow_lt'})
        x0, x1, ytop, ybot = cx - 20, cx + 16, cy - 20, wl
        for y in range(ytop, ybot + 1):                                   # the ferry cabin "shell"
            for x in range(x0, x1 + 1):
                k = (y - ytop) % 4
                c = 'wood_lt' if k == 0 else ('wood' if k < 3 else 'wood_dk')
                if x > x1 - 8:
                    c = 'wood' if k == 0 else 'wood_dk'
                if x in (x0, x1) or y == ybot:
                    c = 'ink'
                setp(x, y, c)
        for (px, py) in ((x0 + 7, ytop + 8), (x0 + 18, ytop + 8), (x0 + 29, ytop + 8)):   # portholes
            for (x, y) in _ellipse_pix(px, py, 3.2, 3.2):
                d = (x - px) ** 2 + (y - py) ** 2
                setp(x, y, 'gold' if d > 5 else ('cream' if (x - px) + (y - py) < -1 else 'glow'))
        for (x, y) in _ellipse_pix(x0 + 7, ytop + 16, 3, 2.5):          # life ring
            setp(x, y, 'blanket' if (x + y) % 3 else 'cream')
        for y in range(ytop - 5, ytop):                                   # roof with rail
            for x in range(x0 - 2, x1 + 3):
                c = 'roof_lt' if y == ytop - 5 else ('roof' if y < ytop - 1 else 'roof_ln')
                if x in (x0 - 2, x1 + 2):
                    c = 'ink'
                setp(x, y, c)
        for x in range(x0 - 1, x1 + 2, 4):
            setp(x, ytop - 6, 'iron'); setp(x, ytop - 7, 'iron')
        for x in range(x0 - 1, x1 + 2):
            setp(x, ytop - 8, 'iron')
        for y in range(ytop - 16, ytop - 5):                             # stovepipe + smoke
            setp(x0 + 3, y, 'iron'); setp(x0 + 4, y, 'rail_dk')
        sprite(x0 + 1, ytop - 22, ['.cc.', 'ccss', '.ss.'], {'c': 'tin_lt', 's': 'tin'})
        _waterline(x0 - 6, x1 + 8, wl + 1)
        _rider(cx - 2, ytop - 6)
    objects.append((cy + 20, draw))


def _side_full():
    """hero turned 3/4 toward the direction of travel, hat to belt (seated)"""
    g = [list(r) for r in CARTOGRAPHER[:18]]
    for x in range(5, 15):
        if g[8][x] in 'ks':
            g[8][x] = 'k' if x <= 8 or x in (11, 12) else 's'
    for y, xs in ((9, (5, 6, 7)), (10, (5, 6))):
        for x in range(5, 15):
            if g[y][x] in 'eksSq':
                g[y][x] = 'k' if x in xs else ('S' if x == 14 else 's')
    for y in (9, 10):
        g[y][10] = 'e'; g[y][13] = 'e'
    g[11][9] = 'q'; g[11][13] = 'q'
    return [''.join(r) for r in g]


def surf_mount(cx, cy, kind='otter'):
    """hero sits on top; the otter (Otter Stick) or seal (Seal Flute) is mostly under water"""
    lt, md, dk = ('otter_lt', 'otter', 'otter_dk') if kind == 'otter' else ('seal_lt', 'seal', 'seal_dk')
    X = lambda n: int(round(n + cx - 35))
    Y = lambda n: int(round(n + cy - 34))
    wl = cy

    def draw():
        for k in range(18):                                               # little wake behind
            for sgn in (-1, 1):
                x, y = X(36) - 24 - k, int(round(wl + 1 + sgn * (1 + k * 0.3)))
                if k % 3 and _in_sea(x, y):
                    setp(x, y, 'foam')
        for i, t in enumerate(np.linspace(0, 2 * np.pi, 72)):            # ripple ring
            x, y = int(round(X(36) + 22 * np.cos(t))), int(round(wl + 1 + 3 * np.sin(t)))
            if i % 6 < 4 and y >= wl and _in_sea(x, y):
                setp(x, y, 'foam')
        animal = set()

        def part(pix, colour):
            _shape(pix, colour)
            animal.update(pix)
        if kind == 'otter':
            part(_limb_pix(X(19), Y(35), X(6), Y(38), 3.0, 2.0), lambda x, y: md)
        else:
            for d in (-3, 3):
                part(_limb_pix(X(19), Y(35), X(10), Y(35 + d), 2.4, 1.4), lambda x, y: dk)
        part(_ellipse_pix(X(25), Y(39), 3, 2), lambda x, y: dk)
        part(_ellipse_pix(X(47), Y(38), 3, 2), lambda x, y: dk)
        body = _ellipse_pix(X(35), Y(34), 17, 7)

        def back(x, y):
            v = -(0.6 * (x - X(35)) / 17 + 0.8 * (y - Y(34)) / 7)
            return lt if v > 0.35 else (md if v > -0.35 else dk)
        part(body, back)
        sprite(X(24), Y(31) - len(SIDE_FULL) + 1, SIDE_FULL, CPAL)
        for (x, y) in body:                                               # near rim of the back seats the rider
            if y >= Y(31) and all((x + a, y + b_) in body for a, b_ in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                setp(x, y, back(x, y))
        hx_, hy_ = X(53), Y(32)
        if kind == 'otter':
            part(_ellipse_pix(hx_ - 4, hy_ - 5, 1.8, 1.8), lambda x, y: dk)
        head = _ellipse_pix(hx_, hy_, 6.5, 5)

        def hcol(x, y):
            v = -(0.6 * (x - hx_) / 6.5 + 0.8 * (y - hy_) / 5)
            return lt if v > 0.35 else (md if v > -0.35 else dk)
        part(head, hcol)
        part(_ellipse_pix(hx_ + 5, hy_ + 1, 3, 2), lambda x, y: 'muzzle' if kind == 'otter' else lt)
        setp(hx_ + 7, hy_, 'eye'); setp(hx_ + 8, hy_, 'eye')
        for dy in range(2 if kind == 'otter' else 3):
            setp(hx_ + 1, hy_ - 3 + dy, 'eye'); setp(hx_ + 2, hy_ - 3 + dy, 'eye')
        setp(hx_ + 1, hy_ - 3, 'snow_lt')
        for (x, y) in animal:                                             # everything below the waterline is under water
            if y > wl and 0 <= x < WW and 0 <= y < HH:
                setp(x, y, (img[y, x] * 0.38 + P['sea'] * 0.62).astype(np.uint8))
        for (x, y) in animal:
            if y == wl and x % 3 != 1:
                setp(x, wl + 1, 'foam')
    objects.append((cy + 8, draw))


SIDE_FULL = _side_full()
MOUNTS = {'mossback': lambda x, y: mossback(x, y), 'turtle': mount_turtle, 'whale': mount_whale,
          'manta': mount_manta, 'crab': mount_crab}


if SCENE == 'fennick':
    # ---- scene layout (world px; tile (c, r) starts at c*16, r*16) ----
    house(208, 12)
    tree(12, 40, 1.05); tree(26, 120, 0.9); tree(8, 150, 0.8)
    tree(104, 30, 1.0); pine(140, 46, 1.0); tree(176, 26, 0.9)
    tree(300, 36, 1.0); pine(330, 58, 0.9)
    tree(98, 128, 0.95); tree(296, 120, 1.0); tree(330, 104, 0.85)
    bush(132, 108); bush(256, 120); bush(70, 104)
    rock(120, 132); rock(236, 124, 9, 6); rock(62, 140, 6, 4)
    barrel(282, 62); barrel(291, 64); crate(198, 62); crate(203, 54)
    logs(318, 64)
    signpost(88, 63)
    lantern(188, 90)
    fence(192, 330, 136)
    jetty(184, 162, HH)
    rowboat(146, 176)
    player(168, 103)                         # mid-step, walking down toward the ledge
elif SCENE == 'canyon':
    shack(36, 24, 56, 38)
    shack(262, 28, 50, 34)
    ladder(128, int(edge_n[128]) - 3, int(edge_n[128]) + FACE_H)
    mine_frame(198, 226, int(edge_n[212]) + 10, int(edge_n[212]) + FACE_H)
    water_tower(318, 150)
    minecart(92, 129)
    ore_pile(240, 78); ore_pile(112, 152)
    crate(102, 72); crate(106, 64)
    barrel(250, 72); barrel(259, 74)
    lantern(186, 94)
    signpost(146, 88)
    for (x, y) in [(22, 98), (138, 108), (252, 110), (292, 98), (52, 136), (24, 164), (44, 156),
                   (60, 14), (150, 12), (262, 16), (330, 20), (236, 152)]:
        dry_shrub(x, y)
    rock(236, 142, 9, 6); rock(130, 172); rock(284, 174, 8, 5)
    player(168, 103)
elif SCENE == 'sea' and WW <= 400:
    tree(28, 40, 0.95); pine(62, 30, 0.9); bush(80, 52); rock(18, 58); bush(46, 60)
    stilt_hut(92, 62)
    pine(322, 32, 0.8); bush(300, 42)
    wreck(56, 176)
    sea_stack(262, 96, 18, 22); sea_stack(292, 172, 12, 13)
    buoy(214, 136)
    gull(116, 98); gull(236, 46)
    surf_mount(168, 104, OPTS.get('mount', 'otter'))
elif SCENE == 'sea':
    tree(70, 78, 0.95); tree(112, 122, 1.0); pine(150, 70, 0.95); tree(176, 110, 0.85); pine(58, 122, 0.8)
    bush(92, 92); bush(184, 132); bush(40, 100); rock(140, 136, 8, 5); rock(100, 60)
    stilt_hut(196, 104)
    tree(500, 66, 0.85); rock(522, 80); bush(482, 74)
    pine(610, 108, 0.75); bush(590, 122); rock(624, 120, 6, 4)
    rope_bridge((540, 74), (578, 104))
    tree(548, 288, 0.95); pine(600, 282, 0.85); bush(580, 306); rock(530, 304)
    wreck(150, 306)
    sea_stack(386, 94, 22, 26); sea_stack(252, 322, 16, 20); sea_stack(452, 347, 12, 13)
    buoy(292, 150); buoy(430, 232)
    gull(268, 110); gull(420, 160); gull(470, 250)
    MOUNTS[OPTS.get('mount', 'turtle')](328, 186)
elif SCENE == 'snow':
    stone_cottage(30, 18, 60)
    stone_cottage(236, 22, 58)
    for (x, y, s_) in [(120, 44, 1.0), (206, 40, 0.9), (312, 104, 1.0), (334, 76, 0.9), (16, 108, 1.0),
                       (230, 150, 0.95), (290, 180, 1.05), (196, 186, 0.9), (52, 166, 0.55)]:
        pine_snow(x, y, s_)
    cairn(66, 172)
    wall_snow(196, 336, 124)
    well(124, 96)
    lantern(188, 94)
    signpost(146, 86)
    sled(262, 96)
    rock_snow(232, 112); rock_snow(276, 146, 10, 6); rock_snow(176, 160)
    crate(304, 62); barrel(216, 58)
    player(168, 103)
elif SCENE == 'forest':
    hollow_oak(168, 70)
    for (x, y, s_) in [(22, 46, 1.05), (88, 62, 1.0), (14, 104, 1.1), (58, 118, 0.95), (30, 160, 1.1), (96, 176, 1.0),
                       (246, 50, 1.0), (320, 60, 1.1), (236, 112, 0.95), (326, 128, 1.05), (254, 170, 1.1),
                       (318, 186, 1.0), (140, 214, 1.3), (212, 212, 1.25)]:
        tree(x, y, s_)
    for (x, y, s_) in [(52, 30, 1.0), (104, 108, 0.9), (126, 152, 0.85), (282, 36, 1.0), (276, 104, 1.0), (210, 160, 0.85)]:
        pine(x, y, s_)
    for (x, y) in [(70, 98), (78, 102), (202, 122), (210, 126), (296, 90), (22, 136), (232, 102)]:
        fern(x, y)
    mushrooms(78, 134); mushrooms(268, 130); mushrooms(196, 104)
    fallen_log(36, 92, 144)
    stump(214, 90)
    bush(122, 98); bush(242, 80); bush(302, 120)
    rock(196, 134); rock(62, 184)
    player(168, 103)

for (cx_, cy_, rx_, ry_) in shadows:
    drop_shadow(cx_, cy_, rx_, ry_)
REC[0] = True
if SCENE == 'fennick':
    bridge(44, 84, 66, 79)()
for _, fn in sorted(objects, key=lambda o: o[0]):
    fn()
REC[0] = False
if OUTLINE == 'bold':      # dark outline around every object silhouette
    img[OBJ & ~ero(OBJ, 1)] = P['ink']
elif OUTLINE in ('soft', 'none'):
    # coloured outlines: each outline pixel becomes a darker shade of the object it borders,
    # lighter on the sun side (top/left), darker on the shadow side (bottom/right)
    f_lit, f_dark = (0.84, 0.6) if OUTLINE == 'soft' else (1.0, 0.92)
    src = img.copy()
    inner = OBJ & ~OUTL

    def outside(yy, xx):
        return not (0 <= yy < HH and 0 <= xx < WW) or not OBJ[yy, xx]
    for y, x in zip(*np.where(OUTL)):
        acc = [src[yy, xx] for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)
               if 0 <= yy < HH and 0 <= xx < WW and inner[yy, xx]]
        base = np.mean(acc, axis=0) if acc else src[y, x].astype(float) + 50
        lit = (outside(y - 1, x) or outside(y, x - 1)) and not (outside(y + 1, x) or outside(y, x + 1))
        img[y, x] = np.clip(base * (f_lit if lit else f_dark), 0, 255).astype(np.uint8)

if SCENE == 'snow':                     # falling snow over the world (not the HUD)
    fr = np.random.default_rng(208)
    for _ in range(240):
        x, y = int(fr.integers(0, WW - 1)), int(fr.integers(0, HH))
        img[y, x] = P['snow_lt']
        if fr.random() < 0.3:
            img[y, x + 1] = P['snow_lt']
elif SCENE == 'forest' and OPTS.get('sunbeams'):   # optional sunbeams through the canopy
    sft = XX * 0.5 + YY
    band = ((sft >= 150) & (sft < 162)) | ((sft >= 262) & (sft < 278))
    core = ((sft >= 154) & (sft < 158)) | ((sft >= 267) & (sft < 273))
    m = band & (core | ((XX + YY) % 2 == 0)) & (XX > 40) & (XX < 320) & (YY < 176)
    img[m] = np.clip(img[m].astype(float) * 1.22 + 8, 0, 255).astype(np.uint8)

# ------------------------------------------------------------------ camera, scale, tilt-shift
frame = img[CROP_Y:CROP_Y + VH, CROP_X:CROP_X + VW]
def to_lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192], [0.1805, 0.0722, 0.9505]])
    xyz = xyz / [0.95047, 1.0, 1.08883]
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


if OPTS.get('quantize') is not None:       # limited retro palette, matched perceptually (CIELAB)
    qp = np.array([hx(c) for c in OPTS['quantize']], float)
    f = frame.reshape(-1, 3).astype(float)
    uniq, inv = np.unique(f, axis=0, return_inverse=True)
    pick = np.argmin(((to_lab(uniq)[:, None, :] - to_lab(qp)[None]) ** 2).sum(-1), axis=1)
    frame = qp[pick][inv.ravel()].reshape(frame.shape).astype(np.uint8)
if ZOOM == 2:
    frame = frame[VH // 4:VH // 4 + VH // 2, VW // 4:VW // 4 + VW // 2]
big = Image.fromarray(np.ascontiguousarray(frame)).resize((VW * SCALE, VH * SCALE), Image.NEAREST)
strong = OPTS.get('tilt') == 'strong'
blur = big.filter(ImageFilter.GaussianBlur(8 if strong else 5))
band = int(VH * SCALE * (0.34 if strong else 0.24))
a = np.zeros((VH * SCALE, VW * SCALE), np.float32)
ys = np.arange(VH * SCALE)
top = np.clip((band - ys) / band, 0, 1) ** 1.3
bot = np.clip((ys - (VH * SCALE - band)) / band, 0, 1) ** 1.3
a[:] = np.maximum(top, bot)[:, None]
out = (np.array(big, np.float32) * (1 - a[..., None]) + np.array(blur, np.float32) * a[..., None]).astype(np.uint8)

# ------------------------------------------------------------------ HUD (pixel font, never blurred)
FONT = {
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'C': ['.####', '#....', '#....', '#....', '#....', '#....', '.####'],
    'D': ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
    'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
    'F': ['#####', '#....', '#....', '####.', '#....', '#....', '#....'],
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
    '3': ['####.', '....#', '....#', '.###.', '....#', '....#', '####.'],
    '4': ['#...#', '#...#', '#...#', '#####', '....#', '....#', '....#'],
    '5': ['#####', '#....', '#....', '####.', '....#', '....#', '####.'],
    '6': ['.###.', '#....', '#....', '####.', '#...#', '#...#', '.###.'],
    '7': ['#####', '....#', '...#.', '..#..', '..#..', '..#..', '..#..'],
    '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
    '9': ['.###.', '#...#', '#...#', '.####', '....#', '....#', '.###.'],
    'V': ['#...#', '#...#', '#...#', '#...#', '.#.#.', '.#.#.', '..#..'],
    'J': ['..###', '...#.', '...#.', '...#.', '...#.', '#..#.', '.##..'],
    'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
    'P': ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'],
    'G': ['.####', '#....', '#....', '#.###', '#...#', '#...#', '.###.'],
    'H': ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'I': ['.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    'K': ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'],
    'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
    'M': ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'],
    'N': ['#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#', '#...#'],
    'O': ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'],
    'Y': ['#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'],
    '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    ' ': ['...', '...', '...', '...', '...', '...', '...'],
    '-': ['....', '....', '....', '###.', '....', '....', '....'],
}
VW, VH, SCALE = 320, 180, 4           # HUD canvas is fixed, whatever the world zoom
hud = np.zeros((VH, VW, 4), np.uint8)


def hset(x, y, col):
    if 0 <= x < VW and 0 <= y < VH:
        hud[y, x, :3] = P[col]; hud[y, x, 3] = 255


def hrect(x0, y0, x1, y1, col):
    for y in range(y0, y1):
        for x in range(x0, x1):
            hset(x, y, col)


def htext(x, y, s, col, shadow='ink'):
    for ch in s:
        g = FONT[ch]
        for dy, row in enumerate(g):
            for dx, c in enumerate(row):
                if c == '#':
                    hset(x + dx, y + dy + 1, shadow)
                    hset(x + dx, y + dy, col)
        x += len(g[0]) + 1
    return x


def text_w(s):
    return sum(len(FONT[c][0]) + 1 for c in s) - 1


# area banner (top-left), shown on entering a route
name, sub = {'fennick': ('LAUVDAL', 'TO KEELVIK'), 'canyon': ('REDSKAR', 'MINING TOWN'),
             'sea': ('THE SMAHOLMS', 'ROUTE 25'), 'snow': ('FJELLTARN', 'HIGHLAND TOWN'),
             'forest': ('HOLEIK WOOD', 'ROUTE 7')}[SCENE]
w = text_w(name) + 14
hrect(6, 6, 6 + w, 22, 'ink')
hrect(7, 7, 5 + w, 21, 'trunk_dk')
hrect(8, 8, 4 + w, 20, 'ink')
htext(13, 10, name, 'cream')
hrect(13, 18, 13 + text_w(name), 19, 'gold')
hrect(6, 22, 8 + text_w(sub) + 6, 31, 'ink')
htext(10, 23, sub, 'sand_dk')
# season badge (top-right)
label = 'WINTER' if SCENE == 'snow' else 'SUMMER'
bw = text_w(label) + 22
bx0 = VW - 6 - bw
hrect(bx0, 6, VW - 6, 22, 'ink')
hrect(bx0 + 1, 7, VW - 7, 21, 'trunk_dk')
hrect(bx0 + 2, 8, VW - 8, 20, 'ink')
sun = ['..y..', 'y.y.y', '.yyy.', 'yyyyy', '.yyy.', 'y.y.y', '..y..']
flake = ['y.y.y', '.y.y.', 'yyyyy', '.y.y.', 'y.y.y', '.....', '.....']
for dy, row in enumerate(flake if SCENE == 'snow' else sun):
    for dx, c in enumerate(row):
        if c == 'y':
            hset(bx0 + 6 + dx, 10 + dy + (1 if SCENE == 'snow' else 0), 'frz' if SCENE == 'snow' else 'gold')
htext(bx0 + 15, 10, label, 'cream')

hud_big = Image.fromarray(hud, 'RGBA').resize((VW * SCALE, VH * SCALE), Image.NEAREST)
final = Image.fromarray(out).convert('RGBA')
final.alpha_composite(hud_big)
if __name__ == '__main__':
    dst = sys.argv[1] if len(sys.argv) > 1 else 'ingame_mockup.png'
    final.convert('RGB').save(dst)
    print('saved', dst, final.size)
