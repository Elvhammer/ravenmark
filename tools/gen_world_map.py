"""Ravenmark world map data + coarse ASCII renderer.

1 map cell = 8 x 16 tiles. Map is 100 x 25 cells = 800 x 400 tiles (2:1).
Run directly to print the ASCII map; `--sizes` also prints route sizes.
render_world_map.py imports this module to draw the pixel-art version.
"""
import sys

W, H = 100, 25

# x < COAST[y] is mainland
COAST = [47, 45, 43, 44, 44, 44, 47, 50, 49, 49, 49, 50, 50, 49, 48,
         47, 46, 44, 42, 41, 36, 31, 28, 26, 25]

TOWNS = {  # code: (x, y, name)
    'A': (24, 18, 'Kvernby'), 'B': (15, 15, 'Stiltvik'), 'C': (10, 11, 'Wheelfoss'),
    'D': (7, 18, 'Redskar'), 'E': (14, 21, 'Saltbrun'), 'F': (12, 5, 'Fjelltarn'),
    'G': (27, 5, 'Greinholt'), 'H': (42, 5, 'Keelvik'), 'I': (47, 9, 'Copperhavn'),
    'J': (38, 11, 'Bruby'), 'K': (38, 19, 'Gullsand'), 'L': (58, 16, 'Skarvsker'),
    'M': (70, 5, 'Bruholm'), 'N': (80, 19, 'Brandfell'), 'O': (95, 11, 'Whitborg'),
}

LAKE = {9: (20, 28), 10: (18, 30), 11: (17, 31), 12: (17, 32), 13: (17, 31), 14: (16, 29), 15: (17, 18)}
REEDS = [(15, 12), (16, 12), (15, 13), (16, 13), (15, 14), (19, 15),
         (22, 11), (23, 11), (25, 11), (26, 11), (22, 12), (23, 12), (24, 12), (25, 12), (26, 12),
         (23, 10), (24, 10), (25, 10)]
TARN = [(x, 3) for x in range(10, 15)]
MARSH = [(x, y) for y in (7, 8) for x in range(17, 26)]           # Candlefen

# Rivers as ordered cell lists (source -> mouth)
RIVERS = {
    'the Fossa': [(9, y) for y in range(4, 11)] + [(x, 11) for x in range(12, 17)],
    'the Lauva': [(15, 1)] + [(x, 2) for x in range(16, 31)] + [(x, 3) for x in range(31, 43)] + [(43, 4)],
    'Lykt Brook': [(27, 6), (27, 7), (26, 8)],
    'the Breia': [(33, 12), (34, 12), (35, 11), (36, 11), (40, 11), (41, 11), (42, 11),
               (43, 10), (44, 10), (45, 10), (46, 10), (47, 10), (48, 10)],
}
# extra end-points so drawn rivers join their lake / tarn / sea
RIVER_ENDS = {
    'the Fossa': ((10, 3), (17, 11)), 'the Lauva': ((14, 0), (44, 4)),
    'Lykt Brook': ((27, 5), (26, 9)), 'the Breia': ((32, 12), (49, 10)),
}

WINTER_SPOTS = {  # cell: name (only reachable when frozen)
    (24, 11): 'Klokkeholm', (12, 3): 'Tarnholm', (8, 8): 'Icefoss Glen', (36, 3): 'Damholm',
}

