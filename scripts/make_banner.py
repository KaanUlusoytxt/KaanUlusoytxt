"""src/banner-source.png'den yazısız profil banner'ı üretir. python scripts/make_banner.py"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CROP = (0, 115, 729, 650)  # el + ipler + grafik bandı

art = Image.open(ROOT / "src" / "banner-source.png").convert("RGB").crop(CROP)
art = art.resize((art.width * 2, art.height * 2), Image.LANCZOS)
art.save(ROOT / "banner.png", optimize=True)
print("ok", art.size)
