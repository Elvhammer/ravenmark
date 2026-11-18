"""Part 3 art: the wider world. New map objects (fallen trees, the museum, eastern houses, stone lanterns,
blossom trees, the dragon shrine, telescopes, the ferry...), the region grounds, new NPCs and item icons,
the whale, the dragon, the erne carrying you by its feet, the Dragon Band on the hero, telescope views and
the world map. Called from proto_build.py after proto_art2.
"""
import json
import os
import numpy as np
from PIL import Image

import proto_build as PB
import proto_art2 as A2
import proto_regions as REG

G = PB.G
ART = PB.ART
C = PB.C
SEASONS = PB.SEASONS
setp, ellipse_pts, lit_key, add = A2.setp, A2.ellipse_pts, A2.lit_key, A2.add
Spr, shade3, ell, limb = A2.Spr, A2.shade3, A2.ell, A2.limb


# ====================================================================== seasonal map objects
def draw_fallen_tree(ax, ay):
    """a storm-felled trunk lying across the path, roots on one end and a leafy crown on the other"""
    G['fallen_log'](ax - 12, ax + 9, ay)

    def leaves():
        pts = {}
        for (ox, oy, r) in [(14, -7, 6), (19, -4, 5), (12, -2, 4.5), (18, -10, 4)]:
            for (x, y) in ellipse_pts(ax + ox, ay + oy, r, r * 0.8):
                pts[(x, y)] = True
        for (x, y) in pts:
            setp(x, y, lit_key((x - ax - 15) / 7, (y - ay + 6) / 6, ['leaf_hi', 'leaf_lt', 'leaf', 'leaf_dk'], x, y, 0.5))
        for (x, y) in pts:
            if (x + 1, y) not in pts or (x, y + 1) not in pts:
                setp(x, y, 'leaf_ol')
        for (x, y) in ((ax - 15, ay - 9), (ax - 16, ay - 6), (ax - 14, ay - 2), (ax - 17, ay - 3), (ax - 15, ay - 12)):
            setp(x, y, 'trunk_dk'); setp(x + 1, y, 'trunk')
    add(ay + 1, leaves)


