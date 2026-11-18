"""Proves the traversal-item order: which tools can be reached with which tools in hand.

    python3 check_progression.py        # prints the stages, exits 1 if the order is broken

Flood-fills every map (walking, swimming by mount, ledges, doors, map edges, erne perches, obstacles that need
a tool) with a growing set of items. Seasons and the tide are assumed favourable (worst case: frozen rivers
and the dawn sandbar count as walkable), so a pass here means no season trick skips a stage.
"""
import json
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), 'game', 'data')
C = json.load(open(os.path.join(DATA, 'content.json')))
MAPS = {'overworld': json.load(open(os.path.join(DATA, 'world.json')))}
for f in os.listdir(os.path.join(DATA, 'maps')):
    MAPS[f[:-5]] = json.load(open(os.path.join(DATA, 'maps', f)))
DIRS = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
GIVERS = {'otter_stick': 'edvin', 'pickaxe': 'gerda', 'seal_flute': 'inga', 'whale_horn': 'halla',
          'dragon_band': 'lan', 'ferry_pass': 'nils'}
BASE = {'lantern', 'cellar_key'}            # Ole's lantern (lamp oil from the store) and Marit's key: always available


def tile(m, x, y):
    M = MAPS[m]
    if 0 <= x < M['width'] and 0 <= y < M['height']:
        return M['terrain'][y][x]
    return None


def static_block(m):
    out = {tuple(b) for b in MAPS[m]['blocked']}
    for key in ('chests', 'signs'):
        for e in C[key]:
            if e['map'] == m:
                out.add((e['x'], e['y']))
    for n in C['npcs']:
        if n.get('map') == m:
            out.add((n['x'], n['y']))
    for p in C['pickups'] + C['perches'] + C['telescopes']:
        if p['map'] == m and p.get('kind') != 'sparkle':
            out.add((p['x'], p['y']))
    return out


BLOCK = {m: static_block(m) for m in MAPS}


def passable(m, x, y, items):
    """'walk', 'swim' or None"""
    c = tile(m, x, y)
    if c is None or (x, y) in BLOCK[m]:
        return None
    for o in C['obstacles']:
        if o['map'] == m and (o['x'], o['y']) == (x, y) and o['needs'] not in items:
            return None
    outdoor = MAPS[m].get('kind', 'outdoor') == 'outdoor' or m == 'overworld'
    if not outdoor:
        if c != '.':
            return None
        M = MAPS[m]
        if M.get('dark') and 'lantern' not in items:
            if not any((x - z[0]) ** 2 + (y - z[1]) ** 2 <= z[2] ** 2 for z in M['lit_zones']):
                return None
        return 'walk'
    if c in ',:.wfltv"=':
        return 'walk' if c != 'v' else 'ledge'               # frozen rivers / reeds in winter, sandbar at dawn
    if c == '~' and ({'otter_stick', 'whale_horn'} & items):
        return 'swim'
    if c == '!' and 'seal_flute' in items:
        return 'swim'
    if c == 'O' and 'whale_horn' in items:
        return 'swim'
    return None


def reach(items):
    start = ('overworld', 55, 22)
    seen = {start}
    q = deque([start])
    while q:
        m, x, y = q.popleft()
        nxt = []
        for d, (dx, dy) in DIRS.items():
            tx, ty = x + dx, y + dy
            for w in C['warps']:                               # doors and stairs
                if w['map'] == m and (w['x'], w['y']) == (tx, ty) and DIRS[w['dir']] == (dx, dy) and 'to' in w:
                    if w.get('needs') is None or w['needs'] in items:
                        nxt.append((w['to'], w['tx'], w['ty']))
            if tile(m, tx, ty) is None:                        # map edges
                side = 'top' if ty < 0 else 'bottom' if ty >= MAPS[m]['height'] else 'left' if tx < 0 else 'right'
                for e in MAPS[m].get('edges', []):
                    c = tx if side in ('top', 'bottom') else ty
                    if e['side'] == side and e['a'] <= c <= e['b']:
                        T = MAPS[e['to']]
                        nt = {'top': (tx + e['shift'], T['height'] - 1), 'bottom': (tx + e['shift'], 0),
                              'left': (T['width'] - 1, ty + e['shift']), 'right': (0, ty + e['shift'])}[side]
                        if passable(e['to'], *nt, items) in ('walk', 'swim'):
                            nxt.append((e['to'],) + nt)
                continue
            p = passable(m, tx, ty, items)
            if p in ('walk', 'swim'):
                nxt.append((m, tx, ty))
            elif p == 'ledge' and dy == 1 and passable(m, tx, ty + 1, items) == 'walk':
                nxt.append((m, tx, ty + 1))
            for pr in C['perches']:                            # the erne
                if 'bird_bell' in items and pr['map'] == m and (pr['x'], pr['y']) == (tx, ty):
                    nxt.append((m, pr['land'][0], pr['land'][1]))
        for n in nxt:
            if n not in seen:
                seen.add(n)
                q.append(n)
    return seen


def near(seen, m, x, y, r=1):
    return any((m, x + dx, y + dy) in seen for dx in range(-r, r + 1) for dy in range(-r, r + 1) if abs(dx) + abs(dy) <= r) \
        or any((m, x + dx, y) in seen for dx in (-2, 2)) or any((m, x, y + dy) in seen for dy in (-2, 2))


def obtainable(seen, items):
    got = set()
    for c in C['chests']:
        if 'item' in c and near(seen, c['map'], c['x'], c['y']):
            got.add(c['item'])
    for p in C['pickups']:
        if near(seen, p['map'], p['x'], p['y']):
            got.add(p['item'])
    for it, npc in GIVERS.items():
        n = next(n for n in C['npcs'] if n['id'] == npc)
        if near(seen, n['map'], n['x'], n['y']):
            got.add(it)
    return got - items


def main():
    order = C['progression']
    items = set(BASE)
    stage = 0
    ok = True
    while True:
        seen = reach(items)
        new = obtainable(seen, items)
        prog = [i for i in order if i in new]
        maps = sorted({s[0] for s in seen})
        print(f'stage {stage}: holding {sorted(i for i in items if i in order) or "nothing"}')
        print(f'   reachable maps: {", ".join(maps)} ({len(seen)} tiles)')
        if not new:
            break
        print(f'   can now find: {sorted(new)}')
        want = next((i for i in order if i not in items), None)
        if prog and prog != [want]:
            print(f'   ORDER BROKEN: expected only {want}, found {prog}')
            ok = False
        items |= new
        stage += 1
    missing = [i for i in order if i not in items]
    if missing:
        print('NEVER REACHABLE:', missing)
        ok = False
    print('PROGRESSION OK' if ok else 'PROGRESSION BROKEN')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
