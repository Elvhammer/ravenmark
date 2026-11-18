"""Builds every asset the Godot prototype needs (Keelvik, Lauvdal, Sule Ness and the coast).

    python3 proto_build.py

Writes into ../game:
  data/world.json, data/sprites.json
  art/ground/ground_<season>.png      (whole map, one per season, shadows baked in)
  art/objects/<kind>_<season>.png     (y-sorted sprites)
  art/hero/hero_<layer>.png           (body / pouch / stick; rows: down, up, right; 4 frames of 20x24)
  art/mounts/surf_<otter|seal>.png    (rows: down, up, right; 4 frames of 72x48)
  art/hud/*.png                       (pixel-font banners, season badges, messages, help, item icons)
All art is drawn in the chosen style (retro 16-colour palette, medium detail, soft coloured outlines).
"""
import json
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
GAME = os.path.join(os.path.dirname(HERE), 'game')
ART = os.path.join(GAME, 'art')
import proto_map as MAP                     # noqa: E402  (builds the map + world.json)
import make_style_sheets as MS              # noqa: E402
import mount_ideas as MI                    # noqa: E402  (loads the mock renderer + palette)

G = MI.G['setp'].__globals__                # live globals of the mock renderer: P, setp, tree(), house_v2(), ...
hx, to_lab = G['hx'], G['to_lab']
QP = np.array([hx(c) for c in MS.RETRO16], float)
QL = to_lab(QP)
P0 = {k: v.copy() for k, v in G['P'].items()}
SEASONS = ['spring', 'summer', 'autumn', 'winter']
TS = 16


def quantize(a):
    f = a.reshape(-1, 3).astype(float)
    uniq, inv = np.unique(f, axis=0, return_inverse=True)
    pick = np.argmin(((to_lab(uniq)[:, None, :] - QL[None]) ** 2).sum(-1), axis=1)
    return QP[pick][inv.ravel()].reshape(a.shape).astype(np.uint8)


def C(h):
    return hx(h)


def save_rgba(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr, 'RGBA' if arr.shape[2] == 4 else 'RGB').save(path)


# ------------------------------------------------------------------ season palettes (retro colours)
LEAF = {
    'spring': ('#4F7A3C', '#8DB054', '#C6D66E', '#C6D66E'),
    'summer': ('#2F4A35', '#4F7A3C', '#8DB054', '#C6D66E'),
    'autumn': ('#6E4A35', '#A8693F', '#E0A256', '#E0A256'),
    'winter': ('#1E1B2C', '#2F4A35', '#4F7A3C', '#4F7A3C'),
}
LEAF_ALT = {   # 'oak_red': cherry in spring, darker green in summer, red in autumn
    'spring': ('#4F7A3C', '#E48A73', '#F2E3B3', '#F2E3B3'),
    'summer': ('#1E1B2C', '#2F4A35', '#4F7A3C', '#8DB054'),
    'autumn': ('#3D3550', '#B8483A', '#E48A73', '#E0A256'),
    'winter': ('#1E1B2C', '#2F4A35', '#4F7A3C', '#4F7A3C'),
}
SNOW, SNOW_SH = C('#F2E3B3'), C('#9CD0C9')


def set_palette(season, leaf=LEAF, extra=None):
    P = G['P']
    for k, v in P0.items():
        P[k] = v.copy()
    dk, md, lt, hi = leaf[season]
    for k, v in (('leaf_dk', dk), ('leaf', md), ('leaf_lt', lt), ('leaf_hi', hi), ('oak_dk', dk), ('oak', md), ('oak_hi', lt)):
        P[k] = C(v)
    if season == 'winter':
        for k in ('flower_a', 'flower_b', 'flower_c'):
            P[k] = C('#6E4A35')
    for k, v in (extra or {}).items():
        P[k] = C(v)


# ------------------------------------------------------------------ object sprites via the mock renderer
def render_sprite(draw, season, size=(128, 128), anchor=(64, 112), leaf=LEAF, extra=None, sea=False, snow=None):
    """run a mock-renderer object on a blank canvas; returns (rgba sprite, shadow factor map, anchor)"""
    Wc, Hc = size
    set_palette(season, leaf, extra)
    G['img'] = np.full((Hc, Wc, 3), 128, np.uint8)
    G['WW'], G['HH'] = Wc, Hc
    G['OBJ'] = np.zeros((Hc, Wc), bool)
    G['OUTL'] = np.zeros((Hc, Wc), bool)
    G['sea'] = np.full((Hc, Wc), sea)
    G['fresh'] = np.zeros((Hc, Wc), bool)
    G['MOSSF'] = np.zeros((Hc, Wc))
    G['objects'].clear()
    G['shadows'].clear()
    G['REC'][0] = False
    draw(anchor[0], anchor[1])
    G['REC'][0] = True
    for _, fn in sorted(G['objects'], key=lambda o: o[0]):
        fn()
    G['REC'][0] = False
    img, OBJ, OUTL = G['img'], G['OBJ'], G['OUTL']
    shadow = np.ones((Hc, Wc))
    moved = (~OBJ) & (img[..., 0] != 128)
    shadow[moved] = img[moved, 0] / 128.0
    for (cx, cy, rx, ry) in G['shadows']:
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if 0 <= x < Wc and 0 <= y < Hc:
                    d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                    if d <= 0.62:
                        shadow[y, x] = min(shadow[y, x], 0.66)
                    elif d <= 1.0 and (x + y) % 2 == 0:
                        shadow[y, x] = min(shadow[y, x], 0.78)
    src = img.copy()                                         # soft coloured outlines (as in the mockups)
    inner = OBJ & ~OUTL
    for y, x in zip(*np.where(OUTL & OBJ)):
        acc = [src[yy, xx] for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)
               if 0 <= yy < Hc and 0 <= xx < Wc and inner[yy, xx]]
        base = np.mean(acc, axis=0) if acc else src[y, x].astype(float) + 50
        out = lambda yy, xx: not (0 <= yy < Hc and 0 <= xx < Wc) or not OBJ[yy, xx]
        lit = (out(y - 1, x) or out(y, x - 1)) and not (out(y + 1, x) or out(y, x + 1))
        img[y, x] = np.clip(base * (0.84 if lit else 0.6), 0, 255).astype(np.uint8)
    rgba = np.zeros((Hc, Wc, 4), np.uint8)
    rgba[..., :3] = quantize(img)
    rgba[..., 3] = OBJ * 255
    if season == 'winter' and snow:
        snow_cap(rgba, snow)
    return rgba, shadow, anchor


def snow_cap(rgba, depth=2):
    """winter: snow on every upward-facing surface"""
    a = rgba[..., 3] > 0
    Hc, Wc = a.shape
    for x in range(Wc):
        for y in range(1, Hc):
            if a[y, x] and not a[y - 1, x]:
                for k in range(depth):
                    if y + k < Hc and a[y + k, x]:
                        rgba[y + k, x, :3] = SNOW if (k == 0 or x % 3) else SNOW_SH


def crop(rgba, anchor):
    ys, xs = np.where(rgba[..., 3] > 0)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return rgba[y0:y1, x0:x1], (anchor[0] - x0, anchor[1] - y0)


def draw_ship(ax, ay):
    """half-built ship on its stocks in the dry dock (anchor = bottom-left of the dock)"""
    setp, shade = G['setp'], G['shade']
    G['shadows'].append((ax + 52, ay - 2, 52, 5))

    def draw():
        x0, x1, keel = ax + 4, ax + 92, ay - 8
        for bx in range(x0 + 4, x1 - 4, 14):                  # cradle blocks
            for y in range(keel + 2, ay):
                for x in range(bx, bx + 5):
                    setp(x, y, 'trunk_dk' if x == bx + 4 or y == ay - 1 else 'trunk')
        for x in range(x0, x1):                               # keel
            setp(x, keel, 'wood_lt'); setp(x, keel + 1, 'wood'); setp(x, keel + 2, 'ink')
        n = 11
        tops = []
        for i in range(n):                                    # ribs (frames)
            rx = x0 + 6 + i * 8
            h = int(6 + 26 * np.sin(np.pi * (i + 0.6) / (n + 0.2)) ** 0.6)
            tops.append((rx, keel - h))
            for k in range(h):
                y = keel - k
                bow = int(round(2 * np.sin(np.pi * k / max(h, 1))))
                setp(rx - bow, y, 'wood_lt'); setp(rx - bow + 1, y, 'wood_dk')
        for i, (rx, ty) in enumerate(tops):                   # planking on the lower hull, left two thirds
            if i < 7:
                for y in range(int(keel - (keel - ty) * 0.55), keel):
                    for x in range(rx - 4, rx + 4):
                        k = (y - keel) % 3
                        setp(x, y, 'wood_lt' if k == 0 else ('wood' if k == 1 else 'wood_dk'))
        for k in range(44):                                   # stem post (bow) + sternpost
            setp(x1 + int(round(k * 0.18)), keel - k, 'wood_dk'); setp(x1 + int(round(k * 0.18)) - 1, keel - k, 'wood')
        for k in range(34):
            setp(x0 - 1, keel - k, 'wood_dk'); setp(x0, keel - k, 'wood')
        for px in (x0 + 18, x0 + 66):                         # scaffold poles + plank
            for y in range(ay - 52, ay):
                setp(px, y, 'trunk'); setp(px + 1, y, 'trunk_dk')
        for x in range(x0 + 14, x0 + 72):
            setp(x, ay - 42, 'wood_lt'); setp(x, ay - 41, 'wood_dk')
        for k in range(30):                                   # ladder leaning on the plank
            y = ay - 1 - k
            x = x0 + 76 - k // 4
            setp(x, y, 'wood_lt'); setp(x + 5, y, 'wood_dk')
            if k % 4 == 0:
                for xx in range(x + 1, x + 5):
                    setp(xx, y, 'wood')
    G['objects'].append((ay, draw))


