"""Repaint the parts of the tutorial world whose tilesets were never committed
(Buildings, Roofs, Plants, Extras) using new generated house art and existing tiles."""
import re, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
import houseart

ROOT = '/home/claude/game/assets/world'
MAP = ROOT + '/worlds/TutorialWorld - Copy.tmx'
W = 64
MISSING = {'Buildings.tsx', 'Roofs.tsx', 'Plants.tsx', 'Extras.tsx'}
GROUND_LAYERS = {'Background-1', 'TheGround'}

s = open(MAP).read()
tilesets = [(int(a), b) for a, b in re.findall(r'<tileset firstgid="(\d+)" source="../asset/data/([^"]+)"', s)]
def setname(g):
    g &= 0x1fffffff
    return [n for f, n in tilesets if f <= g][-1] if g else None
FIRST = dict((n, f) for f, n in tilesets)

# ---- new art tileset -------------------------------------------------------
HOUSES = {
    # name: (x, y, w, roof_rows, wall_rows, door_col, windows, palette, wall, chimney, seed)
    'wrynn': (36, 19, 15, 7, 4, 7, [2, 4, 10, 12], 'red', 'plaster', 12, 4),
    'lyra':  (8, 21, 10, 6, 4, 4, [1, 7], 'slate', 'wood', 2, 7),
}
pieces = {}
for name, (hx, hy, w, rr, wr, dc, win, pal, ws, ch, seed) in HOUSES.items():
    pieces[name] = houseart.draw_house(w, rr, wr, dc, win, pal, ws, ch, seed)
pieces['stall'] = houseart.draw_stall_counter(2, seed=5)

COLS = 28
sheet = Image.new('RGBA', (COLS * 16, 11 * 16), (0, 0, 0, 0))
origin = {}
cx = 0
for name in ['wrynn', 'lyra', 'stall']:
    img = pieces[name]
    sheet.alpha_composite(img, (cx * 16, 0))
    origin[name] = (cx, 0)
    cx += img.width // 16
os.makedirs(ROOT + '/asset/source/generated', exist_ok=True)
sheet.save(ROOT + '/asset/source/generated/OasisBuildings.png')
open(ROOT + '/asset/data/OasisBuildings.tsx', 'w').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.11.0" name="OasisBuildings" tilewidth="16" tileheight="16" tilecount="{COLS * 11}" columns="{COLS}">
 <image source="../source/generated/OasisBuildings.png" width="{COLS * 16}" height="{11 * 16}"/>
