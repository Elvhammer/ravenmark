"""Animated 'surf companion' ideas: small creatures the hero rides on water.

Three-quarter view heading right, 4-frame loop (bob, paddle, ripples), retro 16-colour palette.
    python3 mount_ideas.py OUT_DIR   -> surf_ideas.gif + surf_otter_seal.gif
"""
import runpy
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import make_style_sheets as M

G = runpy.run_path(M.MOCK, init_globals={'OPTS': {**M.BASE, 'scene': 'sea', 'art': 2}}, run_name='ideas')
hx, to_lab = G['hx'], G['to_lab']
CART, CPAL = G['CARTOGRAPHER'], G['CPAL']
PAL = dict(G['P'])
PAL.update({k: hx(v) for k, v in {
    'otter': '#8A5A3B', 'otter_lt': '#B07E50', 'otter_dk': '#5E3E2A', 'muzzle': '#E8D2A8',
    'seal': '#8A8496', 'seal_lt': '#B8B4C4', 'seal_dk': '#5E5870',
    'duck': '#F2E3B3', 'duck_sh': '#C9B98A', 'duck_dk': '#9A8A68', 'bill': '#E0A256', 'bill_dk': '#B07E2E',
}.items()})
QP = np.array([hx(c) for c in M.RETRO16], float)
QL = to_lab(QP)

CW, CH, SC = 72, 48, 5
BOB = [0, -1, 0, 1]


class Cell:
    def __init__(self):
        self.img = np.zeros((CH, CW, 3), np.uint8)
        self.obj = np.zeros((CH, CW), bool)
        self.outl = np.zeros((CH, CW), bool)

    def set(self, x, y, key, obj=True):
        if 0 <= x < CW and 0 <= y < CH:
            self.img[y, x] = PAL[key] if isinstance(key, str) else key
            if obj:
                self.obj[y, x] = True
                self.outl[y, x] = key == 'ink'


def ell(cx, cy, rx, ry):
    return {(x, y) for y in range(int(cy - ry) - 1, int(cy + ry) + 2) for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1}


def limb(x0, y0, x1, y1, w0, w1):
    pix = set()
    n = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
    for i in range(n + 1):
        t = i / n
        x, y, r = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, w0 + (w1 - w0) * t
        pix |= {(xx, yy) for yy in range(int(y - r) - 1, int(y + r) + 2) for xx in range(int(x - r) - 1, int(x + r) + 2)
                if (xx - x) ** 2 + (yy - y) ** 2 <= r * r}
    return pix


