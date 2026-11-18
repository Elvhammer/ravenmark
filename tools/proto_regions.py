"""The regions beyond the home coast: Copperhavn (south), the snowy north, the eastern ocean, the eastern
continent, and the little sea strip used for the ferry crossing.  -> game/data/maps/<id>.json

    python3 proto_regions.py [south|north|ocean|east|crossing]   # writes all maps, prints the named one

Links between maps are edges: stepping off a map edge inside a span enters the next map (see region_lib).
World layout (tiles, home coast = 0,0):  north above home, Copperhavn below-right of home, the ocean east of home,
the eastern continent beyond the ocean.
"""
import sys
import numpy as np
from region_lib import Region


# ====================================================================== Copperhavn (south, across the water)
def south():
    r = Region('south', 96, 48, ',', seed=11)
    # sea: from the top edge (linked to the home coast's south-east sea) into a wide bay
    for y in range(48):
        for x in range(96):
            shore = 34 + 3 * np.sin(y / 3.7)
            bay_bottom = 26 + 3 * np.sin(x / 6.0) - (0 if x < 60 else (x - 60) * 0.25)
            if x > shore and y < bay_bottom:
                r.put(x, y, '~')
    r.rect(60, 0, 95, 47, '~', only=',')                                 # open sea to the east
    for y in range(48):                                                   # beaches along the bay
        for x in range(96):
            if r.get(x, y) == ',' and any(r.get(x + dx, y + dy) == '~' for dx, dy in ((1, 0), (0, -1), (1, -1))):
                r.put(x, y, '.')
    # forests and copper hills
    r.rect(0, 0, 14, 47, 'T')
    r.rect(15, 0, 30, 6, 'T', only=',')
    r.blob(16, 38, 12, 8, '^', only=',.T', seed=3)                       # the copper hill (rock)
    r.blob(16, 38, 6, 4, ',', seed=4)                                     # lookout on the hilltop
    r.line([(30, 33), (25, 35), (20, 37)], 0.6, ':')                      # hill path (a cracked rock blocks it)
    for (x, y) in [(21, 30), (40, 38), (34, 40)]:
        r.rect(x - 1, y, x + 1, y + 1, 'f', only=',')
    r.rect(15, 44, 59, 47, 'T', only=',.')
    r.rect(48, 30, 59, 47, 'T', only=',')
    # town: streets, square, piers
    r.line([(16, 10), (24, 14), (31, 18), (33, 22)], 0.7, ':', only=',.')
    r.line([(20, 24), (28, 22), (36, 21)], 0.7, ':', only=',.')
    r.rect(24, 16, 30, 21, ':', only=',')                                 # square
    r.rect(31, 16, 44, 16, 'w')                                           # ferry pier
    r.rect(33, 23, 40, 23, 'w')                                           # fishing pier
    r.line([(28, 22), (28, 26)], 0.5, ':', only=',')
    r.house('house_b', 17, 14)                                            # Gerda's house
    r.house('house_a', 22, 11)
    r.house('house_a', 31, 12)
    r.house('museum', 24, 29)                                             # the museum (door at 26,29)
    r.house('house_b', 16, 23)
    for (k, x, y) in [('barrel', 33, 17), ('barrel', 33, 18), ('crate', 35, 15), ('crate', 34, 15), ('lamp', 30, 23),
                      ('lamp', 24, 15), ('rack', 32, 25), ('logs', 19, 18), ('rock', 30, 34), ('bush', 36, 27),
                      ('cave_mouth_n', 10, 37), ('lamp', 36, 18)]:
        r.obj(k, x, y, block=((0, 0),) if k not in ('cave_mouth_n',) else ())
    r.put(10, 37, '^')
    for (x, y) in [(28, 8), (40, 28), (45, 33)]:
        r.obj('oak', x, y, oy=12)
    r.trees()
    r.edge('top', 37, 55, 'overworld', 40)
    return r