</tileset>
''')
NEW_FIRST = max(f for f, _ in tilesets) + 288  # 9.tsx is last with 288 tiles
assert tilesets[-1][1] == '9.tsx'
def art(name, c, r):
    ox, oy = origin[name]
    return NEW_FIRST + (oy + r) * COLS + (ox + c)

# ---- parse layers ----------------------------------------------------------
layer_re = re.compile(r'(<layer [^>]*name="([^"]+)"[^>]*>\s*<data encoding="csv">)(.*?)(</data>)', re.S)
layers = []
for m in layer_re.finditer(s):
    layers.append([m.group(2), [int(v) for v in m.group(3).replace('\n', '').split(',') if v.strip()]])
L = dict((n, g) for n, g in layers)

# collect plant/extra positions before clearing
plants, extras = set(), set()
for name, g in layers:
    for k, v in enumerate(g):
        n = setname(v)
        if n == 'Plants.tsx': plants.add((k % W, k // W))
        if n == 'Extras.tsx': extras.add((k % W, k // W))

# clear every tile from missing tilesets
for name, g in layers:
    for k, v in enumerate(g):
        if setname(v) in MISSING: g[k] = 0

# clear house footprints (above-ground layers) and keep plants out of them
house_cells = set()
for name, (hx, hy, w, rr, wr, *_rest) in HOUSES.items():
    for y in range(hy, hy + rr + wr):
        for x in range(hx, hx + w):
            house_cells.add((x, y))
for name, g in layers:
    if name in GROUND_LAYERS: continue
    for (x, y) in house_cells: g[y * W + x] = 0
plants -= house_cells
extras -= house_cells

# ground cells left empty after clearing get the ground tile from just below
for k in range(W * W):
    if all(L[n][k] == 0 for n in GROUND_LAYERS):
        for dy in (1, 2, -1):
            j = k + dy * W
            if 0 <= j < W * W and L['TheGround'][j]:
                L['TheGround'][k] = L['TheGround'][j]; break

new = [0] * (W * W)
def put(x, y, gid):
    if 0 <= x < W and 0 <= y < W: new[y * W + x] = gid

for name, (hx, hy, w, rr, wr, *_rest) in HOUSES.items():
    for r in range(rr + wr):
        for c in range(w):
            put(hx + c, hy + r, art(name, c, r))

# ---- plants: refill clusters with trees and crops from the crops sheet (3.tsx) --
T3 = FIRST['3.tsx']
def t3(c, r): return T3 + r * 30 + c
def stamp(x, y, c0, r0, w, h, layer='Middle'):
    for r in range(h):
        for c in range(w):
            if layer == 'new': put(x + c, y + r, t3(c0 + c, r0 + r))
            else: L[layer][(y + r) * W + (x + c)] = t3(c0 + c, r0 + r)

def clusters(cells):
    seen, out = set(), []
    for p in sorted(cells):
        if p in seen: continue
        st, comp = [p], []
        while st:
            q = st.pop()
            if q in seen or q not in cells: continue
            seen.add(q); comp.append(q)
            x, y = q; st += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        out.append(comp)
    return out

placed = []
for comp in clusters(plants):
    xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
    x0, y0, w, h = min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    if y0 >= 37 and len(comp) < 4:  # stray singles near the plots: wildflowers
        for (x, y) in comp:
            L['Background3'][y * W + x] = t3(6, 0) if (x + y) % 2 else t3(7, 1)
        placed.append(('flowers', x0, y0, len(comp))); continue
    if y0 >= 37:  # farm plots: carrots on each former crop tile
        for (x, y) in comp:
            L['Background3'][y * W + x] = t3(26 + (x % 2), 2 + (y % 2))
        placed.append(('crops', x0, y0, w, h)); continue
    if w >= 4 and h >= 4:
        stamp(x0, y0, 0, 0, 4, 4); placed.append(('big tree', x0, y0))
    elif w == 2 and h >= 4:
        stamp(x0, y0 + h - 4, 10, 0, 2, 4); placed.append(('tall tree', x0, y0))
    elif w >= 2 and h >= 2:
        stamp(x0, y0 + h - 2, 4, 2, 2, 2); placed.append(('small tree', x0, y0))
    else:
        for (x, y) in comp: L['Middle'][y * W + x] = t3(24, 0) if (x + y) % 2 else t3(26, 0)
        placed.append(('sprouts', x0, y0, len(comp)))

# ---- extras: market stall counters / rocks --------------------------------
for comp in clusters(extras):
    xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
    x0, y0, w, h = min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    if y0 < 20:  # under the market awnings
        for r in range(2):
            for c in range(2): put(x0 + c, y0 + r, art('stall', c, r))
        placed.append(('stall counter', x0, y0))
    else:
        for i in range(0, w - 1, 2):
            stamp(x0 + i, y0, 18, 0, 2, 2); placed.append(('rock', x0 + i, y0))

for p in placed: print(p)

# ---- portal to the Mycelic Grove in the east meadow -------------------------
MYC_FIRST = NEW_FIRST + COLS * 11
PX, PY = 44, 41
for r in range(3):
    for c in range(2):
        put(PX + c, PY + r, MYC_FIRST + r * 12 + 9 + c)     # MyceliaExtras portal tiles
        for name, g in layers:
            if name not in GROUND_LAYERS: g[(PY + r) * W + PX + c] = 0
placed.append(('portal', PX, PY))

# ---- write back ------------------------------------------------------------
def csv(g):
    return '\n' + '\n'.join(','.join(str(v) for v in g[r * W:(r + 1) * W]) + (',' if r < W - 1 else '') for r in range(W)) + '\n'
idx = [0]
def repl(m):
    name = m.group(2); g = L[name]
    return m.group(1) + csv(g) + m.group(4)
s = layer_re.sub(repl, s)

# drop the missing tilesets from the map, add the new one
for n in MISSING:
    s = re.sub(r'\s*<tileset firstgid="\d+" source="../asset/data/%s"/>' % re.escape(n), '', s)
s = s.replace('<tileset firstgid="%d" source="../asset/data/9.tsx"/>' % FIRST['9.tsx'],
              '<tileset firstgid="%d" source="../asset/data/9.tsx"/>\n <tileset firstgid="%d" source="../asset/data/OasisBuildings.tsx"/>\n <tileset firstgid="%d" source="../asset/data/MyceliaExtras.tsx"/>' % (FIRST['9.tsx'], NEW_FIRST, MYC_FIRST))

# new Buildings layer right after Background3
nid = int(re.search(r'nextlayerid="(\d+)"', s).group(1))
s = s.replace('nextlayerid="%d"' % nid, 'nextlayerid="%d"' % (nid + 1), 1)
layer_xml = ' <layer id="%d" name="Buildings" width="64" height="64">\n  <data encoding="csv">%s</data>\n </layer>\n' % (nid, csv(new))
pos = s.index('<layer id="6" name="Middle"')
s = s[:pos] + layer_xml.lstrip() + ' ' + s[pos:]

# collision for the small house (the original had none)
oid = int(re.search(r'nextobjectid="(\d+)"', s).group(1))
s = s.replace('nextobjectid="%d"' % oid, 'nextobjectid="%d"' % (oid + 1), 1)
hx, hy, w, rr, wr = HOUSES['lyra'][:5]
rect = '  <object id="%d" x="%d" y="%d" width="%d" height="%d"/>\n' % (oid, hx * 16 + 2, hy * 16 + 4, w * 16 - 4, (rr + wr) * 16 - 22)
m = re.search(r'<objectgroup [^>]*name="Collision"[^>]*>\n', s)
s = s[:m.end()] + rect + s[m.end():]

# portal collision + interaction object
oid += 1
portal_coll = '  <object id="%d" x="%d" y="%d" width="%d" height="%d"/>\n' % (oid, PX * 16 + 2, (PY + 1) * 16, 28, 32)
m = re.search(r'<objectgroup [^>]*name="Collision"[^>]*>\n', s)
s = s[:m.end()] + portal_coll + s[m.end():]
oid += 1
portal_obj = ('  <object id="%d" name="portal" x="%d" y="%d" width="32" height="16">\n   <properties>\n'
              '    <property name="interactable" type="bool" value="true"/>\n'
              '    <property name="interaction_type" value="portal"/>\n'
              '    <property name="interaction_range" type="float" value="4.5"/>\n'
              '    <property name="portal_text" value="Enter the Mycelic Grove"/>\n'
              '    <property name="target_world" type="int" value="1"/>\n'
              '   </properties>\n  </object>\n') % (oid, PX * 16, (PY + 2) * 16)
m = re.search(r'<objectgroup [^>]*name="WorldObjects"[^>]*>\n', s)
s = s[:m.end()] + portal_obj + s[m.end():]
s = re.sub(r'nextobjectid="\d+"', 'nextobjectid="%d"' % (oid + 1), s, count=1)

open(MAP, 'w').write(s)
print('first gid', NEW_FIRST, 'written')