def shape(c, pix, colour):
    for (x, y) in pix:
        c.set(x, y, colour(x, y))
    for (x, y) in pix:
        if any((x + dx, y + dy) not in pix for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            c.set(x, y, 'ink')


def lit3(cx, cy, rx, ry, lt, md, dk):
    def f(x, y):
        v = -(0.6 * (x - cx) / rx + 0.8 * (y - cy) / ry)
        return lt if v > 0.35 else (md if v > -0.35 else dk)
    return f


def _side_rows():
    """hero's upper body turned 3/4 toward the right (direction of travel): hair at the back, eyes shifted right"""
    g = [list(r) for r in CART[:14]]
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


SIDE = _side_rows()


def rider(c, x0, bottom):
    for dy, row in enumerate(SIDE):
        for dx, ch in enumerate(row):
            if ch != '.':
                c.set(x0 + dx, bottom - 13 + dy, CPAL[ch])


def water(c, f):
    c.img[:] = PAL['sea']
    rng = np.random.default_rng(7)
    for _ in range(26):
        x, y = int(rng.integers(0, CW)), int(rng.integers(0, CH))
        for k in range(3):
            c.set((x + k + f) % CW, y, 'sea_lt', obj=False)


def ripples(c, cx, wl, f, rx=15):
    for k in range(18):                                                   # short wake trailing behind (left)
        for sgn in (-1, 1):
            if (k + f) % 3:
                c.set(cx - rx - 2 - k, int(round(wl + 1 + sgn * (1 + k * 0.3))), 'foam', obj=False)
    for i, t in enumerate(np.linspace(0, 2 * np.pi, 72)):
        if (i + f * 2) % 6 < 4:
            x, y = int(round(cx + (rx + f % 2) * np.cos(t))), int(round(wl + 1 + 3 * np.sin(t)))
            if y >= wl:
                c.set(x, y, 'foam', obj=False)


def finish(c, wl, keep=0.55):
    """soft coloured outlines (as in the game), then tint everything below the waterline"""
    src = c.img.copy()
    inner = c.obj & ~c.outl
    for y, x in zip(*np.where(c.outl)):
        acc = [src[yy, xx] for yy in (y - 1, y, y + 1) for xx in (x - 1, x, x + 1)
               if 0 <= yy < CH and 0 <= xx < CW and inner[yy, xx]]
        base = np.mean(acc, axis=0) if acc else src[y, x].astype(float) + 50
        out = lambda yy, xx: not (0 <= yy < CH and 0 <= xx < CW) or not c.obj[yy, xx]
        lit = (out(y - 1, x) or out(y, x - 1)) and not (out(y + 1, x) or out(y, x + 1))
        c.img[y, x] = np.clip(base * (0.84 if lit else 0.6), 0, 255).astype(np.uint8)
    under = c.obj.copy()
    under[:wl + 1] = False
    c.img[under] = (c.img[under] * keep + PAL['sea'] * (1 - keep)).astype(np.uint8)
    for x in range(CW):
        if c.obj[wl, x] and x % 3 != 1:
            c.set(x, wl + 1, 'foam', obj=False)


def eye(c, x, y, tall=2):
    for dy in range(tall):
        c.set(x, y + dy, 'eye'); c.set(x + 1, y + dy, 'eye')
    c.set(x, y, 'snow_lt')


def otter(c, f):
    b, ph = BOB[f], f // 2
    wl = 35 + b
    ripples(c, 34, wl, f, 24)
    shape(c, limb(18, 31 + b, 6, 28 + b, 3.0, 2.0), lambda x, y: 'otter')                         # long flat tail
    shape(c, ell(30, 30 + b, 15, 8), lit3(30, 30 + b, 15, 8, 'otter_lt', 'otter', 'otter_dk'))
    shape(c, ell(22, 36 + b + (1 if ph else -1), 2.6, 2.0), lambda x, y: 'otter_dk')             # back paw
    rider(c, 16, 27 + b)
    shape(c, ell(45, 23 + b, 2.2, 2.2), lambda x, y: 'otter_dk')                                  # ear
    shape(c, ell(49, 28 + b, 8, 6.5), lit3(49, 28 + b, 8, 6.5, 'otter_lt', 'otter', 'otter_dk'))
    shape(c, ell(56, 30 + b, 4, 2.6), lambda x, y: 'muzzle')
    c.set(59, 29 + b, 'eye'); c.set(60, 29 + b, 'eye'); c.set(59, 30 + b, 'eye')
    eye(c, 51, 25 + b)
    for (x, y) in ((56, 33), (58, 33), (60, 32), (61, 31)):
        c.set(x, y + b, 'muzzle')
    shape(c, ell(46, 36 + b + (-1 if ph else 1), 2.6, 2.0), lambda x, y: 'otter_dk')             # front paw paddling
    return wl


def seal(c, f):
    b, ph = BOB[f], f // 2
    wl = 35 + b
    ripples(c, 34, wl, f, 24)
    for dy in (-4, 4):                                                                            # tail flippers
        shape(c, limb(17, 31 + b, 9, 31 + b + dy + (1 if ph else -1), 2.4, 1.4), lambda x, y: 'seal_dk')
    base = lit3(30, 30 + b, 15, 8, 'seal_lt', 'seal', 'seal_dk')
    shape(c, ell(30, 30 + b, 15, 8), lambda x, y: 'seal_dk' if (x * 5 + y * 3) % 13 == 0 else base(x, y))
    rider(c, 16, 27 + b)
    shape(c, ell(50, 28 + b, 8, 6.5), lit3(50, 28 + b, 8, 6.5, 'seal_lt', 'seal', 'seal_dk'))
    shape(c, ell(56, 30.5 + b, 3.6, 2.4), lambda x, y: 'seal_lt')
    c.set(59, 29 + b, 'eye'); c.set(60, 29 + b, 'eye')
    eye(c, 51, 25 + b, tall=3)
    for (x, y) in ((55, 32), (57, 32), (56, 33)):
        c.set(x, y + b, 'seal_dk')
    shape(c, limb(43, 33 + b, 47, 38 + b + (-2 if ph else 1), 2.4, 1.5), lambda x, y: 'seal_dk')   # fore flipper
    return wl


def turtle(c, f):
    b, ph = BOB[f], f // 2
    wl = 34 + b
    ripples(c, 34, wl, f, 24)
    shape(c, limb(17, 33 + b, 9, 36 + b + (1 if ph else -1), 2.4, 1.2), lit3(0, 0, 1, 1, 'tskin', 'tskin', 'tskin_dk'))
    shape(c, limb(42, 31 + b, 50, 31 + b, 3.0, 2.6), lambda x, y: 'tskin')                        # neck
    seeds = [(-8, -2), (0, -4), (8, -2), (-4, 3), (5, 3)]

    def scol(x, y):
        nx, ny = (x - 30) / 16, (y - 29 - b) / 8.5
        if nx * nx + ny * ny > 0.62:
            return 'shell_rim' if ((x * 3) % 5) else 'shell_dk'
        dd = sorted(((x - 30 - px) ** 2 + ((y - 29 - b - py) * 1.6) ** 2) ** 0.5 for (px, py) in seeds)
        if dd[1] - dd[0] < 1.4:
            return 'shell_dk'
        return 'shell_lt' if -(0.6 * nx + 0.8 * ny) > 0.1 else 'shell'
    shape(c, ell(30, 29 + b, 16, 8.5), scol)
    rider(c, 16, 25 + b)
    shape(c, ell(53, 30 + b, 6, 5), lit3(53, 30 + b, 6, 5, 'tskin_lt', 'tskin', 'tskin_dk'))
    eye(c, 54, 28 + b)
    for x in (55, 56, 57):
        c.set(x, 32 + b, 'tskin_dk')
    shape(c, limb(40, 34 + b, 51, 37 + b + (-3 if ph else 2), 3.0, 1.4), lit3(45, 36 + b, 8, 4, 'tskin_lt', 'tskin', 'tskin_dk'))
    return wl


def duck(c, f):
    b, ph = BOB[f], f // 2
    wl = 35 + b
    ripples(c, 34, wl, f, 24)
    shape(c, limb(17, 27 + b, 11, 22 + b, 2.6, 1.6), lambda x, y: 'duck')                        # tail tuft
    shape(c, ell(30, 30 + b, 15, 8), lit3(30, 30 + b, 15, 8, 'duck', 'duck', 'duck_sh'))
    shape(c, limb(41, 28 + b, 47, 21 + b, 3.6, 3.0), lambda x, y: 'duck')                         # neck
    rider(c, 15, 27 + b)
    lift = 1 if ph else 0
    shape(c, ell(27, 30 + b - lift, 10, 5), lambda x, y: 'duck_dk' if x < 21 else 'duck_sh')     # folded wing
    shape(c, ell(49, 18 + b, 6.5, 6), lit3(49, 18 + b, 6.5, 6, 'duck', 'duck', 'duck_sh'))
    shape(c, ell(57, 20 + b, 4.2, 2.2), lambda x, y: 'bill' if y < 21 + b else 'bill_dk')
    eye(c, 51, 16 + b)
    c.set(50, 20 + b, 'blush')
    for k, dx in enumerate((24, 34)):
        shape(c, ell(dx, 39 + b + ((k + ph) % 2), 3, 1.2), lambda x, y: 'bill')
    return wl


IDEAS = [
    ('1  Otter', 'Playful, paddles with its paws.', otter),
    ('2  Seal pup', 'Big dark eyes, flaps its flippers.', seal),
    ('3  Little turtle', 'Calm and steady, rows with flippers.', turtle),
    ('4  Big duck', 'Toy-like, waddle-paddles its feet.', duck),
]


def quantize(a):
    f = a.reshape(-1, 3).astype(float)
    uniq, inv = np.unique(f, axis=0, return_inverse=True)
    pick = np.argmin(((to_lab(uniq)[:, None, :] - QL[None]) ** 2).sum(-1), axis=1)
    return QP[pick][inv.ravel()].reshape(a.shape).astype(np.uint8)


def frames():
    FB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
    FN = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    FH = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    gap, lab, top = 16, 52, 74
    W = 2 * CW * SC + 3 * gap
    H = top + 2 * (CH * SC + lab + gap)
    out = []
    for f in range(4):
        im = Image.new('RGB', (W, H), (43, 38, 34))
        d = ImageDraw.Draw(im)
        d.text((gap, 18), 'SURF COMPANION IDEAS', font=FH, fill=(244, 235, 216))
        d.text((gap, 50), 'Small, friendly, gently animated. Shown 5x (in game ~2-4x).', font=FN, fill=(201, 168, 120))
        for i, (name, desc, fn) in enumerate(IDEAS):
            c = Cell()
            water(c, f)
            wl = fn(c, f)
            finish(c, wl)
            tile = Image.fromarray(quantize(c.img)).resize((CW * SC, CH * SC), Image.NEAREST)
            x0 = gap + (i % 2) * (CW * SC + gap)
            y0 = top + (i // 2) * (CH * SC + lab + gap)
            d.rectangle([x0 - 3, y0 - 3, x0 + CW * SC + 2, y0 + CH * SC + 2], fill=(201, 168, 120))
            im.paste(tile, (x0, y0))
            d.text((x0, y0 + CH * SC + 8), name, font=FB, fill=(244, 235, 216))
            d.text((x0, y0 + CH * SC + 32), desc, font=FN, fill=(190, 178, 160))
        out.append(im)
    return out




# ------------------------------------------------------------------ chosen design: otter (Mount Flute) + seal (Seal Flute)
SIDE_FULL = SIDE + list(CART[14:18])          # seated hero, hat to belt


def rider_full(c, x0, bottom):
    for dy, row in enumerate(SIDE_FULL):
        for dx, ch in enumerate(row):
            if ch != '.':
                c.set(x0 + dx, bottom - len(SIDE_FULL) + 1 + dy, CPAL[ch])


def _surf(c, f, kind):
    """hero sits on top; the animal is mostly under water: a low back, head top, eyes and nose above the surface"""
    b, ph = BOB[f], f // 2
    wl = 34 + b
    lt, md, dk = ('otter_lt', 'otter', 'otter_dk') if kind == 'otter' else ('seal_lt', 'seal', 'seal_dk')
    ripples(c, 36, wl, f, 22)
    if kind == 'otter':
        shape(c, limb(19, 35 + b, 6, 38 + b, 3.0, 2.0), lambda x, y: md)                      # tail (submerged)
    else:
        for dy in (-3, 3):
            shape(c, limb(19, 35 + b, 10, 35 + b + dy, 2.4, 1.4), lambda x, y: dk)          # tail flippers
    for side_x, down in ((25, ph == 0), (47, ph == 1)):                                         # paddling limbs
        shape(c, ell(side_x, 38 + b + (1 if down else 0), 3, 2), lambda x, y: dk)
        if down:
            for (dx, dy) in ((-3, -5), (0, -6), (3, -5)):
                c.set(side_x + dx, wl + dy + 6, 'foam', obj=False)
    body = ell(35, 34 + b, 17, 7)
    back = lit3(35, 34 + b, 17, 7, lt, md, dk)
    shape(c, body, back)
    rider_full(c, 24, 31 + b)
    for (x, y) in body:                                                                         # near rim of the back seats the rider
        if y >= 31 + b and not any((x + dx, y + dy) not in body for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            c.set(x, y, back(x, y))
    hx_, hy_ = 53, 32 + b
    if kind == 'otter':
        shape(c, ell(hx_ - 4, hy_ - 5, 1.8, 1.8), lambda x, y: dk)                             # little ear
    shape(c, ell(hx_, hy_, 6.5, 5), lit3(hx_, hy_, 6.5, 5, lt, md, dk))
    shape(c, ell(hx_ + 5, hy_ + 1, 3, 2), lambda x, y: 'muzzle' if kind == 'otter' else lt)
    c.set(hx_ + 8, hy_, 'eye'); c.set(hx_ + 7, hy_, 'eye')
    for dy in range(2 if kind == 'otter' else 3):
        c.set(hx_ + 1, hy_ - 3 + dy, 'eye'); c.set(hx_ + 2, hy_ - 3 + dy, 'eye')
    c.set(hx_ + 1, hy_ - 3, 'snow_lt')
    return wl


def otter_surf(c, f):
    return _surf(c, f, 'otter')


def seal_surf(c, f):
    return _surf(c, f, 'seal')

def cold_water(c, f):
    """darker cold water with drifting ice floes and falling snow"""
    c.img[:] = PAL['sea_dp']
    rng = np.random.default_rng(11)
    for _ in range(22):
        x, y = int(rng.integers(0, CW)), int(rng.integers(0, CH))
        for k in range(3):
            c.set((x + k + f) % CW, y, 'sea', obj=False)
    for (fx, fy, rx, ry) in ((8, 8, 6, 2.5), (64, 12, 5, 2), (58, 42, 7, 2.5), (10, 41, 4, 1.8)):
        x0 = fx - f // 2
        for (x, y) in ell(x0, fy, rx, ry):
            col = 'snow' if y < fy + ry * 0.75 else 'frz_hi'
            c.set(x, y, col, obj=False)
        for x in range(int(x0 - rx) + 1, int(x0 + rx)):
            c.set(x, int(fy + ry) + 1, 'frz_dk', obj=False)


def snowfall(c, f):
    rng = np.random.default_rng(12)
    for _ in range(18):
        x, y = int(rng.integers(0, CW)), int(rng.integers(0, CH))
        c.set((x - f) % CW, (y + f * 2) % CH, 'snow_lt', obj=False)


def _icon(kind):
    """16x16 backpack icons"""
    g = [['.'] * 16 for _ in range(16)]

    def put(x, y, k):
        if 0 <= x < 16 and 0 <= y < 16:
            g[y][x] = k
    if kind in ('mount_flute', 'seal_flute'):
        lt, md, dk = ('wood_lt', 'wood', 'wood_dk') if kind == 'mount_flute' else ('snow_lt', 'frz_hi', 'frz')
        for i in range(23):
            t = i / 22
            cx_, cy_ = 2 + 11 * t, 13 - 11 * t
            for off, k in ((-1, lt), (0, md), (1, dk)):
                put(int(round(cx_ + off * 0.7)), int(round(cy_ + off * 0.7)), k)
        for t in (0.42, 0.56, 0.7):
            put(int(round(2 + 11 * t)), int(round(13 - 11 * t)), 'eye')
        put(5, 10, 'gold'); put(4, 11, 'gold')
        tas = 'blanket' if kind == 'mount_flute' else 'shut'
        for (x, y) in ((2, 14), (1, 15), (3, 15), (2, 15)):
            put(x, y, tas)
        if kind == 'seal_flute':
            for (x, y) in ((10, 3), (12, 3), (11, 4), (10, 5), (12, 5)):
                put(x, y, 'shut_dk')
    else:                                                     # otter stick: driftwood, cord wrap, otter-head knob
        for i in range(25):
            t = i / 24
            cx_, cy_ = 3 + 8 * t, 15 - 12 * t
            put(int(round(cx_)), int(round(cy_)), 'wood_lt'); put(int(round(cx_)) + 1, int(round(cy_)), 'wood_dk')
        for y in (8, 9, 10):
            put(int(round(3 + 8 * (15 - y) / 12)), y, 'shut'); put(int(round(3 + 8 * (15 - y) / 12)) + 1, y, 'shut_dk')
        for (x, y, k) in ((10, 1, 'otter'), (11, 1, 'otter'), (12, 1, 'otter'), (9, 2, 'otter'), (10, 2, 'otter_lt'),
                          (11, 2, 'otter'), (12, 2, 'eye'), (13, 2, 'muzzle'), (10, 3, 'otter'), (11, 3, 'otter'),
                          (12, 3, 'muzzle'), (13, 3, 'muzzle'), (9, 0, 'otter_dk')):
            put(x, y, k)
    for y in range(16):                                       # auto outline
        for x in range(16):
            if g[y][x] == '.' and any(0 <= x + dx < 16 and 0 <= y + dy < 16 and g[y + dy][x + dx] not in '.o'
                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'o'
    a = np.zeros((16, 16, 4), np.uint8)
    for y in range(16):
        for x in range(16):
            k = g[y][x]
            if k != '.':
                a[y, x, :3] = PAL['ink'] if k == 'o' else PAL[k]
                a[y, x, 3] = 255
    a[..., :3] = quantize(a[..., :3])
    return Image.fromarray(a, 'RGBA')


def chosen_frames():
    FB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
    FS = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
    FN = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    FH = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    gap, top = 16, 74
    W = 2 * CW * SC + 3 * gap
    panel_h = CH * SC + 56
    H = top + panel_h + gap + 104
    icons = [('Otter Stick', 'Guides your otter.\nUse it at any shore.', _icon('otter_stick')),
             ('Seal Flute', 'Calls a seal for\ncold water.', _icon('seal_flute'))]
    out = []
    for f in range(4):
        im = Image.new('RGB', (W, H), (43, 38, 34))
        d = ImageDraw.Draw(im)
        d.text((gap, 18), 'SURFING: OTTER + SEAL', font=FH, fill=(244, 235, 216))
        d.text((gap, 50), 'Rider on top, animal mostly under water. Loop shown 5x; backpack icons below.', font=FN, fill=(201, 168, 120))
        for i, (title, sub, fn, bg) in enumerate((('Otter', 'Otter Stick: lakes, rivers, the open sea', otter_surf, water),
                                                  ('Seal', 'Seal Flute: cold water, ice floes', seal_surf, cold_water))):
            c = Cell()
            bg(c, f)
            wl = fn(c, f)
            finish(c, wl, keep=0.38)
            if bg is cold_water:
                snowfall(c, f)
            tile = Image.fromarray(quantize(c.img)).resize((CW * SC, CH * SC), Image.NEAREST)
            x0 = gap + i * (CW * SC + gap)
            d.rectangle([x0 - 3, top - 3, x0 + CW * SC + 2, top + CH * SC + 2], fill=(201, 168, 120))
            im.paste(tile, (x0, top))
            d.text((x0, top + CH * SC + 8), title, font=FB, fill=(244, 235, 216))
            d.text((x0, top + CH * SC + 34), sub, font=FN, fill=(190, 178, 160))
        y0 = top + panel_h + gap
        for i, (name, desc, ic) in enumerate(icons):
            x0 = gap + i * (CW * SC + gap)
            d.rectangle([x0, y0, x0 + 88, y0 + 88], fill=(30, 27, 44))
            d.rectangle([x0 + 2, y0 + 2, x0 + 86, y0 + 86], fill=(61, 53, 80))
            im.paste(ic.resize((80, 80), Image.NEAREST), (x0 + 4, y0 + 4), ic.resize((80, 80), Image.NEAREST))
            d.text((x0 + 98, y0 + 16), name, font=FS, fill=(244, 235, 216))
            d.multiline_text((x0 + 98, y0 + 42), desc, font=FN, fill=(190, 178, 160), spacing=3)
        out.append(im)
    return out


def save_gif(frames_, dst):
    fr = [f.convert('P', palette=Image.Palette.ADAPTIVE, colors=255) for f in frames_]
    fr[0].save(dst, save_all=True, append_images=fr[1:], duration=200, loop=0, disposal=1)


if __name__ == '__main__':
    import os
    out_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    save_gif(frames(), os.path.join(out_dir, 'surf_ideas.gif'))
    save_gif(chosen_frames(), os.path.join(out_dir, 'surf_otter_seal.gif'))
    print('saved surf_ideas.gif, surf_otter_seal.gif')