ROUTES = {  # land routes, ordered cells
    1: [(22, 18), (21, 18), (20, 17), (19, 17), (18, 17), (17, 16), (16, 16)],
    2: [(13, 14), (13, 13), (12, 12)],
    3: [(12, 10), (12, 9), (12, 8)],
    4: [(12, 7), (12, 6)],
    5: [(14, 5), (15, 4), (16, 4), (17, 4), (18, 4)],
    6: [(19, 4), (20, 4), (21, 5), (22, 5), (23, 5), (24, 5), (25, 5)],
    7: [(29, 6), (30, 6), (31, 7), (32, 7)],
    8: [(33, 8), (34, 8), (35, 9), (36, 10)],
    9: [(38, 12), (38, 13), (39, 14), (39, 15)],
    10: [(39, 16), (39, 17), (38, 18)],
    11: [(36, 19), (35, 19), (34, 19), (33, 19), (32, 19), (31, 19), (30, 19), (29, 19),
         (28, 19), (27, 19), (26, 18)],
    12: [(13, 16), (12, 16), (11, 17), (10, 17), (9, 18)],
    13: [(8, 19), (9, 20), (10, 20), (11, 21), (12, 21)],
    14: [(16, 21), (17, 20), (18, 20), (19, 20), (20, 19), (21, 19), (22, 19)],
    15: [(10, 5), (9, 5), (8, 4), (7, 3), (6, 2)],
    16: [(29, 4), (30, 4), (31, 4), (32, 4), (33, 4), (34, 4), (35, 4), (36, 4), (37, 4),
         (38, 4), (39, 4), (40, 4)],
    17: [(44, 6), (45, 7), (46, 7), (46, 8)],
    18: [(40, 10), (41, 9), (42, 9), (43, 9), (44, 9), (45, 9)],
}
ISLAND_ROUTES = {
    27: [(82, 21), (83, 21)],
    30: [(86, 11), (87, 11), (88, 11), (89, 11), (90, 11), (91, 11), (92, 11)],
}
WINTER_ROUTES = {
    19: [(9, 7), (9, 6), (9, 5), (9, 4)],
    21: [(13, 9), (14, 8), (15, 8), (16, 8), (17, 8), (18, 8), (19, 8), (20, 8), (21, 8),
         (22, 8), (23, 8), (24, 8), (25, 7), (26, 6)],
}
LANES = {  # sailing lanes
    22: [(49, 11), (50, 12), (51, 12), (52, 13), (53, 13), (54, 14), (55, 14)],
    23: [(41, 19), (42, 19), (43, 18), (44, 18), (45, 18), (46, 18), (47, 18), (48, 18),
         (49, 18), (50, 17), (51, 17), (52, 17), (53, 17), (54, 17), (55, 17)],
    24: [(44, 3), (45, 3), (46, 2), (47, 2), (48, 2), (49, 2), (50, 2), (51, 2), (52, 2),
         (53, 2), (54, 2), (55, 2), (56, 2), (57, 2), (58, 2), (59, 2), (60, 2), (61, 3),
         (62, 3), (63, 3), (64, 4), (65, 4), (66, 5), (67, 5), (68, 5)],
    25: [(50, 9), (51, 8), (52, 8), (53, 8), (54, 8), (55, 8), (56, 8), (57, 8), (58, 8),
         (59, 8), (60, 8), (61, 7), (62, 7), (63, 7), (64, 6), (65, 6), (66, 6)],
    26: [(61, 17), (62, 17), (63, 17), (64, 18), (65, 18), (66, 18), (67, 18), (68, 18),
         (69, 18), (70, 18), (71, 19), (72, 19), (73, 19), (74, 19)],
    28: [(72, 5), (73, 5), (74, 5), (75, 5), (76, 6), (77, 6), (78, 7), (79, 7), (80, 8),
         (81, 8), (82, 9), (83, 9), (84, 10), (84, 11)],
    29: [(84, 19), (85, 18), (85, 17), (85, 16), (85, 15), (85, 14), (84, 13), (84, 12)],
}
LABELS = {  # route number positions
    1: (19, 17), 2: (13, 13), 3: (12, 9), 4: (12, 7), 5: (16, 4), 6: (22, 5), 7: (30, 6),
    8: (34, 8), 9: (38, 13), 10: (39, 16), 11: (31, 19), 12: (11, 17), 13: (9, 20),
    14: (18, 20), 15: (6, 2), 16: (33, 4), 17: (44, 6), 18: (42, 9), 19: (9, 6),
    20: (20, 13), 21: (19, 8), 22: (52, 13), 23: (46, 18), 24: (52, 2), 25: (56, 8),
    26: (67, 18), 27: (82, 21), 28: (77, 6), 29: (85, 16), 30: (88, 11),
}

ISLETS = [(52, 6), (54, 9), (55, 6), (57, 10), (59, 7), (60, 9), (62, 6), (63, 10), (65, 8),
          (53, 11), (61, 12), (66, 11), (58, 12),                                  # Scatterlings
          (66, 3), (67, 4), (68, 2), (72, 3), (73, 4), (74, 6), (67, 6), (72, 7), (75, 3),
          (68, 7), (71, 2),                                                        # Bridgeholm
          (51, 20), (66, 22), (70, 14), (74, 12), (62, 23), (86, 2), (90, 22), (47, 22),
          (78, 9), (81, 7), (55, 22)]                                              # lone islets
GULLROCK = [(56, 15), (57, 15), (56, 16), (60, 16), (56, 17), (57, 17), (58, 17), (59, 17)]
SEA_ARCH = [(56, 1), (57, 1)]
EMBERKEY = {17: (78, 81), 18: (76, 83), 19: (75, 84), 20: (75, 84), 21: (76, 83), 22: (78, 81)}
EMBER_PEAK = [(80, 18), (81, 18), (81, 19), (82, 19), (81, 20), (82, 20)]
VELLMARCH_ISLE = {5: (92, 99), 6: (89, 99), 7: (88, 99), 8: (87, 99), 9: (86, 99), 10: (86, 99),
                  11: (85, 99), 12: (86, 99), 13: (86, 99), 14: (87, 99), 15: (88, 99),
                  16: (90, 99), 17: (93, 99)}
