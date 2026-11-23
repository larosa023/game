"""Generate the Mycelic Grove world (MyceliaWorld.tmx) and its extra tileset art."""
import random, os
from PIL import Image, ImageDraw

GAME = '/home/claude/game'
SRC = GAME + '/assets/world/asset/source/'
OUT = (34, 22, 30, 255)
rng = random.Random(1337)
W, H = 52, 40
MCOLS = 18                                # mushroom sheet columns
mush = Image.open(SRC + 'mushroomvillage_16px_all.png').convert('RGBA')


def M(c, r):                              # gid in Mushroom.tsx (firstgid 1)
    return 1 + r * MCOLS + c


# ---------------------------------------------------------------- extra art
XC, XR = 12, 4                            # extras sheet: 12 x 4 tiles
xs = Image.new('RGBA', (XC * 16, XR * 16), (0, 0, 0, 0))
xd = ImageDraw.Draw(xs)


def mushroom_stem(ox, oy, tint):
    """3x2 tile cream stem with a door and a round window, drawn at tile (ox, oy)."""
    x0, y0 = ox * 16 + 4, oy * 16
    w, h = 40, 32
    base = (244, 232, 196); dark = (214, 196, 150); deep = (180, 160, 116)
    xd.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=base + (255,))
    for x in range(w):
        f = x / (w - 1)
        if f < 0.18 or f > 0.82:
            xd.line([x0 + x, y0, x0 + x, y0 + h - 1], fill=dark + (255,))
    for _ in range(40):
        xd.point((x0 + rng.randrange(3, w - 3), y0 + rng.randrange(2, h - 2)), fill=dark + (255,))
    xd.rectangle([x0, y0, x0 + w - 1, y0 + 3], fill=deep + (255,))       # cap shadow
    xd.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], outline=OUT)
    # door from the sheet (14,3) and window (13,4)
    door = mush.crop((14 * 16, 3 * 16, 15 * 16, 4 * 16))
    win = mush.crop((13 * 16, 4 * 16, 14 * 16, 5 * 16))
    xs.alpha_composite(door, (ox * 16 + 16, oy * 16 + 16))
    xs.alpha_composite(win, (ox * 16 + 2, oy * 16 + 3))
    # little tint lantern
    xd.rectangle([ox * 16 + 36, oy * 16 + 18, ox * 16 + 39, oy * 16 + 22], fill=tint + (255,), outline=OUT)


def portal(ox, oy):
    """2x3 tile stone arch with a violet spore vortex."""
    x0, y0 = ox * 16, oy * 16
    stone, sd = (150, 146, 160), (104, 100, 118)
    xd.ellipse([x0 + 1, y0 + 1, x0 + 30, y0 + 40], fill=stone + (255,), outline=OUT)
    xd.rectangle([x0 + 1, y0 + 20, x0 + 30, y0 + 46], fill=stone + (255,), outline=OUT)
    for yy in range(y0 + 6, y0 + 46, 6):
        xd.line([x0 + 2, yy, x0 + 5, yy], fill=sd + (255,)); xd.line([x0 + 26, yy, x0 + 29, yy], fill=sd + (255,))
    # vortex
    for i, c in enumerate([(70, 30, 110), (110, 50, 170), (150, 90, 220), (190, 140, 250), (230, 200, 255)]):
        xd.ellipse([x0 + 6 + i * 2, y0 + 7 + i * 3, x0 + 25 - i * 2, y0 + 44 - i * 2], fill=c + (255,))
    for _ in range(14):
        a, b = rng.randrange(8, 24), rng.randrange(10, 42)
        xd.point((x0 + a, y0 + b), fill=(255, 255, 255, 255))
    xd.rectangle([x0 - 0, y0 + 44, x0 + 31, y0 + 47], fill=sd + (255,), outline=OUT)   # base step


mushroom_stem(0, 0, (255, 140, 60))
mushroom_stem(3, 0, (190, 120, 255))
mushroom_stem(6, 0, (110, 180, 255))
mushroom_stem(0, 2, (255, 90, 90))
portal(9, 0)
xs.save(SRC + 'generated/MyceliaExtras.png')
open(GAME + '/assets/world/asset/data/MyceliaExtras.tsx', 'w').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.11.0" name="MyceliaExtras" tilewidth="16" tileheight="16" tilecount="{XC * XR}" columns="{XC}">
 <image source="../source/generated/MyceliaExtras.png" width="{XC * 16}" height="{XR * 16}"/>