# ====================================================================== the snowy north (always winter)
def north():
    r = Region('north', 96, 64, ',', seed=21, season_lock=3)
    # mountains everywhere first, then carve the walkable land
    r.rect(0, 0, 95, 63, '^')
    # south plateau, linked to Erne Cliff on the home coast (x 10-24)
    r.rect(8, 47, 27, 63, ',')
    r.rect(4, 47, 7, 63, 'T')
    r.rect(28, 47, 33, 63, 'T')
    r.line([(17, 63), (17, 48)], 0.6, ':')
    r.rect(4, 44, 33, 46, 'R')                                            # the chasm (Bird Bell)
    r.rect(4, 44, 7, 46, 'T')
    r.rect(29, 44, 33, 46, 'T')
    # Fjelltarn: a village on a frozen tarn by the fjord
    r.blob(26, 28, 21, 15, ',', seed=5)
    r.rect(8, 37, 28, 43, ',')
    r.blob(22, 29, 6, 4, '=', seed=6)                                     # the tarn (frozen: walk on it)
    r.line([(17, 43), (17, 36), (24, 34), (34, 30), (40, 26)], 0.6, ':', only=',')
    r.line([(16, 25), (24, 21), (33, 22), (40, 26)], 0.6, ':', only=',')
    r.rect(36, 24, 42, 28, ':', only=',')                                 # the square
    # the summit lookout (telescope) north-west of the village
    r.blob(12, 9, 7, 5, ',', seed=7)
    r.line([(16, 24), (14, 18), (12, 13)], 0.6, ':')
    # the fjord: cold sea from the south-east (linked to the Rimestream) up to the whale bay in the north-east
    for y in range(64):
        for x in range(96):
            west = 46 + 5 * np.sin(y / 6.0) + (8 if y < 20 else 0)
            if x >= west and not (y < 18 and x > 62 and x < 92 and y > 2):
                r.put(x, y, '!')
    r.blob(48, 26, 3.5, 6, '!', seed=8)                                   # a cove at the village
    for y in range(18, 40):                                               # village shore = beach
        for x in range(30, 60):
            if r.get(x, y) == ',' and any(r.get(x + dx, y + dy) == '!' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                r.put(x, y, '.')
    r.rect(42, 25, 47, 25, 'w')                                           # Inga's jetty
    # Skarvsker: the whale bay hamlet in the far north-east (only reachable through the cold sea)
    r.rect(63, 3, 91, 17, '^')
    r.blob(77, 10, 11, 5, ',', seed=9)
    for y in range(4, 17):
        for x in range(64, 91):
            if r.get(x, y) == ',' and y >= 13:
                r.put(x, y, '.')
    r.rect(70, 15, 84, 17, '!')
    r.rect(76, 14, 78, 14, 'w')
    r.rect(62, 0, 95, 2, '!')
    r.rect(92, 0, 95, 20, '!')
    # forests on the plateau and around the village
    for (x, y, rx, ry) in [(9, 30, 3, 6), (33, 38, 3, 2), (6, 22, 2, 3), (44, 40, 2, 2)]:
        r.blob(x, y, rx, ry, 'T', only=',', seed=x)
    # houses, the seal hut, decor
    r.house('house_a', 27, 22)
    r.house('house_b', 33, 18)
    r.house('cabin', 22, 36)
    r.house('cabin', 40, 33)
    r.house('cabin', 72, 9)                                               # Skarvsker
    for (k, x, y) in [('rack', 42, 24), ('barrel', 43, 30), ('lamp', 38, 23), ('lamp', 36, 29), ('logs', 31, 27),
                      ('boat', 46, 27), ('rack', 80, 9), ('lamp', 76, 12), ('whalebone', 82, 12),
                      ('standing_stone', 11, 7), ('rock_big', 7, 58), ('rock', 22, 55), ('rock', 26, 31)]:
        r.obj(k, x, y, oy=8 if k == 'boat' else 14)
    r.trees(kinds=(('pine', 0.9), ('oak', 0.1)))
    r.edge('bottom', 10, 24, 'overworld', 0)
    r.edge('bottom', 76, 95, 'overworld', 0)
    return r


# ====================================================================== the eastern ocean (whale only)
def ocean():
    r = Region('ocean', 300, 40, 'O', seed=31)
    rr = np.random.default_rng(5)
    for _ in range(14):                                                   # skerries
        x, y = int(rr.integers(20, 280)), int(rr.integers(3, 37))
        r.blob(x, y, rr.uniform(1, 2.5), rr.uniform(1, 2), '^', seed=int(x))
    r.blob(150, 20, 6, 4, '.', seed=2)                                    # the Halfway Rock: a lone islet
    r.blob(150, 20, 3, 2, ',', seed=3)
    r.obj('beacon', 150, 19)
    r.obj('wreck', 214, 12, block=())
    for (x, y) in [(147, 21), (153, 19)]:
        r.obj('puffin', x, y, block=())
    r.edge('left', 5, 33, 'overworld', 9)
    r.edge('right', 0, 39, 'east', 10)
    return r


# ====================================================================== the eastern continent
def east():
    r = Region('east', 96, 64, ',', seed=41, scenery='east')
    # the west coast: ocean, then harbour water, beach, Whitborg
    for y in range(64):
        for x in range(96):
            coast = 12 + 3 * np.sin(y / 5.0)
            if x < coast - 6:
                r.put(x, y, 'O')
            elif x < coast:
                r.put(x, y, '~')
    for y in range(64):
        for x in range(96):
            if r.get(x, y) == ',' and r.get(x - 1, y) == '~':
                r.put(x, y, '.')
                r.put(x + 1, y, '.')
    r.rect(0, 0, 95, 4, 'T', only=',.')
    r.rect(0, 56, 95, 63, 'T', only=',.')
    # Whitborg
    r.rect(8, 24, 13, 24, 'w')                                            # harbour piers
    r.rect(9, 34, 13, 34, 'w')
    r.line([(14, 24), (22, 26), (30, 28), (40, 28)], 0.7, ':', only=',.')
    r.rect(20, 28, 27, 33, ':', only=',.')                                # market square
    r.line([(14, 34), (21, 32)], 0.6, ':', only=',.')
    for (k, x, y) in [('house_e', 17, 22), ('house_e', 24, 22), ('house_e', 29, 36), ('house_e', 16, 40),
                      ('house_e', 31, 24)]:
        r.house(k, x, y)
    for (k, x, y) in [('stone_lantern', 19, 27), ('stone_lantern', 28, 27), ('stone_lantern', 19, 34),
                      ('stone_lantern', 28, 34), ('blossom', 15, 29), ('blossom', 33, 31), ('blossom', 22, 38),
                      ('crate', 14, 25), ('barrel', 15, 25), ('boat', 9, 27), ('boat', 10, 37), ('rack', 25, 35)]:
        r.obj(k, x, y, oy=8 if k == 'boat' else (12 if k == 'blossom' else 14))
    # inland: blossom woods, a river (otter), a fallen tree (axe), the mountain (cracked rock), a chasm (bird)
    r.line([(40, 28), (52, 30), (56, 36), (66, 40)], 0.7, ':', only=',')
    r.line([(46, 5), (47, 18), (45, 32), (48, 45), (46, 56)], 1.3, '=')   # the Jade River: no bridge
    r.rect(34, 8, 43, 20, 'T', only=',')
    r.rect(34, 40, 60, 55, 'T', only=',')
    r.rect(60, 5, 95, 36, '^', only=',T')                                 # Brandfell
    r.blob(78, 12, 9, 6, ',', seed=12)                                    # the shrine terrace
    r.rect(66, 24, 72, 34, ',')                                           # the lower terrace
    r.rect(69, 35, 69, 36, ':')                                           # a 1-wide way up (a fallen tree lies here)
    r.line([(66, 40), (69, 37)], 0.6, ':')
    r.line([(69, 34), (69, 27)], 0.6, ':')
    r.rect(66, 22, 74, 23, 'R')                                           # the chasm below the shrine
    r.rect(62, 22, 65, 23, '^')
    r.rect(75, 22, 80, 23, '^')
    r.rect(68, 18, 71, 21, ',')
    for (x, y) in [(70, 17), (70, 16), (71, 16), (71, 15), (72, 15), (72, 14)]:   # 1-wide (a cracked rock blocks it)
        r.put(x, y, ':')
    for (x, y, rx, ry) in [(80, 44, 8, 6), (90, 36, 5, 5)]:
        r.blob(x, y, rx, ry, 'T', only=',', seed=x)
    r.obj('shrine', 78, 10, block=[(dx, dy) for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0)])
    for (x, y) in [(74, 13), (82, 13)]:
        r.obj('stone_lantern', x, y)
    for (x, y) in [(52, 26), (57, 33), (62, 36), (40, 34), (73, 15), (84, 15)]:
        r.obj('blossom', x, y, oy=12)
    r.trees(kinds=(('blossom', 0.45), ('pine', 0.4), ('oak', 0.15)))
    r.edge('left', 10, 49, 'ocean', -10)
    return r


# ====================================================================== the ferry crossing (cutscene only)
def crossing():
    r = Region('crossing', 44, 12, '~', seed=51)
    r.blob(14, 2, 3, 1.5, '^', seed=1)
    r.blob(30, 10, 2.5, 1.5, '^', seed=2)
    return r


REGIONS = {'south': south, 'north': north, 'ocean': ocean, 'east': east, 'crossing': crossing}


def build():
    out = {}
    for rid, fn in REGIONS.items():
        reg = fn()
        reg.write()
        out[rid] = reg
    return out


if __name__ == '__main__':
    regs = build()
    want = sys.argv[1] if len(sys.argv) > 1 else None
    for rid, reg in regs.items():
        print(rid, reg.W, 'x', reg.H, len(reg.objects), 'objects')
        if rid == want:
            print(reg.ascii())