VELLMARCH_CLIFFS = [(92, 5), (93, 5), (89, 6), (88, 7), (88, 15), (90, 16), (93, 17), (94, 17)]
SPIRES = [(81, 9), (83, 8), (82, 10)]
MAELSTROM = (88, 20)

HIGHTARN_VALLEY = [(10, 5), (11, 4), (12, 4), (13, 4), (14, 4), (11, 6), (12, 6), (13, 6),
                   (10, 6), (14, 6), (15, 5), (16, 5)]
CANYON_WALLS = [(5, 17), (6, 17), (8, 17), (5, 19), (6, 19), (7, 20), (8, 21), (9, 21),
                (10, 22), (6, 20), (7, 21), (11, 22), (9, 19), (10, 19)]
GANNET_CLIFFS = [(48, 7), (49, 7), (47, 6)]


def is_land(x, y):
    return x < COAST[y]


def terrain(rivers=True, islets=True):
    """Terrain-only grid (no routes, lanes, labels or towns)."""
    g = [['~'] * W for _ in range(H)]

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = c

    for y in range(H):
        for x in range(W):
            if not is_land(x, y):
                continue
            if (x <= 17 and y <= 9) or (y <= 1 and x <= 21) or (x <= 2 and y <= 14):
                c = '^'                                   # NW highlands
            elif 18 <= x <= 41 and y <= 7:
                c = 'T'                                   # north forest
            elif x >= 33 and 6 <= y <= 17 and x < COAST[y] - 1:
                c = 'T'                                   # east forest
            elif (x <= 12 and y >= 14) or (x <= 19 and y >= 19) or (x <= 25 and y >= 21) \
                    or (x <= 21 and y >= 20):
                c = ':'                                   # dry south-west
            else:
                c = ','
            put(x, y, c)
    for p in HIGHTARN_VALLEY:
        put(*p, ',')
    for p in CANYON_WALLS:
        put(*p, '^')
    for p in GANNET_CLIFFS:
        if is_land(*p):
            put(*p, '^')
    for y, (a, b) in LAKE.items():
        for x in range(a, b + 1):
            put(x, y, '=')
    for p in REEDS:
        put(*p, '"')
    put(24, 11, '*')
    for p in TARN:
        put(*p, '=')
    put(12, 3, '*')
    if rivers:
        for name in ('the Fossa', 'the Lauva', 'Lykt Brook'):
            for p in RIVERS[name]:
                put(*p, '=')
    put(8, 8, '*')
    if rivers:
        put(36, 3, '*')
    for p in MARSH:
        put(*p, '"')
    if rivers:
        for p in RIVERS['the Breia']:
            put(*p, '=')
    return g, put


def ascii_map():
    g, put = terrain()
    for cells in ROUTES.values():
        for p in cells:
            put(*p, '#')
    for cells in WINTER_ROUTES.values():
        for p in cells:
            put(*p, '*')
    for p in GULLROCK:
        put(*p, '^')
    for p in ISLETS:
        put(*p, 'o')
    for p in SEA_ARCH:
        put(*p, '^')
    for y, (a, b) in EMBERKEY.items():
        for x in range(a, b + 1):
            put(x, y, '^' if (x, y) in EMBER_PEAK else ':')
    for y, (a, b) in VELLMARCH_ISLE.items():
        for x in range(a, b + 1):
            put(x, y, ',')
    for p in VELLMARCH_CLIFFS:
        put(*p, '^')
    for p in SPIRES:
        put(*p, '|')
    put(*MAELSTROM, '@')
    for cells in LANES.values():
        for (x, y) in cells:
            if g[y][x] == '~':
                put(x, y, '.')
    for cells in ISLAND_ROUTES.values():
        for p in cells:
            put(*p, '#')
    for rid, (x, y) in LABELS.items():
        for i, ch in enumerate(str(rid)):
            put(x + i, y, ch)
    for k, (x, y, _) in TOWNS.items():
        put(x - 1, y, '['); put(x, y, k); put(x + 1, y, ']')
    return '\n'.join(''.join(r) for r in g)


if __name__ == '__main__':
    print(ascii_map())
    if '--sizes' in sys.argv:
        allr = {**ROUTES, **WINTER_ROUTES, **LANES}
        for rid in sorted(allr):
            cs = allr[rid]
            xs = [c[0] for c in cs]; ys = [c[1] for c in cs]
            dx = (max(xs) - min(xs) + 1) * 8; dy = (max(ys) - min(ys) + 1) * 16
            sw, sh = (40, 22.5) if rid in LANES else (20, 11.25)
            print(rid, f'{dx / sw:.1f} x {dy / sh:.1f} screens')