def draw_axe_stump(ax, ay, axe=True):
    G['stump'](ax, ay)
    if not axe:
        return

    def draw():
        for k in range(11):                                              # handle
            setp(ax + 2 + k // 2, ay - 9 - k, 'wood_lt'); setp(ax + 3 + k // 2, ay - 9 - k, 'wood_dk')
        for y in range(ay - 12, ay - 7):                                 # head buried in the stump top
            for x in range(ax - 3, ax + 3):
                setp(x, y, 'iron' if x < ax else 'slate_dk')
        setp(ax - 4, ay - 10, 'stone_lt'); setp(ax - 4, ay - 9, 'stone_lt')
    add(ay + 1, draw)


def draw_telescope(ax, ay):
    def draw():
        for (x1, y1) in ((ax - 6, ay), (ax + 5, ay), (ax, ay - 1)):     # tripod
            n = 14
            for t in range(n + 1):
                setp(ax + (x1 - ax) * t // n, ay - 14 + (y1 - ay + 14) * t // n, 'trunk_dk')
        for t in range(18):                                              # brass tube, aimed at the horizon
            x = ax - 7 + t
            y = ay - 13 - t // 3
            w = 2 if t < 12 else 3
            for k in range(w):
                c = 'gold' if k == 0 else ('wood_lt' if k == 1 else 'wood')
                if t in (5, 11):
                    c = 'trunk_dk'
                setp(x, y + k, c)
        setp(ax + 11, ay - 19, 'glass_lt'); setp(ax + 11, ay - 18, 'glass')
        setp(ax - 8, ay - 13, 'ink'); setp(ax - 8, ay - 12, 'ink')
    add(ay, draw, (ax + 3, ay, 7, 2))


def draw_museum(ax, ay):
    """stone museum with a columned porch around the door (door centred 40 px from the left edge)"""
    G['shadows'].append((ax + 36, ay + 1, 36, 4))

    def draw():
        x0, x1, top = ax, ax + 63, ay - 40
        for y in range(top, ay + 1):                                     # walls
            for x in range(x0, x1 + 1):
                row = (y - top) // 5
                c = 'stone_lt' if x < x0 + 20 else ('stone' if x < x1 - 8 else 'stone_dk')
                if (y - top) % 5 == 0 or (x + (4 if row % 2 else 0)) % 9 == 0:
                    c = 'stone' if c == 'stone_lt' else 'stone_dk'
                if x in (x0, x1) or y == ay:
                    c = 'ink'
                setp(x, y, c)
        for y in range(top - 14, top + 1):                               # slate roof, a low triangle
            half = (y - top + 14) * 36 // 14
            for x in range(ax + 32 - half - 2, ax + 32 + half + 2):
                if x0 - 2 <= x <= x1 + 2:
                    c = 'slate_lt' if x < ax + 32 else 'slate'
                    if y == top or abs(x - (ax + 32)) == half + 1:
                        c = 'ink'
                    setp(x, y, c)
        for (wx, wy) in ((x0 + 6, top + 8), (x0 + 6, top + 22), (x1 - 13, top + 8)):   # tall windows
            for y in range(wy, wy + 10):
                for x in range(wx, wx + 7):
                    setp(x, y, 'ink' if x in (wx, wx + 6) or y in (wy, wy + 9) else ('glass_lt' if y < wy + 3 else 'glass'))
        dx = ax + 40                                                     # the porch: pediment, columns, door
        for y in range(top + 2, top + 10):
            half = (y - top - 2) * 14 // 8
            for x in range(dx - half - 1, dx + half + 2):
                setp(x, y, 'ink' if abs(x - dx) >= half or y == top + 9 else 'wall')
        setp(dx, top + 6, 'gold'); setp(dx - 1, top + 7, 'gold'); setp(dx + 1, top + 7, 'gold')
        for cx in (dx - 13, dx - 8, dx + 7, dx + 12):
            for y in range(top + 10, ay - 2):
                setp(cx, y, 'wall'); setp(cx + 1, y, 'wall_sh'); setp(cx + 2, y, 'stone_dk')
        for y in range(ay - 18, ay - 1):
            for x in range(dx - 5, dx + 5):
                setp(x, y, 'door' if x not in (dx - 5, dx + 4) and y != ay - 18 else 'ink')
        setp(dx + 2, ay - 9, 'gold')
        for x in range(x0 - 2, x1 + 3):                                  # steps
            setp(x, ay - 1, 'stone_lt'); setp(x, ay, 'stone')
        for y in range(top + 12, top + 18):                              # banner with a gold emblem
            for x in range(x0 + 24, x0 + 30):
                setp(x, y, 'band' if y < top + 17 else 'roof_dk')
        setp(x0 + 26, top + 14, 'gold'); setp(x0 + 27, top + 14, 'gold'); setp(x0 + 26, top + 15, 'gold')
    G['objects'].append((ay, draw))


EAST_HOUSE = {'roof_lt': '#E48A73', 'roof': '#B8483A', 'roof_dk': '#6E4A35', 'roof_ln': '#6E4A35',
              'wall': '#F2E3B3', 'wall_sh': '#E0A256', 'wall_dk': '#A8693F'}


def draw_house_e(ax, ay):
    """an eastern house: red tiled roof with upturned eaves, pale walls, a hanging lantern"""
    G['house_v2'](ax, ay - 52)

    def eaves():
        rb = ay - 52 + 27
        for k in range(5):
            for (x, d) in ((ax - 1 - k, -1), (ax + 66 + k, 1)):
                setp(x, rb - k, 'roof_dk'); setp(x, rb - k - 1, 'roof')
                if k == 4:
                    setp(x, rb - k - 2, 'ink')
        for y in range(rb + 2, rb + 8):                                  # lantern under the eave
            setp(ax + 50, y, 'iron') if y < rb + 4 else None
        for (x, y) in ellipse_pts(ax + 50, rb + 7, 2.5, 3):
            setp(x, y, 'glow' if abs(x - ax - 50) < 2 else 'band')
    G['objects'].append((ay + 1, eaves))


def draw_stone_lantern(ax, ay):
    def draw():
        for y in range(ay - 3, ay + 1):
            for x in range(ax - 5, ax + 6):
                setp(x, y, 'stone_dk' if x > ax + 2 or y == ay else 'stone')
        for y in range(ay - 10, ay - 3):
            for x in range(ax - 2, ax + 3):
                setp(x, y, 'stone_lt' if x < ax else 'stone_dk')
        for y in range(ay - 17, ay - 10):
            for x in range(ax - 4, ax + 5):
                inside = ax - 2 <= x <= ax + 2 and ay - 16 <= y <= ay - 12
                setp(x, y, 'glow' if inside else ('stone' if x < ax + 2 else 'stone_dk'))
        for y in range(ay - 20, ay - 17):
            w = 7 - (ay - 18 - y)
            for x in range(ax - w, ax + w + 1):
                setp(x, y, 'stone_dk' if y == ay - 18 else 'stone')
        setp(ax - 7, ay - 19, 'stone_dk'); setp(ax + 7, ay - 19, 'stone_dk'); setp(ax, ay - 21, 'stone')
    add(ay, draw, (ax + 3, ay, 6, 2))


LEAF_BLOSSOM = {
    'spring': ('#B8483A', '#E48A73', '#F2E3B3', '#F2E3B3'),
    'summer': ('#2F4A35', '#4F7A3C', '#E48A73', '#F2E3B3'),
    'autumn': ('#6E4A35', '#B8483A', '#E48A73', '#E0A256'),
    'winter': ('#1E1B2C', '#3D3550', '#6E4A35', '#6E4A35'),
}


def draw_shrine(ax, ay):
    """the dragon shrine: stone platform, red pillars, a double roof with upturned corners"""
    G['shadows'].append((ax + 6, ay + 1, 42, 4))

    def roof(top, half, h, lt, md, dk):
        for y in range(top, top + h):
            k = (y - top) / max(1, h - 1)
            w = int(half * (0.55 + 0.45 * k))
            for x in range(ax - w, ax + w + 1):
                c = lt if x < ax - w // 3 else (md if x < ax + w // 2 else dk)
                if (x + y) % 4 == 0:
                    c = dk
                if y == top or x in (ax - w, ax + w):
                    c = 'ink'
                setp(x, y, c)
        for k in range(4):                                               # upturned corners
            for sx in (-1, 1):
                x = ax + sx * (half + 1 + k)
                setp(x, top + h - 1 - k, md); setp(x, top + h - 2 - k, 'ink')
        for x in range(ax - int(half * 0.55), ax + int(half * 0.55) + 1):
            setp(x, top, 'gold')

    def draw():
        for y in range(ay - 7, ay + 1):                                  # platform + steps
            for x in range(ax - 38, ax + 39):
                c = 'stone_lt' if (y - ay) % 3 == 0 else 'stone'
                if x > ax + 30:
                    c = 'stone_dk'
                if x in (ax - 38, ax + 38) or y == ay:
                    c = 'ink'
                setp(x, y, c)
        for y in range(ay - 30, ay - 7):                                 # the hall
            for x in range(ax - 30, ax + 31):
                c = 'trunk_dk' if (x - ax) % 6 else 'trunk'
                if abs(x - ax) < 9 and y > ay - 24:
                    c = C('#1E1B2C')
                if abs(x - ax) == 9 and y > ay - 24:
                    c = 'gold'
                setp(x, y, c)
        for px in (ax - 30, ax - 18, ax + 16, ax + 28):                  # red pillars
            for y in range(ay - 31, ay - 7):
                setp(px, y, 'roof_lt'); setp(px + 1, y, 'band'); setp(px + 2, y, 'roof_dk')
        roof(ay - 42, 40, 12, 'river_lt', 'river', 'river_dp')
        for x in range(ax - 24, ax + 25):
            for y in range(ay - 47, ay - 42):
                setp(x, y, 'band' if (x // 3) % 2 else 'roof_dk')
        roof(ay - 58, 26, 11, 'river_lt', 'river', 'river_dp')
        for y in range(ay - 66, ay - 58):                                # golden finial
            setp(ax, y, 'gold'); setp(ax + 1, y, 'wood_lt')
        for (x, y) in ellipse_pts(ax, ay - 67, 2, 2):
            setp(x, y, 'gold')
        for lx in (ax - 24, ax + 23):                                    # lanterns under the eaves
            setp(lx, ay - 30, 'iron')
            for (x, y) in ellipse_pts(lx, ay - 26, 2.5, 3.5):
                setp(x, y, 'glow' if abs(x - lx) < 2 else 'band')
    G['objects'].append((ay, draw))


def draw_whalebone(ax, ay):
    def draw():
        for sx in (-1, 1):
            for t in range(28):
                x = ax + sx * int(round(9 * np.cos(t / 27 * np.pi / 2) + 1))
                y = ay - t
                setp(x, y, 'cream'); setp(x + sx, y, 'sand_dk' if sx > 0 else 'sand_lt')
        for x in range(ax - 2, ax + 3):
            setp(x, ay - 28, 'cream')
    add(ay, draw, (ax + 3, ay, 10, 2))


def draw_ferry(ax, ay):
    """Captain Nils's little ferry (bow to the right)"""
    def draw():
        cy = ay - 5
        for x in range(ax - 24, ax + 25):                                # hull
            t = (x - ax + 24) / 48
            half = int(round(6 * (1 - max(0, t - 0.75) * 3.2) if t > 0.75 else 6))
            for y in range(cy - half, cy + half + 1):
                edge = abs(y - cy) >= half - 1
                c = ('roof' if y > cy else 'roof_lt') if edge else ('plank_lt' if (x // 4) % 2 else 'plank')
                if abs(y - cy) == half:
                    c = 'ink'
                setp(x, y, c)
        for x in range(ax - 22, ax + 18):                                # waterline
            setp(x, cy + 7, 'foam' if (x // 2) % 2 else 'sea_lt')
        for y in range(cy - 14, cy + 2):                                 # cabin
            for x in range(ax - 10, ax + 6):
                c = 'wall' if x < ax + 3 else 'wall_sh'
                if y < cy - 11:
                    c = 'roof_dk' if y == cy - 14 else 'roof'
                if x in (ax - 10, ax + 5):
                    c = 'ink'
                setp(x, y, c)
        for wx in (ax - 7, ax - 2):
            for y in range(cy - 9, cy - 5):
                setp(wx, y, 'glass'); setp(wx + 1, y, 'glass')
        for y in range(cy - 22, cy - 13):                                # funnel
            setp(ax - 15, y, 'band'); setp(ax - 14, y, 'roof_dk')
        setp(ax - 15, cy - 22, 'ink'); setp(ax - 14, cy - 22, 'ink')
        for (x, y) in ((ax - 16, cy - 25), (ax - 18, cy - 27), (ax - 17, cy - 26), (ax - 20, cy - 29)):
            setp(x, y, 'stone_lt')
        for x in range(ax + 8, ax + 20, 3):                              # rail
            setp(x, cy - 6, 'wood_dk')
    add(ay, draw)


NEW_KINDS = {
    'fallen_tree': (draw_fallen_tree, (56, 32), (28, 26), {'snow': 2}),
    'axe_stump': (draw_axe_stump, (32, 32), (16, 26), {'snow': 1}),
    'axe_stump_empty': (lambda x, y: draw_axe_stump(x, y, False), (32, 32), (16, 26), {'snow': 1}),
    'telescope': (draw_telescope, (32, 32), (14, 28), {'snow': 1}),
    'museum': (draw_museum, (96, 80), (8, 72), {'snow': 1}),
    'house_e': (draw_house_e, (104, 80), (12, 72), {'extra': EAST_HOUSE, 'snow': 1}),
    'stone_lantern': (draw_stone_lantern, (24, 28), (12, 24), {'snow': 1}),
    'blossom': (lambda x, y: G['tree'](x, y, 0.9), (72, 72), (36, 66), {'leaf': LEAF_BLOSSOM, 'snow': 4}),
    'shrine': (draw_shrine, (96, 80), (48, 74), {'snow': 1}),
    'whalebone': (draw_whalebone, (32, 36), (16, 32), {'snow': 1}),
    'wreck': (lambda x, y: G['wreck'](x, y), (64, 24), (32, 18), {'sea': True}),
    'ferry': (draw_ferry, (64, 44), (32, 34), {'sea': True}),
}
NEW_EMISSIVE = {'house_e': ('glass', 'glass_lt', 'glow'), 'stone_lantern': ('glow',), 'shrine': ('glow',),
                'museum': ('glass', 'glass_lt'), 'ferry': ('glass',)}


# ====================================================================== interiors
def draw_pedestal(ax, ay):
    def draw():
        for y in range(ay - 12, ay + 1):
            w = 6 if y < ay - 9 or y > ay - 2 else 4
            for x in range(ax - w, ax + w + 1):
                c = 'stone_lt' if x < ax - 1 else ('stone' if x < ax + 3 else 'stone_dk')
                if x in (ax - w, ax + w) or y in (ay - 12, ay):
                    c = 'ink'
                setp(x, y, c)
    add(ay, draw, (ax + 3, ay, 7, 2))


def draw_painting(ax, ay):
    def draw():
        x0, y0 = ax - 11, ay - 28
        for y in range(y0, y0 + 16):
            for x in range(x0, x0 + 22):
                if x in (x0, x0 + 21) or y in (y0, y0 + 15):
                    c = 'gold'
                elif y < y0 + 8:
                    c = 'glass_lt' if y < y0 + 4 else 'river_lt'
                elif y < y0 + 10:
                    c = 'river'
                else:
                    c = 'leaf' if (x + y) % 3 else 'leaf_dk'
                setp(x, y, c)
        for k in range(5):                                               # a little whale in the picture
            setp(x0 + 8 + k, y0 + 9, 'slate'); setp(x0 + 9 + k // 2, y0 + 8, 'slate')
        setp(x0 + 12, y0 + 6, 'cream')
    add(ay - 20, draw)


ROOM_KINDS = {
    'pedestal': (draw_pedestal, (24, 20), (12, 16), {}),
    'painting': (draw_painting, (32, 36), (16, 32), {}),
}


# ====================================================================== people
NPC_STYLES = {
    'edvin': ('brim', {'H': '#4F7A3C', 'h': '#2F4A35', 'L': '#8DB054', 'r': '#A8693F', 'k': '#F2E3B3', 'K': '#8A8496',
                       'c': '#6E4A35', 'C': '#3D3550', 'l': '#A8693F', 'y': '#4E8C95', 'Y': '#2E5466'},
              {'beard': '#F2E3B3', 'long_beard': True, 'scarf': True}),
    'gerda': ('cap', {'H': '#A8693F', 'h': '#6E4A35', 'L': '#E0A256', 'k': '#B8483A', 'K': '#6E4A35', 'c': '#6E4A35',
                      'C': '#3D3550', 'l': '#A8693F', 'y': '#E0A256', 'Y': '#A8693F'}, {'apron': '#8A8496'}),
    'nils': ('cap', {'H': '#1E1B2C', 'h': '#1E1B2C', 'L': '#3D3550', 'k': '#F2E3B3', 'K': '#8A8496', 'c': '#2E5466',
                     'C': '#1E1B2C', 'l': '#4E8C95', 'b': '#E0A256', 'y': '#F2E3B3', 'Y': '#8A8496'},
             {'beard': '#F2E3B3'}),
    'agnes': ('hair_bun', {'k': '#8A8496', 'K': '#3D3550', 'c': '#3D3550', 'C': '#1E1B2C', 'l': '#8A8496',
                           'p': '#3D3550', 'P': '#1E1B2C', 'y': '#E0A256', 'Y': '#A8693F', 'b': '#E0A256'}, {}),
    'pim': ('cap', {'H': '#B8483A', 'h': '#6E4A35', 'L': '#E48A73', 'k': '#E0A256', 'K': '#A8693F', 'c': '#4F7A3C',
                    'C': '#2F4A35', 'l': '#8DB054', 'y': '#4F7A3C', 'Y': '#2F4A35'}, {}),
    'inga': ('hood', {'H': '#F2E3B3', 'h': '#9CD0C9', 'L': '#F2E3B3', 'k': '#B8483A', 'K': '#6E4A35', 'c': '#2E5466',
                      'C': '#1E1B2C', 'l': '#4E8C95', 'y': '#F2E3B3', 'Y': '#9CD0C9'}, {'long': True}),
    'bo': ('hood', {'H': '#6E4A35', 'h': '#3D3550', 'L': '#A8693F', 'k': '#E0A256', 'K': '#A8693F', 'c': '#B8483A',
                    'C': '#6E4A35', 'l': '#E48A73', 'y': '#F2E3B3', 'Y': '#9CD0C9'}, {'beard': '#E0A256'}),
    'halla': ('hood', {'H': '#9CD0C9', 'h': '#4E8C95', 'L': '#F2E3B3', 'k': '#F2E3B3', 'K': '#9CD0C9', 'c': '#3D3550',
                       'C': '#1E1B2C', 'l': '#8A8496', 'p': '#3D3550', 'P': '#1E1B2C', 'y': '#9CD0C9', 'Y': '#4E8C95'},
              {'long': True}),
    'rin': ('kerchief', {'H': '#B8483A', 'h': '#6E4A35', 'L': '#E0A256', 'k': '#1E1B2C', 'K': '#3D3550', 'c': '#F2E3B3',
                         'C': '#E0A256', 'l': '#F2E3B3', 'y': '#B8483A', 'Y': '#6E4A35', 'p': '#4E8C95', 'P': '#2E5466'},
            {}),
    'kai': ('hair', {'k': '#1E1B2C', 'K': '#3D3550', 'c': '#4E8C95', 'C': '#2E5466', 'l': '#9CD0C9', 'y': '#E0A256',
                     'Y': '#A8693F'}, {'apron': '#B8483A'}),
    'lan': ('tall', {'H': '#1E1B2C', 'h': '#1E1B2C', 'L': '#3D3550', 'r': '#B8483A', 'k': '#F2E3B3', 'K': '#8A8496',
                     'c': '#B8483A', 'C': '#6E4A35', 'l': '#E48A73', 'b': '#E0A256', 'p': '#B8483A', 'P': '#6E4A35',
                     'y': '#E0A256', 'Y': '#A8693F'}, {'beard': '#F2E3B3', 'long_beard': True}),
}


# ====================================================================== item icons
def I_whale_horn(s):
    s.shape(limb(3, 12, 12, 4, 1.4, 2.6), shade3(8, 8, 6, 5, '#F2E3B3', '#E0A256', '#A8693F'))
    for (x, y) in ((6, 9), (9, 6)):
        s.set(x, y, '#A8693F')
    s.shape(ell(13, 3.5, 1.8, 1.8), lambda x, y: '#6E4A35')


def I_dragon_band(s):
    band = ell(8, 8, 6, 4.5) - ell(8, 8, 3.6, 2.3)
    s.shape(band, lambda x, y: '#B8483A' if (x + y) % 3 else '#E0A256')
    s.shape(ell(8, 3.8, 2, 1.6), lambda x, y: '#E0A256')
    s.set(8, 3, '#F2E3B3')


def I_running_shoes(s):
    for x0, y0 in ((2, 7), (7, 9)):
        shoe = {(x, y) for x in range(x0, x0 + 8) for y in range(y0, y0 + 4) if not (x < x0 + 3 and y == y0)}
        s.shape(shoe, lambda x, y, y0=y0: '#B8483A' if y < y0 + 3 else '#F2E3B3')
    s.set(6, 8, '#F2E3B3'); s.set(11, 10, '#F2E3B3')


def I_ferry_pass(s):
    s.shape({(x, y) for x in range(2, 14) for y in range(4, 12)}, lambda x, y: '#F2E3B3' if x > 3 else '#E0A256')
    for x in range(6, 12):
        s.set(x, 6, '#3D3550')
    for x in range(6, 10):
        s.set(x, 8, '#3D3550')
    s.set(11, 9, '#B8483A'); s.set(10, 9, '#B8483A')


def I_ship_bell(s):
    bell = {(x, y) for (x, y) in ell(8, 8, 4.5, 5) if y <= 9} | {(x, 10) for x in range(2, 15)}
    s.shape(bell, shade3(8, 7, 5, 5, '#9CD0C9', '#4E8C95', '#2E5466'))
    s.shape(ell(8, 12.5, 1.3, 1.3), lambda x, y: '#3D3550')
    s.shape({(7, 2), (8, 2), (9, 2)}, lambda x, y: '#6E4A35')


def I_dragon_scale(s):
    pts = {(x, y) for x in range(2, 15) for y in range(2, 15) if (x - 8) ** 2 / 36 + (y - 6) ** 2 / 25 <= 1 and y < 13 - abs(x - 8) * 0.3}
    s.shape(pts, shade3(7, 6, 6, 5, '#E48A73', '#B8483A', '#6E4A35'))
    for y in range(4, 11):
        s.set(8, y, '#E0A256')


def I_whale_tooth(s):
    s.shape(limb(5, 13, 9, 4, 2.2, 1.0) | ell(5, 12, 2.4, 2), shade3(7, 8, 4, 5, '#F2E3B3', '#F2E3B3', '#9CD0C9'))
    s.set(6, 10, '#9CD0C9')


def I_frost_crystal(s):
    for (x0, y0, x1, y1) in ((8, 2, 8, 14), (3, 5, 13, 11), (3, 11, 13, 5)):
        s.shape(limb(x0, y0, x1, y1, 0.8, 0.8), lambda x, y: '#9CD0C9')
    s.shape(ell(8, 8, 2, 2), lambda x, y: '#F2E3B3')


def I_jade_figure(s):
    body = limb(4, 12, 7, 8, 1.6, 1.6) | limb(7, 8, 11, 9, 1.6, 1.4) | limb(11, 9, 12, 5, 1.4, 1.8)
    s.shape(body, shade3(8, 8, 5, 4, '#8DB054', '#4F7A3C', '#2F4A35'))
    s.set(12, 4, '#1E1B2C'); s.set(13, 3, '#C6D66E')


def I_old_chart(s):
    s.shape({(x, y) for x in range(2, 14) for y in range(3, 13) if not (x > 10 and y > 9)},
            lambda x, y: '#E0A256' if x in (2, 13) else '#F2E3B3')
    for (x, y) in ((4, 6), (5, 7), (6, 7), (8, 9), (9, 5), (10, 6), (5, 10)):
        s.set(x, y, '#4E8C95')
    s.set(9, 8, '#B8483A')


ICONS = {'whale_horn': I_whale_horn, 'dragon_band': I_dragon_band, 'running_shoes': I_running_shoes,
         'ferry_pass': I_ferry_pass, 'ship_bell': I_ship_bell, 'dragon_scale': I_dragon_scale,
         'whale_tooth': I_whale_tooth, 'frost_crystal': I_frost_crystal, 'jade_figure': I_jade_figure,
         'old_chart': I_old_chart}


def register():
    PB.KINDS.update(NEW_KINDS)
    PB.EMISSIVE.update(NEW_EMISSIVE)
    PB.MEDIUM_LIGHTS = PB.MEDIUM_LIGHTS + ('shrine',)
    A2.NPC_STYLES.update(NPC_STYLES)
    A2.ICONS.update(ICONS)
    A2.ROOM_KINDS.update(ROOM_KINDS)


# ====================================================================== the whale (surf mount)
WW_, WH_ = 96, 56


def whale_frame(direction, f):
    s = Spr(WW_, WH_)
    lt, md, dk, sh = '#9CD0C9', '#4E8C95', '#2E5466', '#1E1B2C'
    rise = [0, -2, -1, 1][f]
    wl = 42                                                               # waterline
    cx = 48

    def dome(x0, x1, height, xc):
        pts = {}
        for x in range(x0, x1 + 1):
            k = 1 - ((x - xc) / ((x1 - x0) / 2.0)) ** 2
            if k <= 0:
                continue
            top = int(round(wl - height * np.sqrt(k) + rise))
            for y in range(top, wl + 1):
                pts[(x, y)] = y - top
        for (x, y), d in pts.items():
            s.set(x, y, sh if d == 0 else (lt if d < 2 else (md if y < wl - 2 else dk)))
        return pts
    if direction == 'right':
        fl = 0 if f != 3 else -7                                          # tail flukes, raised every 4th frame
        fluke = limb(16, wl - 1, 8, wl - 3 + fl, 2.2, 1.4) | limb(8, wl - 3 + fl, 2, wl - 9 + fl, 1.8, 1.0) | \
            limb(8, wl - 3 + fl, 3, wl + 1 + fl, 1.8, 1.0)
        s.shape(fluke, lambda x, y: md if y < wl - 4 + fl else dk)
        dome(12, 88, 14, 50)
        for x in range(72, 87):                                           # mouth line, eye
            s.set(x, wl - 3 + (x - 72) // 7 + rise, sh)
        s.set(77, wl - 7 + rise, '#F2E3B3'); s.set(78, wl - 7 + rise, sh)
        for (x, y) in ((30, wl - 8), (34, wl - 10), (61, wl - 9), (44, wl - 12)):          # barnacles
            s.set(x, y + rise, '#F2E3B3')
        spout_x, rx = 62, 40
    else:
        if direction == 'up':
            fl = 0 if f != 3 else -5
            s.shape(limb(cx, wl, cx - 11, wl - 4 + fl, 2.0, 1.4) | limb(cx, wl, cx + 11, wl - 4 + fl, 2.0, 1.4),
                    lambda x, y: md)
        dome(cx - 30, cx + 30, 15, cx)
        if direction == 'down':
            for ex in (cx - 14, cx + 14):
                s.set(ex, wl - 6 + rise, '#F2E3B3'); s.set(ex, wl - 5 + rise, sh)
            for x in range(cx - 11, cx + 12):
                s.set(x, wl - 2 + abs(x - cx) // 7 + rise, sh)
        for (x, y) in ((cx - 18, wl - 9), (cx + 20, wl - 8), (cx - 6, wl - 13)):
            s.set(x, y + rise, '#F2E3B3')
        spout_x, rx = cx, cx - 10
    for x in range(2, 94):                                                # foam along the waterline
        if (x + f * 3) % 5 < 3:
            s.set(x, wl + 1 + (x % 3 == 0), '#F2E3B3' if x % 4 else lt)
    if f in (1, 2):                                                       # the spout
        h = 12 if f == 1 else 7
        for k in range(h):
            for w in (-1, 0, 1):
                if (k + w) % 3:
                    s.set(spout_x + w + (k // 4) * (1 if w > 0 else -1), wl - 18 - k + rise,
                          lt if k % 2 else '#F2E3B3')
    if direction == 'right':
        rows = PB.hero_body('right', 0)[:18]
    else:
        rows = PB.rider_rows('down' if direction == 'down' else 'up')
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch not in '.':
                key = PB.HPAL.get(ch) if ch != 'o' else 'ink'
                s.set(rx + dx, wl - 12 + rise - len(rows) + dy, key, outline=ch == 'o')
    return s.rgba()


def build_whale():
    sheet = np.zeros((WH_ * 3, WW_ * 4, 4), np.uint8)
    for r, d in enumerate(['down', 'up', 'right']):
        for f in range(4):
            sheet[r * WH_:(r + 1) * WH_, f * WW_:(f + 1) * WW_] = whale_frame(d, f)
    PB.save_rgba(sheet, os.path.join(ART, 'mounts', 'surf_whale.png'))


# ====================================================================== the dragon (a long, flying, Chinese-style dragon)
RED = ('#E48A73', '#B8483A', '#6E4A35')


def dragon_head(direction='right'):
    """the dragon's head, facing right (the game turns it to the flight direction)"""
    s = Spr(36, 26)
    s.shape(ell(5, 13, 4.5, 6), lambda x, y: '#4E8C95' if (x + y) % 3 else '#9CD0C9')        # mane
    for (x, y) in ((1, 7), (2, 6), (0, 12), (1, 19), (2, 20), (4, 6)):
        s.set(x, y, '#4E8C95')
    s.shape(ell(13, 12, 8, 6.5), shade3(12, 10, 8, 6, *RED))                                  # skull
    s.shape(limb(15, 10, 29, 10, 3.6, 2.8), shade3(22, 8, 7, 3, *RED))                       # upper jaw
    s.shape(ell(30, 9.5, 2.6, 2.4), shade3(30, 9, 3, 2, *RED))                                # nose
    s.set(31, 9, '#E0A256')
    s.shape(limb(15, 16, 27, 17, 2.4, 1.4), shade3(21, 17, 6, 2, *RED))                      # lower jaw
    for x in range(17, 28):                                                                   # open mouth
        s.set(x, 14, '#1E1B2C')
        if x % 2:
            s.set(x, 13, '#F2E3B3')
    for (x, y) in ((15, 7), (16, 6), (17, 6), (18, 6), (19, 7)):                              # bushy brow
        s.set(x, y, '#E48A73')
    s.set(17, 8, '#F2E3B3'); s.set(18, 8, '#1E1B2C'); s.set(17, 9, '#F2E3B3')                 # eye
    for (x0, y0, x1, y1) in ((12, 6, 3, 0), (10, 7, 1, 4), (7, 3, 5, 0)):                     # golden antlers
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):
            s.set(x0 + (x1 - x0) * t // n, y0 + (y1 - y0) * t // n, '#E0A256')
    for t in range(26):                                                                        # flowing whiskers
        s.set(29 - t, 13 + int(round(3 * np.sin(t / 4.0))) + t // 6, '#F2E3B3')
        s.set(28 - t, 8 - int(round(2 * np.sin(t / 5.0))) - t // 8, '#F2E3B3')
    for (x, y) in ((20, 19), (21, 20), (22, 19), (21, 21)):                                    # beard tuft
        s.set(x, y, '#E0A256')
    return s.rgba()


def dragon_segment(alt):
    s = Spr(14, 14)
    s.shape(ell(7, 7, 5.6, 5.6), shade3(7, 6, 5.5, 5.5, *RED))
    for (x, y) in ell(7, 10.5, 4.5, 1.6):                                                    # golden belly
        s.set(x, y, '#E0A256')
    for (x, y) in (((4, 6), (8, 5), (6, 8), (10, 8)) if alt else ((5, 5), (9, 6), (7, 8), (4, 8))):
        s.set(x, y, '#6E4A35')                                                               # scales
    for (x, y) in ((6, 1), (7, 0), (8, 1), (7, 1)):                                          # dorsal fin
        s.set(x, y, '#4E8C95' if alt else '#9CD0C9')
    return s.rgba()


def dragon_tail():
    s = Spr(22, 16)
    s.shape(ell(15, 8, 5, 4.2), shade3(15, 7, 5, 4, *RED))
    for (x0, y0, x1, y1) in ((11, 7, 1, 2), (11, 8, 0, 8), (11, 9, 1, 14), (11, 8, 4, 5), (11, 8, 4, 11)):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):
            s.set(x0 + (x1 - x0) * t // n, y0 + (y1 - y0) * t // n, '#E0A256' if t % 3 else '#E48A73')
    return s.rgba()


def dragon_leg():
    s = Spr(12, 12)
    s.shape(limb(6, 1, 6, 8, 1.6, 1.4), shade3(6, 4, 2, 4, *RED))
    for dx in (-2, 0, 2):
        s.set(6 + dx, 10, '#E0A256'); s.set(6 + dx, 9, '#E0A256')
    return s.rgba()


def build_dragon():
    d = os.path.join(ART, 'companions')
    PB.save_rgba(dragon_head(), os.path.join(d, 'dragon_head.png'))
    PB.save_rgba(dragon_segment(False), os.path.join(d, 'dragon_seg_a.png'))
    PB.save_rgba(dragon_segment(True), os.path.join(d, 'dragon_seg_b.png'))
    PB.save_rgba(dragon_tail(), os.path.join(d, 'dragon_tail.png'))
    PB.save_rgba(dragon_leg(), os.path.join(d, 'dragon_leg.png'))


# ====================================================================== the erne, carrying you by its feet
def build_erne_carry():
    orig = PB.hero_body
    PB.hero_body = lambda direction, pose: ['.' * PB.HW] * PB.HH_          # no rider on its back
    try:
        frames = [A2.erne_frame(f) for f in range(4)]
    finally:
        PB.hero_body = orig
    sheet = np.zeros((64, 112 * 4, 4), np.uint8)
    for f, fr in enumerate(frames):
        fr = fr.copy()
        for (x, y) in ((53, 40), (54, 41), (58, 40), (57, 41), (55, 42), (56, 42)):   # talons, gripping
            fr[y, x] = (*C('#E0A256'), 255)
        sheet[:, f * 112:(f + 1) * 112] = fr
    PB.save_rgba(sheet, os.path.join(ART, 'companions', 'erne_carry.png'))


# ====================================================================== the Dragon Band, worn (hero layer)
def build_band_layer():
    pos = {'down': [(15, 14), (16, 14)], 'up': [(3, 14), (4, 14)],
           'right': [[(9, 14), (10, 14)], [(10, 14), (11, 14)], [(9, 14), (10, 14)], [(8, 14), (9, 14)]]}
    sheet = np.zeros((PB.HH_ * 3, PB.HW * 4, 4), np.uint8)
    for r, d in enumerate(('down', 'up', 'right')):
        for f in range(4):
            px = pos[d][f] if d == 'right' else pos[d]
            for (x, y) in px:
                ox, oy = f * PB.HW + x, r * PB.HH_ + y
                if d != 'right' and f in (1, 3):
                    oy += 0
                sheet[oy, ox] = (*C('#E0A256'), 255)
                sheet[oy + 1, ox] = (*C('#B8483A'), 255)
    PB.save_rgba(sheet, os.path.join(ART, 'hero', 'hero_band.png'))


# ====================================================================== region grounds
def build_region_grounds(stamps):
    regs = REG.build()
    for rid, reg in regs.items():
        lock = reg.season_lock
        seasons = SEASONS if lock is None else [SEASONS[lock]]
        if rid in ('ocean', 'crossing'):
            seasons = ['summer']
        for s in seasons:
            img, floes = PB.build_ground(s, stamps, reg.T, reg.objects, reg.scenery)
            PB.save_rgba(img, os.path.join(ART, 'ground', f'{rid}_{s}.png'))
            if floes and s == seasons[0]:
                path = os.path.join(REG.MAPS if hasattr(REG, 'MAPS') else '', f'{rid}.json')
                d = json.load(open(os.path.join(os.path.dirname(PB.MAP.OUT), 'maps', f'{rid}.json')))
                d['blocked'] = sorted({tuple(b) for b in d['blocked']} | set(floes))
                d['blocked'] = [list(b) for b in d['blocked']]
                with open(os.path.join(os.path.dirname(PB.MAP.OUT), 'maps', f'{rid}.json'), 'w') as f:
                    json.dump(d, f)
        print('ground', rid, seasons)
    for rid in ('ocean', 'crossing'):                                    # always summer art at sea
        p = os.path.join(os.path.dirname(PB.MAP.OUT), 'maps', f'{rid}.json')
        d = json.load(open(p))
        d['season_lock'] = 1
        json.dump(d, open(p, 'w'))
    return regs


# ====================================================================== telescope views + world map
def _sprite_file(kind, season, manifest):
    m = manifest.get(kind, {})
    if m.get('seasonal', True) is False:
        return os.path.join(ART, 'objects', m.get('file', kind) + '.png')
    return os.path.join(ART, 'objects', f'{kind}_{season}.png')


def compose(map_id, season, cx, cy, w, h, manifest):
    """a piece of a map as the player would see it: ground + objects"""
    d = json.load(open(os.path.join(os.path.dirname(PB.MAP.OUT), 'maps', f'{map_id}.json')))
    g = Image.open(os.path.join(ART, 'ground', f'{map_id}_{season}.png')).convert('RGBA')
    x0, y0 = cx * 16 + 8 - w // 2, cy * 16 + 8 - h // 2
    canvas = Image.new('RGBA', (w, h))
    canvas.alpha_composite(g.crop((x0, y0, x0 + w, y0 + h)))
    for o in sorted(d['objects'], key=lambda o: o['y']):
        m = manifest.get(o['kind'])
        if not m:
            continue
        sx, sy = o['x'] - m['ox'] - x0, o['y'] - m['oy'] - y0
        if sx > w or sy > h or sx + m['w'] < 0 or sy + m['h'] < 0:
            continue
        im = Image.open(_sprite_file(o['kind'], season, manifest)).convert('RGBA')
        canvas.alpha_composite(im, (int(sx), int(sy))) if sx >= 0 and sy >= 0 else canvas.paste(im, (int(sx), int(sy)), im)
    return canvas


def build_views(manifest):
    content = json.load(open(os.path.join(PB.GAME, 'data', 'content.json')))
    out = os.path.join(ART, 'views')
    os.makedirs(out, exist_ok=True)
    W, H = 256, 128
    for vid, (mid, cx, cy) in content['views'].items():
        season = 'winter' if mid == 'north' else 'summer'
        im = compose(mid, season, cx, cy, W, H, manifest)
        if vid == 'scope_summit':                                         # something long and red...
            seg = [Image.open(os.path.join(ART, 'companions', f'dragon_seg_{k}.png')).convert('RGBA') for k in 'ab']
            for i in range(26):
                a = i / 25 * 5.2 + 0.6
                px = int(W / 2 + 70 * np.cos(a) * (1 - i / 60))
                py = int(H / 2 - 30 + 34 * np.sin(a) * 0.55 - i * 0.6)
                im.alpha_composite(seg[i % 2], (px - 7, py - 7))
            head = Image.open(os.path.join(ART, 'companions', 'dragon_head.png')).convert('RGBA')
            im.alpha_composite(head, (int(W / 2 + 70 * np.cos(0.6)) - 4, int(H / 2 - 30 + 34 * np.sin(0.6) * 0.55) - 16))
        img = np.array(im)
        bay = G['BAYER']
        for y in range(H):
            for x in range(W):
                d = ((x - W / 2 + 0.5) / (W / 2 - 4)) ** 2 + ((y - H / 2 + 0.5) / (H / 2 - 3)) ** 2
                if d > 1.0:
                    img[y, x, 3] = 0
                elif d > 0.93:
                    img[y, x, :3] = C('#E0A256') if d < 0.97 else C('#6E4A35')
                elif d > 0.72 and bay[y % 4, x % 4] < (d - 0.72) * 3.5:
                    img[y, x, :3] = C('#1E1B2C')
        img[..., :3] = PB.quantize(img[..., :3])
        PB.save_rgba(img, os.path.join(out, f'{vid}.png'))


MAP_COL = {
    'home': {'~': '#2E5466', 'b': '#2E5466', 'l': '#2E5466', '!': '#4E8C95', 'O': '#1E1B2C', ',': '#4F7A3C',
             'f': '#4F7A3C', 't': '#2F4A35', 'T': '#2F4A35', '^': '#8A8496', 'v': '#4F7A3C', ':': '#A8693F',
             '.': '#E0A256', '=': '#4E8C95', '"': '#8DB054', 'R': '#1E1B2C', 'w': '#A8693F'},
}
MAP_COL['east'] = dict(MAP_COL['home'], **{',': '#8DB054', 'T': '#B8483A', ':': '#E48A73'})
MAP_COL['north'] = dict(MAP_COL['home'], **{',': '#F2E3B3', 'f': '#F2E3B3', 'T': '#4F7A3C', '^': '#8A8496',
                                             '=': '#9CD0C9', ':': '#9CD0C9', '!': '#2E5466', '.': '#F2E3B3'})


def build_worldmap():
    content = json.load(open(os.path.join(PB.GAME, 'data', 'content.json')))
    wm = content['worldmap']
    Wm, Hm = wm['size']
    maps = {'overworld': json.load(open(PB.MAP.OUT))}
    for rid in ('north', 'south', 'ocean', 'east'):
        maps[rid] = json.load(open(os.path.join(os.path.dirname(PB.MAP.OUT), 'maps', f'{rid}.json')))
    R = np.random.default_rng(3).random((Hm, Wm))
    bay = G['BAYER']

    def render(open_ocean):
        img = np.zeros((Hm, Wm, 3), np.uint8)
        img[:] = C('#1E1B2C')
        img[(R < 0.06)] = C('#3D3550')
        water = np.zeros((Hm, Wm), bool)
        for rid, (rx, ry, rw, rh) in wm['regions'].items():
            if rid == 'east' and not open_ocean:
                continue
            M = maps[rid]
            scen = 'north' if rid == 'north' else ('east' if rid == 'east' else 'home')
            for py in range(int(ry), int(np.ceil(ry + rh))):
                for px in range(int(rx), int(np.ceil(rx + rw))):
                    tx = int((px + 0.5 - rx) * M['width'] / rw)
                    ty = int((py + 0.5 - ry) * M['height'] / rh)
                    if not (0 <= tx < M['width'] and 0 <= ty < M['height']) or not (0 <= px < Wm and 0 <= py < Hm):
                        continue
                    ch = M['terrain'][ty][tx]
                    col = MAP_COL[scen].get(ch, MAP_COL[scen][','])
                    if rid == 'ocean' or ch == 'O':
                        col = '#2E5466' if (px * 5 + py * 3) % 17 else '#4E8C95'
                        if rid == 'ocean' and not open_ocean:              # the ocean fades out to the east
                            f = (px - rx) / rw
                            if bay[py % 4, px % 4] < (f - 0.18) * 1.8:
                                col = '#1E1B2C' if R[py, px] > 0.08 else '#3D3550'
                    img[py, px] = C(col)
                    water[py, px] = ch in '~!Obl='
        inside = np.zeros((Hm, Wm), bool)                                # soften the outer edges of the known world
        for rid, (rx, ry, rw, rh) in wm['regions'].items():
            if rid == 'east' and not open_ocean:
                continue
            inside[int(ry):int(np.ceil(ry + rh)), int(rx):int(np.ceil(rx + rw))] = True
        dist = np.zeros((Hm, Wm), int)
        cur = inside.copy()
        for k in range(1, 6):
            shrunk = cur & np.roll(cur, 1, 0) & np.roll(cur, -1, 0) & np.roll(cur, 1, 1) & np.roll(cur, -1, 1)
            dist[cur & ~shrunk] = k
            cur = shrunk
        dist[cur] = 9
        YY, XX = np.mgrid[0:Hm, 0:Wm]
        fade = inside & (dist < 5) & (bay[YY % 4, XX % 4] * 4.5 > dist - 0.5)
        img[fade] = C('#1E1B2C')
        snowy = np.zeros((Hm, Wm), bool)
        rx, ry, rw, rh = wm['regions']['north']
        snowy[int(ry):int(ry + rh), int(rx):int(rx + rw)] = True
        img[snowy & np.all(img == C('#8A8496'), axis=-1) & ((XX + YY) % 3 == 0)] = C('#F2E3B3')
        land = ~water & ~np.all(img == C('#1E1B2C'), axis=-1) & ~np.all(img == C('#3D3550'), axis=-1)
        edge = land & (np.roll(water, 1, 0) | np.roll(water, -1, 0) | np.roll(water, 1, 1) | np.roll(water, -1, 1))
        img[edge] = C('#F2E3B3')
        a = np.zeros((Hm, Wm, 4), np.uint8)
        a[..., :3] = img
        a[..., 3] = 255
        return a
    PB.save_rgba(render(False), os.path.join(ART, 'hud', 'worldmap_fog.png'))
    PB.save_rgba(render(True), os.path.join(ART, 'hud', 'worldmap_open.png'))
    icons = {
        'town': ['..k..', '.krk.', 'krrrk', '.kck.', '.kck.'], 'cave': ['.kkk.', 'kgggk', 'kgkgk', 'kgkgk', 'kkkkk'],
        'ferry': ['..k..', '..kk.', 'kkkkk', 'kwwwk', '.kkk.'], 'museum': ['.kkk.', 'kgggk', 'kwkwk', 'kwkwk', 'kkkkk'],
        'shrine': ['k.k.k', 'krrrk', '.kck.', 'kcccK', 'kkkkk'], 'scope': ['....k', '..kk.', '.kk..', 'k.k..', '.k.k.'],
        'dragon': ['.rr..', 'r..r.', '.rr.r', '...rr', '..rr.'],
    }
    pal = {'k': '#1E1B2C', 'K': '#1E1B2C', 'r': '#B8483A', 'c': '#F2E3B3', 'g': '#8A8496', 'w': '#F2E3B3'}
    for name, rows in icons.items():
        a = np.zeros((7, 7, 4), np.uint8)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != '.':
                    a[y + 1, x + 1] = (*C(pal[ch]), 255)
        for y in range(7):                                                # cream halo so icons read on any colour
            for x in range(7):
                if a[y, x, 3] == 0 and any(0 <= y + dy < 7 and 0 <= x + dx < 7 and a[y + dy, x + dx, 3]
                                           and tuple(a[y + dy, x + dx, :3]) != tuple(C('#F2E3B3'))
                                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    a[y, x] = (*C('#F2E3B3'), 255)
        PB.save_rgba(a, os.path.join(ART, 'hud', f'mapicon_{name}.png'))
    cur = np.zeros((9, 9, 4), np.uint8)                                   # map cursor
    for k in range(9):
        if k != 4:
            cur[4, k] = (*C('#F2E3B3'), 255)
            cur[k, 4] = (*C('#F2E3B3'), 255)
    PB.save_rgba(cur, os.path.join(ART, 'hud', 'map_cursor.png'))


def build_all(manifest, stamps):
    A2.build_room_objects  # (room kinds were registered before proto_art2 rendered them)
    build_whale()
    build_dragon()
    build_erne_carry()
    build_band_layer()
    build_region_grounds(stamps)
    build_views(manifest)
    build_worldmap()
