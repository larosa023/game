"""Procedural 16px pixel-art houses for Oasis (3/4 top-down view).
draw_house(...) returns an RGBA image sized to whole tiles."""
from PIL import Image, ImageDraw
import random

T = 16

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)

ROOFS = {
    'red':   [(150, 62, 52), (178, 80, 62), (122, 48, 44), (92, 36, 38)],
    'slate': [(84, 98, 128), (104, 120, 152), (66, 76, 104), (48, 54, 78)],
    'moss':  [(96, 120, 64), (120, 146, 78), (74, 94, 52), (54, 70, 42)],
}
OUTLINE = (44, 30, 36, 255)


def roof(d, x0, y0, w, h, palette, rng):
    """Hip roof: a front plane narrowing toward the ridge, with lit left / shaded right hip faces."""
    base, light, dark, deep = palette
    inset_top = min(int(h * 0.55), w // 4)
    for y in range(h):
        t = y / max(1, h - 1)
        inset = int(inset_top * (1 - t))
        # vertical gradient: lighter near the ridge, darker toward the eave
        g = 1.12 - 0.22 * t
        front = shade(base, g)
        for x in range(w):
            if x < inset:
                c = shade(light, 0.92 + 0.08 * (1 - t))
            elif x >= w - inset:
                c = shade(dark, 0.95)
            else:
                c = front
            d.point((x0 + x, y0 + y), fill=c)
        # shingle courses every 5px on the front plane
        if y % 5 == 4 and y < h - 4:
            for x in range(inset + 1, w - inset - 1):
                d.point((x0 + x, y0 + y), fill=shade(base, g * 0.72))
            off = 0 if (y // 5) % 2 == 0 else 5
            for x in range(inset + 3 + off, w - inset - 2, 10):
                for k in range(1, 5):
                    if y + k < h - 4:
                        d.point((x0 + x, y0 + y + k), fill=shade(base, g * 0.8))
        # hip edges
        if inset > 0:
            d.point((x0 + inset, y0 + y), fill=shade(light, 1.1))
            d.point((x0 + w - inset - 1, y0 + y), fill=shade(dark, 0.75))
    for _ in range(w * h // 90):
        py = rng.randrange(y0 + 2, y0 + h - 6)
        inset = int(inset_top * (1 - (py - y0) / max(1, h - 1)))
        if w - 2 * inset - 6 <= 0: continue
        px = rng.randrange(x0 + inset + 3, x0 + w - inset - 3)
        d.point((px, py), fill=shade(light, 1.0))
    # ridge cap
    d.rectangle([x0 + inset_top, y0, x0 + w - inset_top - 1, y0 + 2], fill=shade(light, 1.08) + ())
    # eave lip
    d.rectangle([x0, y0 + h - 4, x0 + w - 1, y0 + h - 1], fill=deep + (255,))
    d.line([x0, y0 + h - 4, x0 + w - 1, y0 + h - 4], fill=shade(base, 0.8))
    # outline following the hip silhouette
    d.line([x0 + inset_top, y0, x0 + w - inset_top - 1, y0], fill=OUTLINE)
    d.line([x0, y0 + h - 1, x0 + w - 1, y0 + h - 1], fill=OUTLINE)
    d.line([x0, y0 + h - 1, x0, y0 + h - 4], fill=OUTLINE)
    d.line([x0 + w - 1, y0 + h - 1, x0 + w - 1, y0 + h - 4], fill=OUTLINE)
    for y in range(h - 3):
        inset = int(inset_top * (1 - y / max(1, h - 1)))
        d.point((x0 + inset, y0 + y), fill=OUTLINE)
        d.point((x0 + w - inset - 1, y0 + y), fill=OUTLINE)
    # clear the area outside the hip silhouette (transparent corners)
    return inset_top


def chimney(d, x, y):
    stone = (128, 120, 116)
    d.rectangle([x, y, x + 9, y + 15], fill=stone + (255,), outline=OUTLINE)
    for yy in range(y + 3, y + 15, 4):
        d.line([x + 1, yy, x + 8, yy], fill=(100, 92, 90, 255))
    d.rectangle([x - 1, y, x + 10, y + 2], fill=(92, 86, 84, 255), outline=OUTLINE)


def wall(d, x0, y0, w, h, rng, style):
    if style == 'plaster':
        base, trim = (228, 204, 160), (122, 78, 52)
    else:
        base, trim = (176, 124, 82), (104, 66, 44)
    d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=base + (255,))
    if style == 'wood':
        for y in range(y0 + 4, y0 + h, 4):
            d.line([x0, y, x0 + w - 1, y], fill=shade(base, 0.82))
        for _ in range(w * h // 60):
            d.point((rng.randrange(x0, x0 + w), rng.randrange(y0, y0 + h)), fill=shade(base, 0.9))
    else:
        for _ in range(w * h // 50):
            d.point((rng.randrange(x0, x0 + w), rng.randrange(y0, y0 + h)), fill=shade(base, 0.93))
        # timber frame posts every 3 tiles
        for x in range(x0, x0 + w, 48):
            d.rectangle([x, y0, x + 2, y0 + h - 1], fill=trim + (255,))
        d.rectangle([x0 + w - 3, y0, x0 + w - 1, y0 + h - 1], fill=trim + (255,))
    # shadow under the eave
    d.rectangle([x0, y0, x0 + w - 1, y0 + 2], fill=shade(base, 0.6))
    # foundation
    d.rectangle([x0, y0 + h - 4, x0 + w - 1, y0 + h - 1], fill=(120, 112, 108, 255))
    d.line([x0, y0 + h - 4, x0 + w - 1, y0 + h - 4], fill=(90, 84, 82, 255))
    d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], outline=OUTLINE)


def window(d, x, y):
    d.rectangle([x, y, x + 13, y + 11], fill=(92, 60, 42, 255), outline=OUTLINE)
    d.rectangle([x + 2, y + 2, x + 11, y + 9], fill=(96, 168, 196, 255))
    d.line([x + 2, y + 2, x + 5, y + 2], fill=(200, 236, 244, 255))
    d.point((x + 3, y + 3), fill=(200, 236, 244, 255))
    d.line([x + 7, y + 2, x + 7, y + 9], fill=(92, 60, 42, 255))
    d.line([x + 2, y + 6, x + 11, y + 6], fill=(92, 60, 42, 255))
    # flower box
    d.rectangle([x - 1, y + 11, x + 14, y + 13], fill=(120, 80, 50, 255), outline=OUTLINE)
    for i, c in enumerate([(220, 80, 90), (250, 210, 80), (220, 80, 90), (250, 210, 80)]):
        d.point((x + 2 + i * 3, y + 10), fill=c + (255,))


def door(d, x, y, w, h):
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=(70, 44, 32, 255), outline=OUTLINE)
    d.rectangle([x + 2, y + 2, x + w - 3, y + h - 1], fill=(132, 86, 52, 255))
    for xx in range(x + 5, x + w - 3, 5):
        d.line([xx, y + 3, xx, y + h - 1], fill=(104, 66, 40, 255))
    d.rectangle([x + 2, y + 2, x + w - 3, y + 4], fill=(108, 70, 44, 255))
    d.rectangle([x + w - 8, y + h // 2, x + w - 7, y + h // 2 + 1], fill=(240, 200, 90, 255))


def draw_house(tw, roof_rows, wall_rows, door_col, windows, palette='red', wall_style='plaster',
               chimney_col=None, seed=1):
    rng = random.Random(seed)
    W, H = tw * T, (roof_rows + wall_rows) * T
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rh = roof_rows * T
    wall(d, 3, rh - 2, W - 6, wall_rows * T + 2, rng, wall_style)
    top = 6 if chimney_col is not None else 0
    layer = Image.new('RGBA', (W, rh - top), (0, 0, 0, 0))
    inset_top = roof(ImageDraw.Draw(layer), 0, 0, W, rh - top, ROOFS[palette], rng)
    hgt = rh - top
    for y in range(hgt):
        inset = int(inset_top * (1 - y / max(1, hgt - 1)))
        for x in list(range(0, inset)) + list(range(W - inset, W)):
            pass  # hip faces stay (they read as the roof's sides)
    img.alpha_composite(layer, (0, top))
    if chimney_col is not None:
        chimney(d, chimney_col * T + 3, 0)
    wy = rh + 6
    for c in windows:
        window(d, c * T + 1, wy)
    door(d, door_col * T + 2, rh + (wall_rows * T) - 26, 2 * T - 4, 26)
    return img


def draw_stall_counter(tw, seed=3):
    """Crate counter with produce for under market stall awnings (2 rows tall)."""
    rng = random.Random(seed)
    img = Image.new('RGBA', (tw * T, 2 * T), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 6, tw * T - 1, 2 * T - 1], fill=(150, 100, 60, 255), outline=OUTLINE)
    for x in range(0, tw * T, 8):
        d.line([x, 7, x, 2 * T - 2], fill=(120, 78, 46, 255))
    d.line([1, 12, tw * T - 2, 12], fill=(176, 124, 80, 255))
    fruit = [(220, 70, 60), (250, 190, 60), (130, 190, 70), (200, 90, 160)]
    for x in range(3, tw * T - 4, 4):
        c = fruit[rng.randrange(len(fruit))]
        d.ellipse([x, 2 + rng.randrange(2), x + 4, 6 + rng.randrange(2)], fill=c + (255,), outline=shade(c, 0.6))
    return img