</tileset>
''')
XFIRST = 1 + 288


def X(c, r):
    return XFIRST + r * XC + c


# ---------------------------------------------------------------- layers
ground = [[M(1, 2)] * W for _ in range(H)]
deco = [[0] * W for _ in range(H)]
mid = [[0] * W for _ in range(H)]
top = [[0] * W for _ in range(H)]
collision = []           # (x, y, w, h) in tiles
blocked = [[False] * W for _ in range(H)]


def block(x, y, w, h, coll=True, pad=0.0):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if 0 <= xx < W and 0 <= yy < H: blocked[yy][xx] = True
    if coll: collision.append((x + pad, y + pad, w - 2 * pad, h - 2 * pad))


def nine(layer, x, y, w, h, c0, r0):
    """Fill a rectangle with a 3x3 autotile block whose top-left is (c0, r0)."""
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            cc = c0 + (0 if xx == x else 2 if xx == x + w - 1 else 1)
            rr = r0 + (0 if yy == y else 2 if yy == y + h - 1 else 1)
            layer[yy][xx] = M(cc, rr)


# forest border (canopy interior tiles, trunks facing in along the top)
def canopy(x, y):
    return M(6 + (x % 3), 11 + (y % 3))
for y in range(H):
    for x in range(W):
        if y < 3 or y >= H - 2 or x < 2 or x >= W - 2:
            mid[y][x] = canopy(x, y)
for x in range(2, W - 2):
    mid[3][x] = M(6 + (x % 3), 15)                       # trunks under the top canopy
block(0, 0, W, 3); block(0, H - 2, W, 2); block(0, 0, 2, H); block(W - 2, 0, 2, H)

# paths (rounded stone plaza tiles), autotiled from a mask so joints are seamless
pmask = [[False] * W for _ in range(H)]
for (x, y, w, h) in [(24, 4, 3, 13), (19, 15, 14, 9), (24, 23, 3, 12), (32, 18, 14, 3), (6, 18, 14, 3)]:
    for yy in range(y, y + h):
        for xx in range(x, x + w): pmask[yy][xx] = True
def pm(x, y): return 0 <= x < W and 0 <= y < H and pmask[y][x]
for y in range(H):
    for x in range(W):
        if not pmask[y][x]: continue
        c = 0 if not pm(x - 1, y) else 2 if not pm(x + 1, y) else 1
        r = 9 if not pm(x, y - 1) else 11 if not pm(x, y + 1) else 10
        deco[y][x] = M(c, r)

# spore pond ringed with reeds
nine(deco, 6, 6, 9, 7, 9, 9)
block(6, 6, 9, 7, pad=0.4)

# tall grass and flower patches
for (x, y, w, h, c0) in [(4, 26, 6, 5, 0), (12, 27, 6, 4, 3), (36, 6, 7, 5, 3), (40, 26, 7, 6, 0),
                         (29, 27, 5, 4, 3), (16, 5, 5, 4, 0)]:
    nine(deco, x, y, w, h, c0, 5)

# mushroom houses around the plaza: cap (3x2) on a generated stem (3x2)
houses = [((12, 7), (0, 0), 16, 11), ((12, 5), (3, 0), 33, 11), ((15, 7), (6, 0), 15, 24), ((15, 4), (0, 2), 33, 24)]
for (cap_c, cap_r), (sc, sr), hx, hy in houses:
    for r in range(2):
        for c in range(3):
            top[hy + r][hx + c] = M(cap_c + c, cap_r + r)
            mid[hy + 2 + r][hx + c] = X(sc + c, sr + r)
    block(hx, hy, 3, 4, pad=0.15)

# trees scattered on open ground (big 2x3, small 1x3)
def free(x, y, w, h):
    return all(0 <= xx < W and 0 <= yy < H and not blocked[yy][xx] and deco[yy][xx] == 0
               for yy in range(y - 1, y + h + 1) for xx in range(x - 1, x + w + 1))
placed = 0
while placed < 34:
    x, y = rng.randrange(3, W - 4), rng.randrange(4, H - 5)
    big = rng.random() < 0.6
    w = 2 if big else 1
    if not free(x, y, w, 3): continue
    for r in range(3):
        for c in range(w):
            if not big and r == 0: continue        # the small tree is only 2 tiles tall
            (mid if r == 2 else top)[y + r][x + c] = M((6 if big else 8) + c, 7 + r)
    block(x, y + 2, w, 1, pad=0.2)
    block(x, y, w, 2, coll=False)
    placed += 1

# bushes, pots, lanterns, stools for life
props = [(9, 12), (9, 13), (15, 1), (16, 1), (17, 1), (10, 12), (11, 12)]
for i in range(26):
    x, y = rng.randrange(3, W - 3), rng.randrange(5, H - 3)
    if not free(x, y, 1, 1): continue
    c, r = props[i % len(props)]
    if r == 1:                                      # potted plant is 1x2
        if not free(x, y, 1, 2): continue
        mid[y][x] = M(c, 1); mid[y + 1][x] = M(c, 2); block(x, y, 1, 2, coll=False)
    else:
        mid[y][x] = M(c, r); block(x, y, 1, 1, coll=False)

# return portal south of the plaza
PX, PY = 24, 33
for r in range(3):
    for c in range(2):
        mid[PY + r][PX + c] = X(9 + c, r)
block(PX, PY + 1, 2, 2, pad=0.1)

# ---------------------------------------------------------------- objects
oid = [100]
def nid():
    oid[0] += 1; return oid[0]

def props_xml(d):
    out = []
    for k, v in d.items():
        t = ' type="bool"' if isinstance(v, bool) else ' type="int"' if isinstance(v, int) else ' type="float"' if isinstance(v, float) else ''
        vv = str(v).lower() if isinstance(v, bool) else str(v)
        out.append(f'    <property name="{k}"{t} value="{vv}"/>')
    return '   <properties>\n' + '\n'.join(out) + '\n   </properties>\n'

def point(name, x, y, p=None):
    return f'  <object id="{nid()}"{(" name=%s" % chr(34) + name + chr(34)) if name else ""} x="{x * 16:.1f}" y="{y * 16:.1f}">\n' + (props_xml(p) if p else '') + '   <point/>\n  </object>\n'

def rect(name, x, y, w, h, p=None):
    head = f'  <object id="{nid()}"{(" name=%s" % chr(34) + name + chr(34)) if name else ""} x="{x * 16:.1f}" y="{y * 16:.1f}" width="{w * 16:.1f}" height="{h * 16:.1f}"'
    return head + ('>\n' + props_xml(p) + '  </object>\n' if p else '/>\n')

actions = point('WorldSpawn', PX + 1, PY - 1.5)
coll = ''.join(rect(None, *c) for c in collision)
worldobjs = rect('portal', PX, PY, 2, 1.5, {
    'interactable': True, 'interaction_type': 'portal', 'target_world': 0, 'portal_text': 'Return home',
    'interaction_range': 4.5})
# mushrooms to pick up (rare silver spores and a codex hidden deep in the grove)
items = []
def walkable(x, y):
    return 2 < x < W - 3 and 4 < y < H - 3 and not blocked[y][x]
tries = 0
while len(items) < 18 and tries < 5000:
    tries += 1
    x, y = rng.randrange(3, W - 3), rng.randrange(5, H - 3)
    if not walkable(x, y) or any(abs(x - a) + abs(y - b) < 4 for a, b, _ in items): continue
    kind = 'SILVER_SPORE' if len(items) in (5, 13) else ('CRIMSON_CAP' if len(items) % 2 else 'VERDANT_FUNGUS')
    items.append((x, y, kind))
items.append((47, 5, 'ARCANA_CODEX'))
for x, y, kind in items:
    worldobjs += rect(None, x + 0.2, y + 0.2, 0.6, 0.6, {'interactable': True, 'interaction_type': 'map_item', 'item': kind, 'item_amount': 1})
entities = ''
spots = [(40, 8), (44, 14), (38, 22), (46, 24), (42, 31), (9, 22), (8, 32), (31, 6), (36, 30)]
for x, y in spots:
    while blocked[y][x]: x += 1
    entities += point(None, x, y, {'enemy': True, 'key': 'oasis:sporeling'})

# ---------------------------------------------------------------- write TMX
def csv(layer):
    rows = [','.join(str(v) for v in row) for row in layer]
    return '\n' + ',\n'.join(rows) + '\n'

tmx = f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.11.0" orientation="orthogonal" renderorder="right-down" width="{W}" height="{H}" tilewidth="16" tileheight="16" infinite="0" backgroundcolor="#1e2a24" nextlayerid="20" nextobjectid="{oid[0] + 1}">
 <tileset firstgid="1" source="../asset/data/Mushroom.tsx"/>
 <tileset firstgid="{XFIRST}" source="../asset/data/MyceliaExtras.tsx"/>
 <layer id="1" name="TheGround" width="{W}" height="{H}">
  <data encoding="csv">{csv(ground)}</data>
 </layer>
 <layer id="2" name="Background" width="{W}" height="{H}">
  <data encoding="csv">{csv(deco)}</data>
 </layer>
 <layer id="3" name="Middle" width="{W}" height="{H}">
  <data encoding="csv">{csv(mid)}</data>
 </layer>
 <layer id="4" name="Top" width="{W}" height="{H}">
  <data encoding="csv">{csv(top)}</data>
 </layer>
 <objectgroup id="10" name="Collision">
{coll} </objectgroup>
 <objectgroup id="11" name="Actions">
{actions} </objectgroup>
 <objectgroup id="12" name="WorldObjects">
{worldobjs} </objectgroup>
 <objectgroup id="13" name="Entities">
{entities} </objectgroup>
</map>
'''
open(GAME + '/assets/world/worlds/MyceliaWorld.tmx', 'w').write(tmx)
print('items', len(items), 'collisions', len(collision))