def draw_lighthouse(ax, ay):
    setp = G['setp']
    G['shadows'].append((ax + 14, ay, 16, 4))

    def draw():
        for y in range(ay - 12, ay + 1):                      # stone base
            w = 13
            for x in range(ax - w, ax + w + 1):
                c = 'stone_lt' if x < ax - 4 else ('stone' if x < ax + 6 else 'stone_dk')
                if (y - ay) % 4 == 0 or (x + (2 if ((y - ay) // 4) % 2 else 0)) % 6 == 0:
                    c = 'stone_dk'
                if x in (ax - w, ax + w) or y == ay:
                    c = 'ink'
                setp(x, y, c)
        top = ay - 62
        for y in range(top, ay - 12):                         # tapered striped tower
            t = (y - top) / (ay - 12 - top)
            w = int(round(6 + 3 * t))
            red = ((y - top) // 9) % 2 == 0
            for x in range(ax - w, ax + w + 1):
                lit = x < ax - w // 3
                c = ('roof_lt' if lit else 'roof') if red else ('wall' if lit else 'wall_sh')
                if x >= ax + w - 1:
                    c = 'roof_dk' if red else 'wall_dk'
                if x in (ax - w, ax + w):
                    c = 'ink'
                setp(x, y, c)
        for wy in (top + 14, top + 32):                       # little windows
            for y in range(wy, wy + 4):
                setp(ax - 1, y, 'glass'); setp(ax, y, 'glass'); setp(ax + 1, y, 'ink')
        for x in range(ax - 9, ax + 10):                      # gallery + railing
            setp(x, top, 'ink'); setp(x, top - 1, 'iron')
            if x % 3 == 0:
                setp(x, top - 2, 'iron'); setp(x, top - 3, 'iron')
        for x in range(ax - 9, ax + 10):
            setp(x, top - 4, 'iron')
        for y in range(top - 12, top - 4):                    # lamp room
            for x in range(ax - 5, ax + 6):
                c = 'glow' if (x - ax) % 4 else 'ink'
                if y in (top - 12, top - 5) or x in (ax - 5, ax + 5):
                    c = 'ink'
                setp(x, y, c)
        for r in range(6):                                    # red cap + finial
            for x in range(ax - 6 + r, ax + 7 - r):
                setp(x, top - 13 - r, 'ink' if x in (ax - 6 + r, ax + 6 - r) or r == 0 else ('roof_lt' if x < ax else 'roof'))
        setp(ax, top - 20, 'iron'); setp(ax, top - 21, 'gold')
    G['objects'].append((ay, draw))


def draw_rack(ax, ay):
    """fish-drying rack"""
    setp = G['setp']
    G['shadows'].append((ax + 5, ay, 12, 2))

    def draw():
        for px in (ax - 10, ax + 10):
            for k in range(20):
                setp(px + (1 if k > 10 else 0) * (1 if px > ax else -1), ay - k, 'trunk'); setp(px + 1, ay - k, 'trunk_dk')
        for x in range(ax - 11, ax + 13):
            setp(x, ay - 19, 'wood_lt'); setp(x, ay - 18, 'wood_dk')
        for fx in range(ax - 8, ax + 10, 4):                  # hanging fish
            for k in range(7):
                setp(fx, ay - 17 + k, 'stone_lt' if k < 5 else 'stone_dk')
                setp(fx + 1, ay - 17 + k, 'stone' if k < 5 else 'ink')
    G['objects'].append((ay, draw))


def draw_chest(ax, ay, opened=False):
    setp = G['setp']
    G['shadows'].append((ax + 3, ay, 8, 2))

    def draw():
        x0 = ax - 7
        for y in range(ay - 9, ay + 1):                       # box
            for x in range(x0, x0 + 15):
                c = 'wood' if x < x0 + 10 else 'wood_dk'
                if (y - ay) % 4 == 0:
                    c = 'wood_dk'
                if x in (x0 + 3, x0 + 11):
                    c = 'iron'
                if x in (x0, x0 + 14) or y == ay:
                    c = 'ink'
                setp(x, y, c)
        if opened:
            for y in range(ay - 16, ay - 9):
                for x in range(x0, x0 + 15):
                    c = 'wood_lt' if y < ay - 13 else 'mine'
                    if x in (x0, x0 + 14) or y == ay - 16:
                        c = 'ink'
                    setp(x, y, c)
            setp(x0 + 6, ay - 11, 'gold'); setp(x0 + 9, ay - 12, 'cream')
        else:
            for y in range(ay - 14, ay - 9):                  # rounded lid
                for x in range(x0, x0 + 15):
                    c = 'wood_lt' if y < ay - 12 and x < x0 + 10 else 'wood'
                    if x in (x0 + 3, x0 + 11):
                        c = 'iron'
                    if x in (x0, x0 + 14) or y == ay - 14:
                        c = 'ink'
                    if y == ay - 14 and x in (x0, x0 + 14):
                        continue
                    setp(x, y, c)
            for (x, y) in ((x0 + 6, ay - 10), (x0 + 7, ay - 10), (x0 + 6, ay - 9), (x0 + 7, ay - 9)):
                setp(x, y, 'gold')
    G['objects'].append((ay, draw))


def draw_fence(ax, ay):
    """one 16 px fence segment (post on the left) so segments tile seamlessly"""
    setp, shade = G['setp'], G['shade']

    def draw():
        for (ry, sag) in ((ay - 8, 0), (ay - 4, 1)):
            for x in range(ax - 8, ax + 8):
                s_ = int(round(sag * np.sin(np.pi * (x - ax + 8) / 16)))
                setp(x, ry + s_, 'wood_lt'); setp(x, ry + s_ + 1, 'wood_dk')
        px = ax - 8
        for yy in range(ay - 11, ay + 1):
            for i, c in enumerate(('wood_lt', 'wood', 'wood_dk')):
                setp(px + i, yy, c)
        setp(px + 1, ay - 12, 'wood_lt')
        shade(px + 3, ay, 0.7); shade(px + 4, ay, 0.8)
    G['objects'].append((ay, draw))


HOUSE_B = {'roof_lt': '#8A8496', 'roof': '#5E6372', 'roof_dk': '#3D3550', 'roof_ln': '#2A2438',
           'wall': '#C4503E', 'wall_sh': '#A8463A', 'wall_dk': '#8E3F2E'}
HOUSE_SNOW = {'roof_lt': '#F2E3B3', 'roof': '#F2E3B3', 'roof_dk': '#9CD0C9', 'roof_ln': '#9CD0C9'}

KINDS = {   # kind: (draw(ax, ay), canvas size, anchor, options)
    'oak': (lambda x, y: G['tree'](x, y, 1.0), (72, 72), (36, 66), {'snow': 4}),
    'oak_red': (lambda x, y: G['tree'](x, y, 0.9), (72, 72), (36, 66), {'leaf': LEAF_ALT, 'snow': 4}),
    'pine': (lambda x, y: G['pine'](x, y, 1.0), (48, 64), (24, 58), {}),
    'bush': (lambda x, y: G['bush'](x, y), (32, 24), (16, 20), {'snow': 2}),
    'rock': (lambda x, y: G['rock'](x, y), (24, 16), (12, 13), {'snow': 2}),
    'rock_big': (lambda x, y: G['rock'](x, y, 11, 7), (32, 20), (16, 16), {'snow': 2}),
    'house_a': (lambda x, y: G['house_v2'](x, y - 52), (96, 80), (8, 72), {'snow': 1}),
    'house_b': (lambda x, y: G['house_v2'](x, y - 52), (96, 80), (8, 72), {'extra': HOUSE_B, 'snow': 1}),
    'ship': (draw_ship, (128, 80), (12, 72), {'snow': 2}),
    'lighthouse': (draw_lighthouse, (48, 104), (24, 96), {'snow': 2}),
    'barrel': (lambda x, y: G['barrel'](x, y), (24, 24), (12, 20), {'snow': 2}),
    'crate': (lambda x, y: G['crate'](x, y), (24, 24), (12, 20), {'snow': 2}),
    'logs': (lambda x, y: G['logs'](x, y), (40, 32), (20, 26), {'snow': 2}),
    'sign': (lambda x, y: G['signpost'](x, y), (24, 28), (8, 24), {'snow': 1}),
    'lamp': (lambda x, y: G['lantern'](x, y), (16, 32), (8, 28), {'snow': 1}),
    'fence': (draw_fence, (32, 20), (12, 16), {'snow': 1}),
    'rack': (draw_rack, (40, 32), (20, 28), {'snow': 1}),
    'boat': (lambda x, y: G['rowboat'](x, y), (48, 32), (24, 16), {'sea': True, 'snow': 1}),
    'chest': (lambda x, y: draw_chest(x, y), (24, 24), (12, 20), {'snow': 1}),
    'chest_open': (lambda x, y: draw_chest(x, y, True), (24, 28), (12, 24), {}),
}


def build_objects():
    """render every object kind in every season; returns manifest + shadow stamps"""
    manifest, stamps = {}, {}
    winter_house = dict(HOUSE_SNOW)
    for kind, (fn, size, anchor, opt) in KINDS.items():
        for season in SEASONS:
            extra = dict(opt.get('extra', {}))
            extra.update(opt.get('extra_season', {}).get(season, {}))
            if season == 'winter' and (kind.startswith('house') or kind == 'cabin'):
                extra.update(winter_house)
            if kind == 'pine' and season == 'winter':
                fn_ = lambda x, y: G['pine_snow'](x, y, 1.0)
            else:
                fn_ = fn
            rgba, shadow, anc = render_sprite(fn_, season, size, anchor, opt.get('leaf', LEAF), extra,
                                              opt.get('sea', False), opt.get('snow'))
            spr, (ox, oy) = crop(rgba, anc)
            save_rgba(spr, os.path.join(ART, 'objects', f'{kind}_{season}.png'))
            manifest[kind] = {'ox': int(ox), 'oy': int(oy), 'w': int(spr.shape[1]), 'h': int(spr.shape[0])}
            if season == 'summer':
                stamps[kind] = (shadow, anc)
    return manifest, stamps


# ------------------------------------------------------------------ ground
def build_ground(season, stamps, T=None, objects=None, scenery='home'):
    T = T if T is not None else MAP.T
    objects = objects if objects is not None else MAP.objects
    Wt, Ht = len(T[0]), len(T)
    WW, HH = Wt * TS, Ht * TS
    tg = np.array(T)
    YY, XX = np.mgrid[0:HH, 0:WW]
    R = np.random.default_rng(5).random((HH, WW))
    BAY = G['BAYER'][YY % 4, XX % 4]
    sn = G['smooth_noise']

    def km(chars):
        return np.kron(np.isin(tg, list(chars)).astype(np.uint8), np.ones((TS, TS), np.uint8)).astype(bool)

    def warp(m, amp, cell, seed):
        dx = (sn(WW, HH, cell, seed) * amp).round().astype(int)
        dy = (sn(WW, HH, cell, seed + 1) * amp).round().astype(int)
        return m[np.clip(YY + dy, 0, HH - 1), np.clip(XX + dx, 0, WW - 1)]

    def dil(m, r):
        o = m.copy()
        for _ in range(r):
            n = o.copy()
            n[1:] |= o[:-1]; n[:-1] |= o[1:]; n[:, 1:] |= o[:, :-1]; n[:, :-1] |= o[:, 1:]
            o = n
        return o

    def ero(m, r):
        return ~dil(~m, r)

    def rounded(m, r):
        return dil(ero(dil(ero(m, r), r), r), r)

    set_palette(season)
    Pal = dict(G['P'])
    if season == 'spring':
        Pal.update({k: C(v) for k, v in {'grass_lt': '#C6D66E', 'grass_hi': '#C6D66E'}.items()})
    if season == 'autumn':
        Pal.update({k: C(v) for k, v in {'grass_lt': '#E0A256', 'grass_hi': '#E0A256', 'grass_dk2': '#A8693F'}.items()})
    if scenery == 'east':                                   # the far side: terracotta paths, pink petals
        Pal.update({k: C(v) for k, v in {'path': '#E48A73', 'path_md': '#B8483A', 'path_dk': '#A8693F',
                                          'flower_a': '#E48A73', 'flower_b': '#F2E3B3', 'flower_c': '#E48A73'}.items()})
    img = np.zeros((HH, WW, 3), np.uint8)

    def paint(m, col):
        img[m] = Pal[col] if isinstance(col, str) else col

    sea = warp(rounded(km('~!blO'), 6), 3, 9, 20)
    ocean = sea & warp(rounded(km('O'), 6), 4, 12, 22)
    cold = sea & warp(rounded(km('!'), 8), 5, 14, 21)
    water = warp(rounded(km('='), 5), 2, 7, 10) & ~sea
    reeds = warp(rounded(km('"'), 4), 2, 7, 11) & ~sea
    sand = warp(rounded(km('.~!blO'), 6), 3, 9, 20) & ~sea
    plank = km('w')
    path = warp(rounded(km(':'), 4), 1.5, 6, 30) & ~water & ~sea & ~sand & ~plank
    cliff = km('^') & ~sea
    forest = km('Tt')
    flower = km('f')
    fresh = (water | reeds) & ~plank
    land = ~(sea | fresh)
    winter = season == 'winter'

    # grass / snow
    mott = sn(WW, HH, 10, 40) * 0.6 + sn(WW, HH, 4, 41) * 0.4
    if winter:
        paint(land, Pal['snow'] if 'snow' in Pal else SNOW)
    else:
        paint(land, 'grass')
        paint(land & (mott + (BAY - 0.5) * 0.35 * 0.45 < -0.4), 'grass_dk')
        paint(land & (mott + (BAY - 0.5) * 0.35 * 0.45 > 0.45), 'grass_lt')
        paint(land & (R < 0.008), 'grass_dk2')
        fl = sn(WW, HH, 18, 42)
        paint(land & forest, 'floor')
        paint(land & forest & (fl < -0.1), 'floor_dk')
        if season == 'autumn':
            paint(land & (R > 0.985), 'grass_lt')
            paint(land & forest & (R > 0.97), C('#E0A256'))
            paint(land & forest & (R < 0.02), C('#B8483A'))
    # paths
    if winter:
        paint(path, SNOW_SH)
        paint(path & (R < 0.05), C('#F2E3B3'))
    else:
        paint(path, 'path')
        pn = sn(WW, HH, 5, 50)
        paint(path & (pn + (BAY - 0.5) * 0.18 < -0.9), 'path_md')
        paint(path & dil(land & ~path & ~sand, 1), 'path_dk')
    # sand
    paint(sand, 'sand')
    paint(sand & (R < 0.03), 'sand_dk')
    paint(sand & dil(sea, 4) & ~dil(sea, 1), 'sand_wet')
    if winter:
        paint(sand & ~dil(sea, 3), SNOW)
        paint(sand & ~dil(sea, 3) & (R < 0.03), C('#E0A256'))
    # cliffs (coastal stone faces with a grassy / snowy lip)
    d = YY % TS
    paint(cliff, 'stone')
    paint(cliff & (((YY + np.round(2 * np.sin(XX / 5.0)).astype(int)) % 5) == 0), 'stone_dk')
    paint(cliff & (R < 0.05), 'stone_lt')
    above_cliff = np.zeros_like(cliff); above_cliff[3:] = cliff[3:] & ~cliff[:-3]
    paint(above_cliff, SNOW if winter else Pal['grass_hi'])
    massif = ero(cliff, 20)                                  # deep inside large rock areas: calm mountain tops
    if massif.any():
        mn = sn(WW, HH, 12, 70) + 0.3 * sn(WW, HH, 5, 71)
        ridge = massif & (((XX + YY + (mn * 12).astype(int)) % 29) == 0)
        if winter:
            paint(massif, SNOW)
            paint(massif & (mn < -0.4) & (BAY < 0.5), SNOW_SH)
            paint(massif & (mn < -0.65), SNOW_SH)
            paint(ridge, C('#8A8496'))
        else:
            base, dark, light = (('#A8693F', '#6E4A35', '#E0A256') if scenery == 'east'
                                 else ('#8A8496', '#3D3550', '#9CD0C9'))
            paint(massif, C(base))
            paint(massif & (mn < -0.5) & (BAY < 0.5), C(dark))
            paint(massif & (mn > 0.55) & (BAY < 0.4), C(light))
            paint(ridge, C(dark))
    # sea: depth from distance to land, foam, cold water darker with ice floes
    dist = np.full((HH, WW), 99)
    cur = ~sea
    for i in range(1, 18):
        cur = dil(cur, 1)
        dist[(dist == 99) & cur & sea] = i
    paint(sea, 'sea')
    paint(sea & (dist > 12) & (BAY < 0.5), 'sea_dp')
    paint(sea & (dist > 15), 'sea_dp')
    paint(sea & cold, 'sea_dp')
    paint(ocean, C('#2E5466'))                              # the open ocean: deep, with long swells
    swell = ocean & (((YY + (sn(WW, HH, 14, 61) * 6).astype(int)) % 13) == 0) & (R < 0.55)
    paint(swell, 'sea')
    paint(ocean & (R > 0.996), 'sea_lt')
    wave = sea & ((YY + (sn(WW, HH, 8, 60) * 3).astype(int)) % 9 == 0) & (R < 0.4)
    paint(wave, 'sea_lt')
    paint(sea & (dist <= 2) & ((XX // 3 + YY) % 5 != 0), 'foam')
    paint(sea & (dist == 5) & (np.sin(XX / 3.0 + YY) > 0.4), 'foam')
    paint(sea & (R > 0.997), 'spark')
    reef = km('b') & sea                                    # reefs: rocks breaking the surface, foam around them
    rocks = reef & (sn(WW, HH, 3, 300) > 0.12)
    paint(reef & dil(rocks, 1) & ~rocks & ((XX + YY) % 2 == 0), 'foam')
    paint(rocks, 'stone')
    up1 = np.zeros_like(rocks); up1[1:] = rocks[:-1]
    dn1 = np.zeros_like(rocks); dn1[:-1] = rocks[1:]
    paint(rocks & ~up1, 'stone_lt')
    paint(rocks & ~dn1, 'stone_dk')
    shal = warp(rounded(km('l'), 3), 2, 5, 311) & sea       # low-tide shallows (a sandbar appears at dawn)
    paint(shal, 'sea_lt')
    paint(shal & (sn(WW, HH, 4, 310) > 0.35), 'sand_wet')
    paint(shal & (R < 0.03), 'stone')
    fr = np.random.default_rng(77)                          # ice floes in the Rimestream (blocking)
    floes = []
    cold_tiles = [(x, y) for y in range(Ht) for x in range(Wt) if T[y][x] == '!']
    cold_tiles = cold_tiles or [(0, 0)]
    for _ in range(26):
        tx, ty = cold_tiles[int(fr.integers(0, len(cold_tiles)))]
        if all(abs(tx - a) + abs(ty - b) > 3 for (a, b) in floes) and T[ty][tx] == '!' and (tx > 78 or scenery == 'north'):
            floes.append((tx, ty))
    for (tx, ty) in floes:
        cx, cy = tx * TS + 8, ty * TS + 8
        rx, ry = fr.uniform(7, 11), fr.uniform(4, 6)
        m = ((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2 <= 1
        paint(m, SNOW)
        paint(m & (YY > cy + ry * 0.4), SNOW_SH)
        edge = dil(m, 1) & ~m & (YY > cy)
        paint(edge, 'sea_dp')
    # fresh water: river (or ice in winter), reeds
    if winter:
        paint(fresh, C('#4E8C95'))
        paint(fresh & ((((XX - YY) % 29) < 2) | (((XX - YY + 11) % 41) == 0)), SNOW_SH)
        paint(fresh & (sn(WW, HH, 6, 207) > 0.72), SNOW)
        cr = np.random.default_rng(206)
        ice_px = list(zip(*np.where(fresh)))
        for _ in range(60 if ice_px else 0):
            y, x = ice_px[int(cr.integers(0, len(ice_px)))]
            for k in range(int(cr.integers(6, 16))):
                if 0 <= x < WW and 0 <= y < HH and fresh[y, x]:
                    img[y, x] = C('#2E5466')
                x += int(cr.integers(-1, 2)); y += int(cr.choice([-1, 0, 0, 1]))
        paint(reeds & (R < 0.05), C('#6E4A35'))
        paint(fresh & dil(land, 1), C('#2E5466'))
    else:
        paint(fresh, 'river')
        paint(fresh & ~dil(~fresh, 4), 'river_dp')
        paint(fresh & dil(~fresh, 1), 'river_lt')
        above1 = np.zeros_like(land); above1[1:] = land[:-1]
        paint(fresh & above1, 'bank')
        for (yy, xx) in zip(*np.where(water & (R < 0.01))):
            for k in range(4):
                if yy + k < HH and water[yy + k, xx]:
                    img[yy + k, xx] = Pal['river_hi']
        paint(reeds, 'river_lt')
        paint(reeds & (R < 0.16), 'shrub_lt')
        paint(reeds & (R > 0.93), 'shrub_dk')
    # ledges: earth face at the bottom of each ledge tile, grass (or snow) lip
    ledge_tiles = [(x, y) for y in range(Ht) for x in range(Wt) if T[y][x] == 'v']
    for (tx, ty) in ledge_tiles:
        for x in range(tx * TS, tx * TS + TS):
            y0 = ty * TS + 9 + int(round(np.sin(x / 9.0)))
            img[y0 - 1, x] = SNOW if winter else Pal['grass_hi']
            for k in range(7):
                streak = (k + int(round(2.5 * np.sin(x / 7.0)))) % 3 == 0
                c = 'cliff_lt' if k == 0 else ('cliff_dk' if k == 6 or (streak and k > 1) else 'cliff')
                img[y0 + k, x] = Pal[c]
            for k in (7, 8):
                img[y0 + k, x] = (img[y0 + k, x] * 0.72).astype(np.uint8)
    # planks: bridges (planks across the travel direction) and piers
    for y in range(Ht):
        for x in range(Wt):
            if T[y][x] != 'w':
                continue
            horiz = (x > 0 and T[y][x - 1] == 'w') or (x < Wt - 1 and T[y][x + 1] == 'w')
            x0, y0 = x * TS, y * TS
            for yy in range(y0, y0 + TS):
                for xx in range(x0, x0 + TS):
                    k = ((xx - x0) if horiz else (yy - y0)) % 4
                    c = 'wood_lt' if k == 0 else ('wood_dk' if k == 3 else 'wood')
                    img[yy, xx] = SNOW if (winter and k != 3 and R[yy, xx] < 0.8) else Pal[c]
            if horiz:
                for xx in range(x0, x0 + TS):
                    img[y0, xx] = Pal['trunk_dk']; img[y0 + TS - 1, xx] = Pal['trunk_dk']
                    if y0 + TS < HH and sea[y0 + TS, xx]:
                        img[y0 + TS, xx] = (img[y0 + TS, xx] * 0.65).astype(np.uint8)
                        img[y0 + TS + 1, xx] = (img[y0 + TS + 1, xx] * 0.8).astype(np.uint8)
                for (px, py) in ((x0 + 2, y0 + TS - 3), (x0 + 2, y0 + 1)):
                    img[py:py + 3, px:px + 2] = Pal['trunk_dk']
            else:
                for yy in range(y0, y0 + TS):
                    for xx in (x0, x0 + TS - 1):
                        img[yy, xx] = Pal['trunk_dk']
                    for xx in (x0 + 1, x0 + TS - 2):
                        img[yy, xx] = Pal['wood_lt']
    # small decorations
    if not winter:
        dens = 0.016 if season == 'spring' else 0.006
        for (yy, xx) in zip(*np.where(land & ~path & ~sand & ~forest & ~cliff & (R > 1 - 0.004))):
            G_spr(img, xx - 1, yy - 2, ['l.l', 'dld'], {'d': Pal['grass_dk2'], 'l': Pal['grass_hi']})
        fl_m = land & ~path & ~sand & ~forest & ~cliff & ((flower & (R > 1 - dens * 6)) | (R > 1 - dens * 0.3))
        cols = ['flower_a', 'flower_b', 'flower_c'] if season != 'autumn' else ['flower_c', 'grass_lt']
        for (yy, xx) in zip(*np.where(fl_m)):
            img[yy, xx] = Pal[cols[(xx * 7 + yy) % len(cols)]]
            if yy + 1 < HH:
                img[yy + 1, xx] = Pal['grass_dk2']
    else:
        for (yy, xx) in zip(*np.where(land & ~path & ~cliff & (R > 1 - 0.002))):
            G_spr(img, xx - 1, yy - 2, ['d.d', '.d.'], {'d': Pal['pine_dk']})
    # ravine (north of Lauvdal): cliff face, a deep dark chasm with a thread of river, the far rim
    rav = km('R')
    for x in range(WW):
        col = np.where(rav[:, x])[0]
        if len(col) == 0:
            continue
        runs = np.split(col, np.where(np.diff(col) != 1)[0] + 1)
        for run in runs:
            y0, h = run[0], len(run)
            for k in range(h):
                y = y0 + k
                wob = int(round(2 * np.sin(x / 7.0)))
                if k < 2:
                    c = SNOW if winter else Pal['grass_hi']
                elif k < 18 + wob:
                    streak = (k + int(round(3 * np.sin(x / 5.0)))) % 4 == 0
                    c = Pal['cliff_lt'] if k < 4 else (Pal['cliff_dk'] if streak else Pal['cliff'])
                elif k < 22 + wob:
                    c = Pal['cliff_dk']
                elif k < h - 6:
                    c = C('#1E1B2C')
                    if (x * 7 + y * 3) % 13 == 0 and k < h - 14:
                        c = C('#3D3550')
                    if abs(k - (h - 13 + int(round(1.5 * np.sin(x / 9.0))))) < 1:
                        c = C('#2E5466')
                elif k < h - 2:
                    c = Pal['cliff_dk'] if k == h - 3 else C('#1E1B2C')
                else:
                    c = SNOW_SH if winter else Pal['grass_dk']
                img[y, x] = c
    # baked object shadows
    for o in objects:
        if o['kind'] not in stamps:
            continue
        sh, (ax, ay) = stamps[o['kind']]
        ys, xs = np.where(sh < 0.999)
        for y, x in zip(ys, xs):
            gx, gy = o['x'] + x - ax, o['y'] + y - ay
            if 0 <= gx < WW and 0 <= gy < HH:
                img[gy, gx] = (img[gy, gx] * sh[y, x]).astype(np.uint8)
    for c in (MAP.chests if T is MAP.T else []):
        sh, (ax, ay) = stamps['chest']
        ys, xs = np.where(sh < 0.999)
        for y, x in zip(ys, xs):
            gx, gy = c['x'] * TS + 8 + x - ax, c['y'] * TS + 14 + y - ay
            if 0 <= gx < WW and 0 <= gy < HH:
                img[gy, gx] = (img[gy, gx] * sh[y, x]).astype(np.uint8)
    return quantize(img), floes


def G_spr(img, x, y, rows, pal):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.' and 0 <= y + dy < img.shape[0] and 0 <= x + dx < img.shape[1]:
                img[y + dy, x + dx] = pal[ch]


# ------------------------------------------------------------------ hero (layered, 3 directions x 4 frames)
HW, HH_ = 20, 24
HPAL = dict(MI.CPAL)
HPAL.update({'K': 'hair2', 'n': 'hat_dk'})


class Grid:
    def __init__(self):
        self.g = [['.'] * HW for _ in range(HH_)]

    def put(self, x, y, c):
        if 0 <= x < HW and 0 <= y < HH_:
            self.g[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def outline(self, only=None):
        src = [r[:] for r in self.g]
        for y in range(HH_):
            for x in range(HW):
                if src[y][x] != '.':
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < HW and 0 <= yy < HH_ and src[yy][xx] != '.' and (only is None or (xx, yy) in only):
                        self.g[y][x] = 'o'
                        break
        return self

    def rows(self):
        return [''.join(r) for r in self.g]


def legs_front(g, pose):
    if pose in (0, 2):
        g.rect(6, 19, 8, 20, 'p'); g.rect(11, 19, 13, 20, 'p'); g.put(8, 19, 'P'); g.put(13, 19, 'P'); g.put(13, 20, 'P')
        g.rect(6, 21, 8, 22, 'w'); g.rect(11, 21, 13, 22, 'w'); g.put(8, 22, 'W'); g.put(13, 22, 'W')
    else:
        a, b = (6, 11) if pose == 1 else (11, 6)          # forward leg x, back leg x
        g.rect(a, 19, a + 2, 20, 'p'); g.put(a + 2, 19, 'P'); g.put(a + 2, 20, 'P')
        g.rect(b, 19, b + 2, 19, 'p'); g.put(b + 2, 19, 'P')
        g.rect(a - (1 if a == 6 else 0), 21, a + 2 + (1 if a == 11 else 0), 22, 'w'); g.put(a + 2, 22, 'W')
        g.rect(b, 20, b + 2, 21, 'w'); g.put(b + 2, 21, 'W')


def arms_front(g, pose):
    if pose in (0, 2):
        g.rect(3, 13, 4, 16, 'c'); g.put(3, 13, 'l'); g.put(3, 14, 'l'); g.rect(3, 17, 4, 17, 's')
        g.rect(15, 13, 16, 16, 'C'); g.rect(15, 17, 16, 17, 's')
    else:
        lf = pose == 1                                     # left arm forward with right leg... (opposite swing)
        ll, rl = (17, 16) if lf else (16, 17)
        g.rect(3, 13, 4, ll, 'c'); g.put(3, 13, 'l'); g.put(3, 14, 'l'); g.rect(3, ll + 1, 4, ll + 1, 's')
        g.rect(15, 13, 16, rl, 'C'); g.rect(15, rl + 1, 16, rl + 1, 's')


def hat(g, side=False, back=False):
    g.rect(7, 2, 12, 2, 'H'); g.rect(6, 3, 13, 4, 'H')
    g.put(6, 3, 'L'); g.put(6, 4, 'L'); g.put(7, 2, 'L'); g.put(13, 3, 'h'); g.put(13, 4, 'h'); g.put(12, 2, 'h')
    g.rect(6, 5, 13, 5, 'r')
    if side:
        g.rect(3, 6, 18, 6, 'H'); g.rect(3, 6, 7, 6, 'L'); g.put(18, 6, 'h'); g.rect(4, 7, 17, 7, 'h')
    else:
        g.rect(2, 6, 17, 6, 'H'); g.rect(2, 6, 6, 6, 'L'); g.put(17, 6, 'h'); g.rect(3, 7, 16, 7, 'h')


def scarf_tail(g, pose):
    tip = 1 if pose in (1, 3) else 0
    for (x, y, c) in [(4, 12, 'y'), (3, 12, 'y'), (3, 13, 'Y'), (2, 13, 'y'), (1, 14 + tip, 'y'), (2, 14, 'Y'), (1, 15 + tip, 'Y')]:
        g.put(x, y, c)


def hero_body(direction, pose):
    g = Grid()
    if direction == 'down':
        legs_front(g, pose)
        for y in range(13, 19):
            xl, xr = (5, 14) if y < 17 else (4, 15)
            for x in range(xl, xr + 1):
                g.put(x, y, 'l' if x <= xl + 1 else ('C' if x >= xr - 1 else 'c'))
        for y in range(14, 19):
            g.put(10, y, 'C')
        g.put(9, 15, 'b'); g.rect(5, 17, 14, 17, 'g'); g.put(9, 17, 'b')
        arms_front(g, pose)
        g.rect(5, 8, 14, 11, 's')
        for y in range(9, 12):
            g.put(14, y, 'S')
        g.put(5, 11, '.'); g.put(14, 11, '.')
        for x in (5, 6, 9, 10, 13, 14):
            g.put(x, 8, 'k')
        g.put(5, 9, 'k'); g.put(14, 9, 'k')
        for y in (9, 10):
            g.put(7, y, 'e'); g.put(12, y, 'e')
        g.put(6, 11, 'q'); g.put(13, 11, 'q')
        g.rect(5, 12, 14, 12, 'y'); g.put(6, 13, 'y'); g.put(7, 13, 'Y')
        scarf_tail(g, pose)
        hat(g)
    elif direction == 'up':
        legs_front(g, pose)
        for y in range(13, 19):
            xl, xr = (5, 14) if y < 17 else (4, 15)
            for x in range(xl, xr + 1):
                g.put(x, y, 'l' if x <= xl + 1 else ('C' if x >= xr - 1 else 'c'))
        for y in range(16, 19):
            g.put(9, y, 'C')                               # back vent
        g.rect(5, 17, 14, 17, 'g')
        arms_front(g, pose)
        g.rect(5, 8, 14, 11, 'k')                          # back of the head: hair
        g.put(5, 11, '.'); g.put(14, 11, '.')
        for x in (7, 10, 12):
            g.put(x, 9, 'K')
        g.rect(5, 12, 14, 12, 'y'); g.rect(6, 13, 13, 13, 'Y')
        scarf_tail(g, pose)
        hat(g, back=True)
    else:                                                  # right-facing profile
        if pose in (0, 2):
            g.rect(8, 19, 11, 20, 'p'); g.put(11, 19, 'P'); g.put(11, 20, 'P')
            g.rect(8, 21, 12, 22, 'w'); g.put(12, 22, 'W')
        else:
            near_fwd = pose == 1
            fx, bx = (11, 6) if near_fwd else (6, 11)
            g.rect(bx, 19, bx + 2, 20, 'P')                # far leg (darker)
            g.rect(bx - (1 if bx == 6 else 0), 21, bx + 3, 22, 'W')
            g.rect(fx, 19, fx + 2, 20, 'p')                # near leg
            g.rect(fx - (1 if fx == 6 else 0), 21, fx + 3, 22, 'w'); g.put(fx + 3, 22, 'W')
        for y in range(13, 19):
            xl, xr = (7, 13) if y < 17 else (6, 14)
            for x in range(xl, xr + 1):
                g.put(x, y, 'l' if x == xl else ('C' if x == xr else 'c'))
        g.put(12, 15, 'b'); g.rect(6, 17, 14, 17, 'g'); g.put(12, 17, 'b')
        if pose in (0, 2):                                 # near arm swinging
            g.rect(9, 13, 10, 16, 'c'); g.put(9, 13, 'l'); g.rect(9, 17, 10, 17, 's')
        elif pose == 1:
            g.rect(10, 13, 11, 15, 'c'); g.rect(12, 15, 12, 16, 'c'); g.rect(12, 17, 13, 17, 's')
        else:
            g.rect(8, 13, 9, 15, 'c'); g.rect(7, 15, 7, 16, 'c'); g.rect(6, 17, 7, 17, 's')
        g.rect(8, 8, 14, 11, 's')                          # face
        g.rect(5, 8, 8, 11, 'k'); g.put(5, 11, '.')
        g.put(9, 9, 'S'); g.put(15, 10, 's')               # ear shadow, nose
        for y in (9, 10):
            g.put(12, y, 'e')
        g.put(13, 11, 'q')
        g.rect(6, 12, 13, 12, 'y'); g.put(13, 13, 'Y')
        for (x, y, c) in [(5, 12, 'y'), (4, 12, 'y'), (3, 13, 'Y'), (2, 13, 'y'), (1, 14 + (1 if pose % 2 else 0), 'y'), (2, 14, 'Y')]:
            g.put(x, y, c)
        hat(g, side=True)
    return g.outline().rows()


def hero_layer(kind, direction, pose):
    """equipment layers; drawn only when worn"""
    g = Grid()
    if kind == 'pouch':
        if direction == 'down':
            for k in range(6):
                g.put(6 + k, 13 + k * 4 // 5, 't')
            g.rect(12, 16, 15, 18, 'g'); g.rect(12, 16, 15, 16, 'G'); g.put(13, 17, 'b')
            bag = {(x, y) for x in range(12, 16) for y in range(16, 19)}
        elif direction == 'up':
            for k in range(6):
                g.put(13 - k, 13 + k * 4 // 5, 't')
            g.rect(4, 16, 7, 18, 'g'); g.rect(4, 16, 7, 16, 'G')
            bag = {(x, y) for x in range(4, 8) for y in range(16, 19)}
        else:
            for k in range(4):
                g.put(9 + k, 13 + k, 't')
            g.rect(10, 16, 13, 18, 'g'); g.rect(10, 16, 13, 16, 'G'); g.put(11, 17, 'b')
            bag = {(x, y) for x in range(10, 14) for y in range(16, 19)}
        g.outline(only=bag)
    else:   # walking stick (slung on the back)
        if direction == 'down':
            pts = [(13 + round(k * 4 / 7), 15 - k) for k in range(8)]
            cap = [(17, 7), (18, 7), (17, 8), (18, 8)]
        elif direction == 'up':
            pts = [(6 + round(k * 7 / 10), 16 - k) for k in range(11)]
            cap = [(13, 5), (14, 5), (13, 6), (14, 6)]
        else:
            pts = [(8 - round(k * 4 / 9), 16 - k) for k in range(10)]
            cap = [(3, 6), (4, 6), (3, 7), (4, 7)]
        for (x, y) in pts:
            g.put(x, y, 'm'); g.put(x + 1, y, 'M')
        for (x, y) in cap:
            g.put(x, y, 'x')
        g.outline()
    return g.rows()


STICK_PAL = {'m': 'wood_lt', 'M': 'wood_dk', 'x': 'trunk_dk'}


def grid_to_rgba(rows, pal_keys):
    a = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    set_palette('summer')
    P = G['P']
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.':
                continue
            key = pal_keys.get(ch, HPAL.get(ch))
            a[y, x, :3] = P[key]
            a[y, x, 3] = 255
    # soft outline: 'o' pixels take a darker shade of their filled neighbours
    out = a.copy()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != 'o':
                continue
            acc = [a[yy, xx, :3].astype(float) for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)
                   if 0 <= yy < len(rows) and 0 <= xx < len(row) and rows[yy][xx] not in '.o']
            if acc:
                ext = lambda yy, xx: not (0 <= yy < len(rows) and 0 <= xx < len(row)) or rows[yy][xx] == '.'
                lit = (ext(y - 1, x) or ext(y, x - 1)) and not (ext(y + 1, x) or ext(y, x + 1))
                out[y, x, :3] = np.clip(np.mean(acc, axis=0) * (0.84 if lit else 0.6), 0, 255)
    out[..., :3] = quantize(out[..., :3])
    return out


def build_hero():
    dirs = ['down', 'up', 'right']
    for layer in ('body', 'pouch', 'stick'):
        sheet = np.zeros((HH_ * 3, HW * 4, 4), np.uint8)
        for r, d in enumerate(dirs):
            for f in range(4):
                rows = hero_body(d, f) if layer == 'body' else hero_layer(layer, d, f)
                tile = grid_to_rgba(rows, STICK_PAL if layer == 'stick' else {})
                sheet[r * HH_:(r + 1) * HH_, f * HW:(f + 1) * HW] = tile
        save_rgba(sheet, os.path.join(ART, 'hero', f'hero_{layer}.png'))


# ------------------------------------------------------------------ surfing (otter / seal), 3 directions x 4 frames
def rider_rows(direction):
    rows = hero_body('down' if direction == 'down' else 'up', 0)
    return rows[:18]


def surf_frame(kind, direction, f):
    c = MI.Cell()
    MI.water(c, f)
    c.img[:] = MI.PAL['sea']                                   # plain water: the game draws the sea itself
    if direction == 'right':
        wl = MI._surf(c, f, kind)
    else:
        b, ph = MI.BOB[f], f // 2
        wl = 36 + b
        lt, md, dk = ('otter_lt', 'otter', 'otter_dk') if kind == 'otter' else ('seal_lt', 'seal', 'seal_dk')
        for i, t in enumerate(np.linspace(0, 2 * np.pi, 60)):
            if (i + f * 2) % 6 < 4:
                x, y = int(round(36 + (16 + f % 2) * np.cos(t))), int(round(wl + 1 + 3 * np.sin(t)))
                if y >= wl:
                    c.set(x, y, 'foam', obj=False)
        wake_dir = -1 if direction == 'down' else 1
        for k in range(10):
            for sgn in (-1, 1):
                if (k + f) % 3:
                    c.set(36 + sgn * (2 + k // 3), wl + wake_dir * (4 + k) if direction == 'up' else wl - 7 - k, 'foam', obj=False)
        for side_x, down in ((25, ph == 0), (47, ph == 1)):
            MI.shape(c, MI.ell(side_x, 39 + b + (1 if down else 0), 3, 2), lambda x, y: dk)
        if direction == 'up':
            if kind == 'otter':
                MI.shape(c, MI.limb(36, 38 + b, 36, 45 + b, 3.0, 2.0), lambda x, y: md)
        body = MI.ell(36, 34 + b, 13, 6)
        back = MI.lit3(36, 34 + b, 13, 6, lt, md, dk)
        MI.shape(c, body, back)
        rows = rider_rows(direction)
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch != '.':
                    c.set(26 + dx, 32 + b - len(rows) + 1 + dy, MI.CPAL.get(ch, HPAL.get(ch)))
        for (x, y) in body:
            if y >= 32 + b and all((x + a, y + bb) in body for a, bb in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c.set(x, y, back(x, y))
        if direction == 'down':                                # head peeking out in front
            MI.shape(c, MI.ell(36, 37 + b, 5.5, 3.5), MI.lit3(36, 37 + b, 5.5, 3.5, lt, md, dk))
            if kind == 'otter':
                for ex in (31, 41):
                    MI.shape(c, MI.ell(ex, 34 + b, 1.4, 1.4), lambda x, y: dk)
            for (x, y) in MI.ell(36, 38.5 + b, 2.6, 1.4):
                c.set(x, y, 'muzzle' if kind == 'otter' else lt)
            c.set(33, 36 + b, 'eye'); c.set(39, 36 + b, 'eye'); c.set(33, 35 + b, 'snow_lt')
            c.set(36, 38 + b, 'eye')
        elif kind == 'otter':
            for ex in (31, 41):
                MI.shape(c, MI.ell(ex, 28 + b, 1.4, 1.4), lambda x, y: dk)
    MI.finish(c, wl, keep=0.38)
    rgb = MI.quantize(c.img)
    a = np.zeros((MI.CH, MI.CW, 4), np.uint8)
    a[..., :3] = rgb
    sea_px = np.all(rgb == MI.quantize(np.array([[MI.PAL['sea']]], np.uint8))[0, 0], axis=-1)
    a[..., 3] = np.where(sea_px, 0, 255)
    return a


def build_mounts():
    for kind in ('otter', 'seal'):
        sheet = np.zeros((MI.CH * 3, MI.CW * 4, 4), np.uint8)
        for r, d in enumerate(['down', 'up', 'right']):
            for f in range(4):
                sheet[r * MI.CH:(r + 1) * MI.CH, f * MI.CW:(f + 1) * MI.CW] = surf_frame(kind, d, f)
        save_rgba(sheet, os.path.join(ART, 'mounts', f'surf_{kind}.png'))


# ------------------------------------------------------------------ HUD: pixel font, banners, badges, messages
FONT = {
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'], 'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
    'C': ['.####', '#....', '#....', '#....', '#....', '#....', '.####'], 'D': ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
    'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####'], 'F': ['#####', '#....', '#....', '####.', '#....', '#....', '#....'],
    'G': ['.####', '#....', '#....', '#.###', '#...#', '#...#', '.###.'], 'H': ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'I': ['.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'], 'J': ['..###', '...#.', '...#.', '...#.', '...#.', '#..#.', '.##..'],
    'K': ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'], 'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
    'M': ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'], 'N': ['#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#', '#...#'],
    'O': ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'], 'P': ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'],
    'Q': ['.###.', '#...#', '#...#', '#...#', '#.#.#', '#..#.', '.##.#'], 'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'], 'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'], 'V': ['#...#', '#...#', '#...#', '#...#', '.#.#.', '.#.#.', '..#..'],
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'], 'X': ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'],
    'Y': ['#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'], 'Z': ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'], '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'], '3': ['####.', '....#', '....#', '.###.', '....#', '....#', '####.'],
    '4': ['#...#', '#...#', '#...#', '#####', '....#', '....#', '....#'], '5': ['#####', '#....', '#....', '####.', '....#', '....#', '####.'],
    '6': ['.###.', '#....', '#....', '####.', '#...#', '#...#', '.###.'], '7': ['#####', '....#', '...#.', '..#..', '..#..', '..#..', '..#..'],
    '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'], '9': ['.###.', '#...#', '#...#', '.####', '....#', '....#', '.###.'],
    ' ': ['...', '...', '...', '...', '...', '...', '...'], '.': ['.', '.', '.', '.', '.', '.', '#'],
    ',': ['..', '..', '..', '..', '..', '.#', '#.'], '!': ['#', '#', '#', '#', '#', '.', '#'],
    '?': ['.###.', '#...#', '....#', '...#.', '..#..', '.....', '..#..'], "'": ['#', '#', '.', '.', '.', '.', '.'],
    ':': ['.', '#', '.', '.', '.', '#', '.'], '/': ['....#', '...#.', '...#.', '..#..', '.#...', '.#...', '#....'],
    '-': ['....', '....', '....', '####', '....', '....', '....'], '+': ['.....', '..#..', '..#..', '#####', '..#..', '..#..', '.....'],
}
INK = C('#1E1B2C')
CREAM = C('#F2E3B3')
GOLD = C('#E0A256')
PANEL = C('#3D3550')
PANEL_IN = C('#6E4A35')


def text_w(s):
    return sum(len(FONT[ch][0]) + 1 for ch in s) - 1


def draw_text(a, x, y, s, col, shadow=INK):
    for ch in s:
        gl = FONT[ch]
        for dy, row in enumerate(gl):
            for dx, c in enumerate(row):
                if c == '#':
                    if shadow is not None and y + dy + 1 < a.shape[0]:
                        a[y + dy + 1, x + dx, :3] = shadow; a[y + dy + 1, x + dx, 3] = 255
                    a[y + dy, x + dx, :3] = col; a[y + dy, x + dx, 3] = 255
        x += len(gl[0]) + 1


def panel(w, h):
    a = np.zeros((h, w, 4), np.uint8)
    a[:, :, :3] = INK; a[:, :, 3] = 255
    a[1:-1, 1:-1, :3] = PANEL_IN
    a[2:-2, 2:-2, :3] = INK
    return a


def build_hud():
    out = os.path.join(ART, 'hud')
    banners = {'keelvik': ('KEELVIK', 'BOATWRIGHT VILLAGE'), 'lauvdal': ('LAUVDAL', 'ROUTE 16'),
               'sulenes': ('SULE NESS', 'ROUTE 17'), 'vidsea': ('THE VIDSEA', 'OPEN WATER'),
               'rimestream': ('RIMESTREAM', 'COLD WATER')}
    for key, (name, sub) in banners.items():
        w = max(text_w(name) + 16, text_w(sub) + 12)
        a = np.zeros((28, w, 4), np.uint8)
        a[0:16, 0:text_w(name) + 16] = panel(text_w(name) + 16, 16)
        draw_text(a, 7, 4, name, CREAM)
        a[12, 7:7 + text_w(name), :3] = GOLD
        a[16:26, 0:text_w(sub) + 10, :3] = INK; a[16:26, 0:text_w(sub) + 10, 3] = 255
        draw_text(a, 5, 17, sub, C('#C6A878') if False else C('#E0A256'), None)
        save_rgba(a, os.path.join(out, f'banner_{key}.png'))
    icons = {
        'spring': ['..p..', '.pyp.', '..p..', '..g..', 'g.g.g', '.ggg.', '..g..'],
        'summer': ['..y..', 'y.y.y', '.yyy.', 'yyyyy', '.yyy.', 'y.y.y', '..y..'],
        'autumn': ['...o.', '..ooo', '.ooro', 'oooo.', '.oo..', '.r...', 'r....'],
        'winter': ['y.y.y', '.y.y.', 'yyyyy', '.y.y.', 'y.y.y', '.....', '.....'],
    }
    icol = {'spring': {'p': C('#E48A73'), 'y': GOLD, 'g': C('#8DB054')}, 'summer': {'y': GOLD},
            'autumn': {'o': C('#E0A256'), 'r': C('#B8483A')}, 'winter': {'y': C('#9CD0C9')}}
    for s in SEASONS:
        label = s.upper()
        w = text_w(label) + 22
        a = panel(w, 16)
        for dy, row in enumerate(icons[s]):
            for dx, ch in enumerate(row):
                if ch != '.':
                    a[4 + dy, 6 + dx, :3] = icol[s][ch]
        draw_text(a, 15, 4, label, CREAM)
        save_rgba(a, os.path.join(out, f'season_{s}.png'))
    messages = {
        'intro': ['YOU CARRY THE OTTER STICK.', 'FACE THE WATER AND PRESS SPACE.'],
        'otter_cold': ['THE OTTER SHIVERS AND TURNS BACK.', 'THIS WATER IS TOO COLD.'],
        'seal_on': ['THE SEAL TAKES OVER', 'IN THE COLD WATER.'],
        'frozen': ['THE WATER IS FROZEN.', 'YOU CAN WALK ON THE ICE.'],
        'got_seal_flute': ['FOUND THE SEAL FLUTE!', 'A SEAL WILL CARRY YOU IN COLD WATER.'],
        'got_coin': ['FOUND AN OLD SILVER COIN!', 'ONLY REACHABLE OVER THE ICE.'],
        'got_float': ['FOUND A GLASS FISHING FLOAT!', ''],
        'got_stick': ['FOUND A WALKING STICK!', 'PRESS R TO WEAR IT OR PUT IT AWAY.'],
        'empty': ['THE CHEST IS EMPTY.', ''],
        'sign_keelvik': ['KEELVIK', 'BOATS HAVE BEEN BUILT HERE FOR AGES.'],
        'sign_lauvdal': ['LAUVDAL', 'WEST: GREINHOLT.  EAST: KEELVIK.'],
        'sign_sulenes': ['SULE NESS LIGHTHOUSE', 'MIND THE LEDGES ON THE WAY DOWN.'],
    }
    for key, lines in messages.items():
        a = panel(300, 30)
        draw_text(a, 8, 6, lines[0], CREAM)
        if lines[1]:
            draw_text(a, 8, 17, lines[1], C('#E0A256'))
        save_rgba(a, os.path.join(out, f'msg_{key}.png'))
    help_lines = ['CONTROLS', 'ARROWS / WASD   MOVE', 'SHIFT           RUN', 'SPACE           SURF / READ / OPEN',
                  'TAB             NEXT SEASON', '1 2 3 4         PICK A SEASON',
                  'T               NEXT TIME OF DAY', 'E               POUCH ON / OFF',
                  'R               WALKING STICK ON / OFF', 'H               HIDE THIS HELP']
    a = panel(max(text_w(l) for l in help_lines) + 16, 12 + 10 * len(help_lines))
    for i, line in enumerate(help_lines):
        draw_text(a, 8, 6 + i * 10, line, GOLD if i == 0 else CREAM)
    save_rgba(a, os.path.join(out, 'help.png'))
    a = np.zeros((10, text_w('H: HELP') + 2, 4), np.uint8)
    draw_text(a, 0, 1, 'H: HELP', CREAM)
    save_rgba(a, os.path.join(out, 'hint.png'))
    # item icons (16x16)
    def icon(rows, pal):
        a = np.zeros((16, 16, 4), np.uint8)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != '.':
                    a[y, x, :3] = C(pal[ch]); a[y, x, 3] = 255
        return a
    MI_icons = {'otter_stick': MI._icon('otter_stick'), 'seal_flute': MI._icon('seal_flute')}
    for k, im in MI_icons.items():
        im.save(os.path.join(out, f'icon_{k}.png'))
    staff = ['..........kk....', '.........kWWk...', '.........kWdk...', '........kWdk....', '........kWk.....',
             '.......kWdk.....', '.......kWk......', '......kWdk......', '......kWk.......', '.....kWdk.......',
             '.....kWk........', '....kWdk........', '....kWk.........', '...kWdk.........', '...kkk..........', '................']
    save_rgba(icon(staff, {'k': '#1E1B2C', 'W': '#A8693F', 'd': '#6E4A35'}), os.path.join(out, 'icon_walking_stick.png'))
    coin = ['................', '................', '.....kkkkk......', '....kccccck.....', '...kcCCCCcck....', '...kcCkkCcck....',
            '...kcCkkCcck....', '...kcCCCCcck....', '....kcccccdk....', '.....kkkkkk.....', '................', '................',
            '................', '................', '................', '................']
    save_rgba(icon(coin, {'k': '#1E1B2C', 'c': '#9CD0C9', 'C': '#F2E3B3', 'd': '#4E8C95'}), os.path.join(out, 'icon_coin.png'))
    flt = ['................', '.......kk.......', '......kddk......', '....kkkkkkkk....', '...kgGGgggggk...', '..kgGGgggggggk..',
           '..kgGgggggggdk..', '..kgggggggggdk..', '..kggggggggddk..', '...kgggggddk....', '....kkkkkkk.....', '................',
           '................', '................', '................', '................']
    save_rgba(icon(flt, {'k': '#1E1B2C', 'g': '#4E8C95', 'G': '#9CD0C9', 'd': '#2E5466'}), os.path.join(out, 'icon_float.png'))


# ------------------------------------------------------------------ day / night
# Schedule (24 h): night 22-04 (6 h), dawn 04-07 (3 h), day 07-19 (12 h), dusk 19-22 (3 h).
# The LUT is 16 columns (one per palette colour) x (1 + 96) rows: row 0 is the reference palette,
# rows 1..96 give the colour every 15 minutes from 00:00. The game blends between neighbouring rows.
KEYS_H = [(4.0, 'night'), (5.5, 'dawn'), (7.0, 'day'), (19.0, 'day'), (20.5, 'dusk'), (22.0, 'night'), (28.0, 'night')]


def from_lab(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200

    def finv(t):
        return np.where(t ** 3 > 0.008856, t ** 3, (t - 16 / 116) / 7.787)
    xyz = np.stack([finv(fx) * 0.95047, finv(fy), finv(fz) * 1.08883], -1)
    M = np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192], [0.1805, 0.0722, 0.9505]])
    lin = np.clip(xyz @ np.linalg.inv(M), 0, 1)
    srgb = np.where(lin > 0.0031308, 1.055 * lin ** (1 / 2.4) - 0.055, 12.92 * lin)
    return np.clip(np.round(srgb * 255), 0, 255)


def key_palette(name, lab):
    L, a, b = lab[:, 0], lab[:, 1], lab[:, 2]
    if name == 'day':
        out = lab.copy()
    elif name == 'night':          # moonlit: darker, desaturated, shifted to blue
        out = np.stack([L * 0.5 + 4, a * 0.35 + 1, b * 0.25 - 16], -1)
    elif name == 'dusk':           # golden-rose evening light, purple shadows
        out = np.stack([L * 0.8 + 1, a * 0.8 + 14, b * 0.75 + 7 - np.where(L < 45, 16, 0)], -1)
    else:                          # dawn: cool rose and lavender
        out = np.stack([L * 0.72 + 3, a * 0.75 + 9, b * 0.55 - 7], -1)
    return out


def build_daynight_lut():
    pal = QP.copy()
    lab = to_lab(pal)
    keys = {n: key_palette(n, lab) for n in ('day', 'night', 'dusk', 'dawn')}
    rows = [pal]
    for r in range(96):
        h = r / 4.0
        hh = h + 24 if h < 4.0 else h
        for (h0, k0), (h1, k1) in zip(KEYS_H, KEYS_H[1:]):
            if h0 <= hh <= h1:
                t = (hh - h0) / (h1 - h0)
                t = t * t * (3 - 2 * t)
                rows.append(from_lab(keys[k0] * (1 - t) + keys[k1] * t))
                break
    lut = np.stack(rows).astype(np.uint8)
    rgba = np.concatenate([lut, np.full(lut.shape[:2] + (1,), 255, np.uint8)], -1)
    save_rgba(rgba, os.path.join(ART, 'daynight_lut.png'))
    prev = np.repeat(np.repeat(lut, 6, 1), 2, 0)                          # human-readable preview strip
    Image.fromarray(prev).save(os.path.join(os.path.dirname(GAME), 'docs', 'prototype', 'daynight_lut_preview.png'))
    return lut


EMISSIVE = {'house_a': ('glass', 'glass_lt', 'glow'), 'house_b': ('glass', 'glass_lt', 'glow'),
            'lamp': ('glow', 'cream'), 'lighthouse': ('glow', 'glass')}
LIT = {'glass': (255, 201, 74), 'glass_lt': (255, 233, 160), 'glow': (255, 244, 200), 'cream': (255, 244, 200),
       'frz_hi': (190, 250, 255), 'frz': (120, 220, 240)}
MEDIUM_LIGHTS = ('lamp', 'beacon', 'stall_a', 'stall_b', 'fireplace', 'stove')


def build_lights(manifest, kinds=None, emissive=None):
    """lit windows / lamps (colours outside the 16-colour palette, so the day/night LUT leaves them alone)"""
    kinds = kinds or KINDS
    for kind, keys in (emissive or EMISSIVE).items():
        fn, size, anchor, opt = kinds[kind]
        rgba, _, anc = render_sprite(fn, 'summer', size, anchor, opt.get('leaf', LEAF), dict(opt.get('extra', {})),
                                     opt.get('sea', False), None)
        img, Pc = G['img'], G['P']
        ys, xs = np.where(rgba[..., 3] > 0)
        y0, x0 = ys.min(), xs.min()
        lit = np.zeros_like(rgba)
        mask = np.zeros(rgba.shape[:2], bool)
        for k in keys:
            m = np.all(img == Pc[k], axis=-1) & (rgba[..., 3] > 0)
            lit[m, :3] = LIT[k]
            lit[m, 3] = 255
            mask |= m
        h, w = manifest[kind]['h'], manifest[kind]['w']
        save_rgba(lit[y0:y0 + h, x0:x0 + w], os.path.join(ART, 'objects', f'{kind}_lit.png'))
        seen = np.zeros_like(mask)                                        # light sources = connected clusters
        lights = []
        for (y, x) in zip(*np.where(mask)):
            if seen[y, x]:
                continue
            stack, pts = [(y, x)], []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                pts.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            py, px = np.mean(pts, axis=0)
            lights.append([float(px - anc[0]), float(py - anc[1]), len(pts)])
        merged = []                                                       # one light per window / lamp
        for (x, y, n) in lights:
            for m in merged:
                if abs(m[0] - x) <= 8 and abs(m[1] - y) <= 8:
                    m[0], m[1], m[2] = (m[0] * m[2] + x * n) / (m[2] + n), (m[1] * m[2] + y * n) / (m[2] + n), m[2] + n
                    break
            else:
                merged.append([x, y, n])
        top = min(m[1] for m in merged)
        manifest[kind]['lights'] = [[round(x, 1), round(y, 1), 'l' if (kind == 'lighthouse' and y == top) else
                                     ('m' if kind in MEDIUM_LIGHTS else 's')] for (x, y, n) in merged]


def build_halos():
    """dithered warm glow, drawn additively around lights at night"""
    bay = G['BAYER']
    for name, r in (('s', 10), ('m', 18), ('l', 34)):
        n = 2 * r
        a = np.zeros((n, n, 4), np.uint8)
        for y in range(n):
            for x in range(n):
                d = ((x - r + 0.5) ** 2 + (y - r + 0.5) ** 2) ** 0.5 / r
                if d >= 1:
                    continue
                inten = (1 - d) ** 1.6
                level = 0.42 if inten > 0.55 else (0.26 if inten > 0.25 else 0.13)
                if inten + (bay[y % 4, x % 4] - 0.5) * 0.12 < 0.05:
                    continue
                a[y, x] = (255, 176, 80, int(255 * level))
        save_rgba(a, os.path.join(ART, 'objects', f'halo_{name}.png'))


def build_clock_hud():
    out = os.path.join(ART, 'hud')
    glyphs = '0123456789:'
    a = np.zeros((9, 6 * len(glyphs), 4), np.uint8)
    for i, ch in enumerate(glyphs):
        draw_text(a, i * 6, 0, ch, CREAM)
    save_rgba(a, os.path.join(out, 'clock_digits.png'))
    save_rgba(panel(42, 16), os.path.join(out, 'clock_panel.png'))
    icons = {'night': (['..ss.', '.ss..', 'ss...', 'ss...', 'ss...', '.ss..', '..ss.'], C('#9CD0C9')),
             'dawn': (['.....', '.....', '..p..', '.ppp.', 'ppppp', '.....', 'ppppp'], C('#E48A73')),
             'day': (['..y..', 'y.y.y', '.yyy.', 'yyyyy', '.yyy.', 'y.y.y', '..y..'], GOLD),
             'dusk': (['.....', '.....', '..o..', '.ooo.', 'ooooo', '.....', 'ooooo'], C('#E0A256'))}
    for k, (rows, col) in icons.items():
        a = np.zeros((7, 5, 4), np.uint8)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != '.':
                    a[y, x, :3] = col
                    a[y, x, 3] = 255
        save_rgba(a, os.path.join(out, f'time_{k}.png'))


# ------------------------------------------------------------------ main
def main():
    sys.modules.setdefault('proto_build', sys.modules[__name__])
    import proto_art2 as A2
    import proto_art3 as A3
    A2.register()
    A3.register()
    manifest, stamps = build_objects()
    print('objects:', len(manifest), 'kinds x', len(SEASONS), 'seasons')
    floes = []
    for s in SEASONS:
        ground, floes = build_ground(s, stamps)
        save_rgba(ground, os.path.join(ART, 'ground', f'ground_{s}.png'))
        print('ground', s)
    build_hero()
    build_mounts()
    build_hud()
    build_daynight_lut()
    build_lights(manifest)
    build_halos()
    build_clock_hud()
    A2.build_all(manifest)
    manifest['_lowtide'] = A2.build_lowtide()
    A3.build_all(manifest, stamps)
    data = json.load(open(MAP.OUT))
    data['blocked'] = sorted(set(map(tuple, data['blocked'])) | set(floes))
    data['blocked'] = [list(b) for b in data['blocked']]
    with open(MAP.OUT, 'w') as f:
        json.dump(data, f)
    with open(os.path.join(GAME, 'data', 'sprites.json'), 'w') as f:
        json.dump(manifest, f, indent=1)
    print('done')


if __name__ == '__main__':
    main()
