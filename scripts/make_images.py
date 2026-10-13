"""Banner + proje kartı görsellerini üretir (Pillow). python scripts/make_images.py"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
random.seed(7)

BG = (11, 15, 20)
GRID = (28, 36, 46)
GREEN = (74, 224, 154)
RED = (240, 96, 96)
AMBER = (245, 184, 76)
BLUE = (96, 165, 250)
TEXT = (230, 237, 243)
MUTED = (125, 138, 150)

FONT_DIRS = ["/usr/share/fonts/opentype/inter", "C:/Windows/Fonts", "/Library/Fonts"]


def font(name, size, fallback="DejaVuSans.ttf"):
    for d in FONT_DIRS:
        p = Path(d) / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    try:
        return ImageFont.truetype(fallback, size)
    except OSError:
        return ImageFont.load_default()


def mono(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "C:/Windows/Fonts/consola.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def grid(d, w, h, step):
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=GRID, width=1)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=GRID, width=1)


def glow(img, layer, radius=14):
    blurred = layer.filter(ImageFilter.GaussianBlur(radius))
    img.alpha_composite(blurred)
    img.alpha_composite(layer)


def price_walk(n, start=100.0, vol=1.6):
    p, out = start, []
    for _ in range(n):
        o = p
        c = o + random.gauss(0.15, vol)
        hi = max(o, c) + abs(random.gauss(0, vol * 0.7))
        lo = min(o, c) - abs(random.gauss(0, vol * 0.7))
        out.append((o, hi, lo, c))
        p = c
    return out


def candles(d, rect, bars, width_ratio=0.6):
    x0, y0, x1, y1 = rect
    lo = min(b[2] for b in bars)
    hi = max(b[1] for b in bars)
    sy = lambda v: y1 - (v - lo) / (hi - lo) * (y1 - y0)
    step = (x1 - x0) / len(bars)
    for i, (o, h, l, c) in enumerate(bars):
        cx = x0 + step * (i + 0.5)
        col = GREEN if c >= o else RED
        d.line([(cx, sy(h)), (cx, sy(l))], fill=col + (200,), width=2)
        bw = step * width_ratio / 2
        top, bot = sorted((sy(o), sy(c)))
        d.rectangle([cx - bw, top, cx + bw, max(bot, top + 2)], fill=col + (230,))
    return sy, step


def banner():
    W, H = 1500, 420
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    grid(d, W, H, 30)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    bars = price_walk(70)
    sy, step = candles(ld, (620, 60, W - 40, H - 60), bars)
    # trend / model line
    closes = [b[3] for b in bars]
    ema, a, pts = closes[0], 0.18, []
    for i, c in enumerate(closes):
        ema = a * c + (1 - a) * ema
        pts.append((620 + step * (i + 0.5), sy(ema)))
    ld.line(pts, fill=BLUE + (255,), width=3, joint="curve")
    glow(img, layer, 10)

    # left fade so text stays readable
    fade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fade)
    for x in range(900):
        alpha = int(255 * max(0, 1 - x / 900) ** 1.3)
        fd.line([(x, 0), (x, H)], fill=BG + (alpha,))
    img.alpha_composite(fade)

    d = ImageDraw.Draw(img)
    d.text((80, 120), "kaan ulusoy", font=font("Inter-Bold.otf", 84), fill=TEXT)
    d.text((84, 228), "quant finance  ·  machine learning  ·  security", font=font("Inter-Medium.otf", 28), fill=MUTED)
    d.rounded_rectangle([84, 290, 84 + 14, 304], 3, fill=GREEN)
    d.text((110, 283), "orderflow → features → model → signal", font=mono(22), fill=GREEN)
    img.convert("RGB").save(ROOT / "banner.png", optimize=True)


def card_base(title_tag):
    W, H = 800, 500
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    grid(d, W, H, 25)
    d.text((32, 26), title_tag, font=mono(20), fill=MUTED)
    return img, W, H


def card_lstm():
    img, W, H = card_base("okx / btc · eth · sol / 15m")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    bars = price_walk(36, vol=1.3)
    sy, step = candles(ld, (40, 80, W - 40, 330), bars)
    # probability strip
    for i, (o, h, l, c) in enumerate(bars):
        p = max(0.05, min(0.95, 0.5 + (c - o) / 6 + random.gauss(0, 0.12)))
        x = 40 + step * i
        col = GREEN if p >= 0.5 else RED
        hgt = abs(p - 0.5) * 220
        ld.rectangle([x + 3, 420 - hgt, x + step - 3, 420], fill=col + (150,))
    ld.line([(40, 420), (W - 40, 420)], fill=MUTED + (200,), width=1)
    glow(img, layer, 8)
    d = ImageDraw.Draw(img)
    d.text((40, 440), "P(up) per bar · balanced acc 0.580", font=mono(18), fill=TEXT)
    img.convert("RGB").save(ASSETS / "card-lstm.png", optimize=True)


def card_phishing():
    img, W, H = card_base("url → tokens → classifier")
    d = ImageDraw.Draw(img)
    f = mono(24)
    urls = [
        ("https://accounts.google.com/signin", GREEN, "0.02"),
        ("http://g00gle-verify-acc.xyz/login", RED, "0.97"),
        ("https://github.com/KaanUlusoytxt", GREEN, "0.01"),
        ("http://paypa1.com.session-renew.ru/?id=", RED, "0.94"),
        ("https://e-devlet-giris.tk/dogrula", RED, "0.91"),
        ("https://www.turkiye.gov.tr", GREEN, "0.03"),
    ]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for i, (u, col, s) in enumerate(urls):
        y = 85 + i * 62
        ld.rounded_rectangle([32, y, W - 32, y + 46], 8, outline=col + (160,), width=2, fill=(18, 24, 32, 255))
        ld.text((50, y + 10), u[:40], font=f, fill=TEXT + (255,))
        ld.text((W - 110, y + 10), s, font=f, fill=col + (255,))
    glow(img, layer, 6)
    img.convert("RGB").save(ASSETS / "card-phishing.png", optimize=True)


def card_passkeeper():
    img, W, H = card_base("vault · local-only · firefox")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cx, cy = W // 2, 270
    # shield
    pts = []
    for t in range(0, 181):
        a = math.radians(t)
        pts.append((cx + 130 * math.cos(a + math.pi), cy - 40 + 0))
    shield = [(cx - 130, cy - 130), (cx + 130, cy - 130), (cx + 130, cy), (cx, cy + 150), (cx - 130, cy)]
    ld.polygon(shield, outline=GREEN + (255,), width=4, fill=(14, 40, 30, 255))
    # lock
    ld.rounded_rectangle([cx - 50, cy - 30, cx + 50, cy + 50], 10, fill=GREEN + (255,))
    ld.arc([cx - 34, cy - 85, cx + 34, cy - 5], 180, 360, fill=GREEN + (255,), width=10)
    ld.ellipse([cx - 9, cy, cx + 9, cy + 18], fill=BG + (255,))
    glow(img, layer, 16)
    d = ImageDraw.Draw(img)
    d.text((40, 440), "Ctrl+Shift+L  →  autofill", font=mono(20), fill=TEXT)
    img.convert("RGB").save(ASSETS / "card-passkeeper.png", optimize=True)


def card_screener():
    img, W, H = card_base("bist · growth 40 / value 40 / quality 20")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    scores = sorted([random.uniform(0.25, 0.98) for _ in range(12)], reverse=True)
    for i, s in enumerate(scores):
        y = 80 + i * 30
        col = GREEN if i < 5 else (60, 72, 86)
        ld.text((40, y), f"#{i + 1:02d}", font=mono(18), fill=(MUTED if i >= 5 else TEXT) + (255,))
        g, v = s * 0.4, s * 0.4
        x0 = 110
        span = W - 160
        ld.rounded_rectangle([x0, y + 3, x0 + span * g, y + 21], 3, fill=(GREEN if i < 5 else col) + (255,))
        ld.rounded_rectangle([x0 + span * g, y + 3, x0 + span * (g + v), y + 21], 3, fill=(BLUE if i < 5 else col) + (255,))
        ld.rounded_rectangle([x0 + span * (g + v), y + 3, x0 + span * s, y + 21], 3, fill=(AMBER if i < 5 else col) + (255,))
    glow(img, layer, 6)
    img.convert("RGB").save(ASSETS / "card-screener.png", optimize=True)


if __name__ == "__main__":
    banner()
    card_lstm()
    card_phishing()
    card_passkeeper()
    card_screener()
    print("ok")
