"""Generate the Oasis title logo and app icons (pixel art)."""
from PIL import Image, ImageDraw
import os

GAME = '/home/claude/game'
OUT = (34, 22, 30, 255)

# 7-row bitmap glyphs
GLYPHS = {
    'O': ["01110", "11011", "11011", "11011", "11011", "11011", "01110"],
    'A': ["01110", "11011", "11011", "11111", "11011", "11011", "11011"],
    'S': ["01111", "11000", "11000", "01110", "00011", "00011", "11110"],
    'I': ["111", "010", "010", "010", "010", "010", "111"],
}


def palm(d, x, y, s=1):
    """Small palm tree with its base at (x, y)."""
    trunk = [(120, 80, 48), (150, 104, 62)]
    for i in range(9 * s):
        cx = x + int((i / (9 * s)) ** 2 * 3 * s)
        d.rectangle([cx, y - i, cx + s, y - i], fill=trunk[(i // s) % 2] + (255,))
    tx, ty = x + 3 * s, y - 9 * s
    leaf = (64, 150, 70, 255); leaf2 = (40, 110, 56, 255)
    for dx, dy in [(-5, 2), (-4, 1), (-3, 0), (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1), (3, 0), (4, 1), (5, 2)]:
        d.rectangle([tx + dx * s, ty + dy * s, tx + dx * s + s - 1, ty + dy * s + s - 1], fill=leaf)
    for dx, dy in [(-5, 3), (5, 3), (-3, 1), (3, 1), (-1, 0), (1, 0), (-4, 2), (4, 2)]:
        d.rectangle([tx + dx * s, ty + dy * s, tx + dx * s + s - 1, ty + dy * s + s - 1], fill=leaf2)
    d.rectangle([tx, ty + s, tx + s - 1, ty + 2 * s - 1], fill=(200, 150, 70, 255))  # coconut


def logo(px=4):
    text = "OASIS"
    widths = [len(GLYPHS[c][0]) for c in text]
    gap = 1
    gw = sum(widths) + gap * (len(text) - 1)
    W, H = (gw + 4) * px + 24 * px // 2, (7 + 10) * px
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    top = 7 * px
    # gradient: warm sand at top to teal at bottom
    grad = [(255, 226, 140), (250, 206, 110), (240, 180, 90), (110, 200, 190), (70, 170, 175), (50, 140, 160), (40, 110, 140)]
    x = 2 * px
    letter_boxes = []
    for c in text:
        g = GLYPHS[c]
        for r, row in enumerate(g):
            for k, bit in enumerate(row):
                if bit == '1':
                    letter_boxes.append((x + k * px, top + r * px))
        x += (len(g[0]) + gap) * px
    # outline pass (draw a dark block 1px around every lit cell)
    o = max(1, px // 2)
    for bx, by in letter_boxes:
        d.rectangle([bx - o, by - o, bx + px - 1 + o, by + px - 1 + o + px // 2], fill=OUT)
    for bx, by in letter_boxes:
        r = (by - top) // px
        d.rectangle([bx, by, bx + px - 1, by + px - 1], fill=grad[r] + (255,))
        d.rectangle([bx, by, bx + px - 1, by], fill=tuple(min(255, v + 30) for v in grad[r]) + (255,))
    # palm tree leaning over the I
    palm(d, x + px * 2, top + 7 * px, s=max(1, px // 2) * 2)
    # sun
    sx, sy = 4 * px, 2 * px
    d.ellipse([sx, sy, sx + 4 * px, sy + 4 * px], fill=(255, 196, 92, 255), outline=OUT)
    return img.crop(img.getbbox())


def icon(size):
    s = 32
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([1, 1, 30, 30], fill=(96, 190, 220, 255), outline=OUT)        # sky/water disc
    d.pieslice([1, 1, 30, 30], 0, 180, fill=(60, 150, 190, 255), outline=OUT)
    d.ellipse([5, 17, 26, 27], fill=(240, 206, 130, 255), outline=OUT)      # sand island
    d.ellipse([20, 5, 26, 11], fill=(255, 210, 100, 255))                   # sun
    palm(d, 12, 21, 1)
    return img.resize((size, size), Image.NEAREST)


if __name__ == '__main__':
    lg = logo(4)
    lg.save(GAME + '/assets/ui/oasis_logo.png')
    os.makedirs(GAME + '/lwjgl3/icons', exist_ok=True)
    os.makedirs(GAME + '/assets/icons', exist_ok=True)
    for n in (16, 32, 64, 128):
        icon(n).save(GAME + '/assets/icons/oasis_%d.png' % n)
    icon(256).save(GAME + '/lwjgl3/icons/logo.png')
    icon(256).save(GAME + '/lwjgl3/icons/logo.ico', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    prev = Image.new('RGBA', (lg.width + 140, max(lg.height, 128) + 20), (90, 40, 40, 255))
    prev.alpha_composite(lg, (10, 10)); prev.alpha_composite(icon(128), (lg.width + 10, 10))
    prev.resize((prev.width * 2, prev.height * 2), Image.NEAREST).save('/tmp/logo_prev.png')
    print(lg.size)
