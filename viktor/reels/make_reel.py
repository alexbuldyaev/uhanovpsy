"""Рилс 1080×1920 для Instagram: приглашение пройти «Пять граней».

Кадры рисуются в Pillow и передаются в ffmpeg. Запуск: python3 make_reel.py [путь_к_шрифтам]
Шрифты — пакеты @fontsource/cormorant-garamond и @fontsource/manrope (файлы .woff).
"""
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
PHOTOS = HERE.parent / "assets" / "photos"
FONTS = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "fonts"
OUT = HERE / "reel-pyat-granej.mp4"
W, H, FPS = 1080, 1920, 30

PAPER = (242, 240, 235); CARD = (251, 250, 247); INK = (30, 36, 34); SOFT = (74, 80, 76)
MUTED = (108, 114, 109); LINE = (224, 220, 211); PINE = (45, 74, 67); PINE_SOFT = (227, 233, 229); SAND = (205, 191, 168)


# ---------- шрифты: кириллица и латиница лежат в разных файлах ----------
def _font_pair(family, weight, style="normal"):
    base = FONTS / "@fontsource" / family / "files"
    return {sub: str(base / f"{family}-{sub}-{weight}-{style}.woff") for sub in ("cyrillic", "latin")}

FACES = {
    "serif": _font_pair("cormorant-garamond", 500),
    "serif-it": _font_pair("cormorant-garamond", 500, "italic"),
    "serif-b": _font_pair("cormorant-garamond", 600),
    "sans": _font_pair("manrope", 500),
    "sans-b": _font_pair("manrope", 600),
}
_cache = {}
def font(face, size, sub):
    key = (face, size, sub)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(FACES[face][sub], size)
    return _cache[key]

def is_cyr(ch):
    # В кириллическом файле только буквы; пробелы, кавычки и тире — в латинском.
    return "\u0400" <= ch <= "\u04ff"

def runs(text):
    out, cur, sub = [], "", None
    for ch in text:
        s = "cyrillic" if is_cyr(ch) else "latin"
        if sub is None or s == sub:
            cur += ch; sub = s
        else:
            out.append((sub, cur)); cur, sub = ch, s
    if cur:
        out.append((sub, cur))
    return out

def text_w(text, face, size, track=0):
    return sum(font(face, size, s).getlength(t) for s, t in runs(text)) + track * max(len(text) - 1, 0)

def draw_text(d, xy, text, face, size, fill, anchor="l", track=0):
    """Текст со сменой файла шрифта для кириллицы и латиницы. anchor: l | c | r (по горизонтали), y — базовая линия."""
    x, y = xy
    w = text_w(text, face, size, track)
    if anchor == "c": x -= w / 2
    elif anchor == "r": x -= w
    for sub, t in runs(text):
        f = font(face, size, sub)
        if track:
            for ch in t:
                d.text((x, y), ch, font=f, fill=fill, anchor="ls"); x += f.getlength(ch) + track
        else:
            d.text((x, y), t, font=f, fill=fill, anchor="ls"); x += f.getlength(t)
    return w


# ---------- анимация ----------
def ease(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def appear(t, start, dur=0.55):
    """0→1: прозрачность и подъём элемента, который появляется в момент start."""
    return ease((t - start) / dur)

def layer_with_alpha(base, layer, a):
    if a <= 0: return base
    if a >= 1: base.alpha_composite(layer); return base
    l = layer.copy(); l.putalpha(l.getchannel("A").point(lambda v: int(v * a)))
    base.alpha_composite(l); return base

def blank(color=PAPER):
    return Image.new("RGBA", (W, H), color + (255,))

def overlay():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def put(base, t, start, draw_fn, rise=36):
    a = appear(t, start)
    if a <= 0: return
    lay = overlay(); draw_fn(ImageDraw.Draw(lay), lay)
    if rise:
        lay = lay.transform(lay.size, Image.AFFINE, (1, 0, 0, 0, 1, -int(rise * (1 - a))), resample=Image.BILINEAR)
    layer_with_alpha(base, lay, a)


# ---------- материалы ----------
portrait = Image.open(PHOTOS / "3.jpg").convert("RGB")
reading = Image.open(PHOTOS / "2.jpg").convert("RGB")

def cover(img, w, h, focus=(0.5, 0.35), zoom=1.0):
    r = max(w / img.width, h / img.height) * zoom
    im = img.resize((math.ceil(img.width * r), math.ceil(img.height * r)), Image.LANCZOS)
    x = int((im.width - w) * focus[0]); y = int((im.height - h) * focus[1])
    return im.crop((x, y, x + w, y + h))

avatar = portrait.crop((380, 180, 700, 500)).resize((150, 150), Image.LANCZOS)
mask = Image.new("L", (150, 150), 0); ImageDraw.Draw(mask).ellipse((0, 0, 149, 149), fill=255)


# ---------- сцены (t — секунды от начала сцены) ----------
def s_hook(t):
    im = blank()
    put(im, t, 0.1, lambda d, l: draw_text(d, (W / 2, 640), "ЭКСПРЕСС-ЧЕКАП", "sans-b", 34, MUTED, "c", track=7))
    for i, line in enumerate(["Десять минут,", "чтобы лучше", "понять себя"]):
        put(im, t, 0.35 + i * 0.28, lambda d, l, line=line, i=i: draw_text(d, (W / 2, 830 + i * 132), line, "serif", 124, INK, "c"))
    put(im, t, 1.5, lambda d, l: draw_text(d, (W / 2, 1290), "авторский формат психолога", "serif-it", 54, SOFT, "c"))
    return im

def s_portrait(t, dur):
    z = 1.04 + 0.08 * (t / dur)
    im = cover(portrait, W, H, (0.42, 0.25), z).convert("RGBA")
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(230 * ease((y - H * 0.5) / (H * 0.42))) if y > H * 0.5 else 0)
    shade = Image.new("RGBA", (W, H), (20, 26, 24, 255)); shade.putalpha(grad.resize((W, H)))
    im.alpha_composite(shade)
    put(im, t, 0.4, lambda d, l: draw_text(d, (90, 1360), "Виктор Уханов", "serif", 112, CARD))
    put(im, t, 0.7, lambda d, l: draw_text(d, (92, 1440), "практикующий психолог · эксперт ТВЦ", "sans", 40, (214, 222, 218)))
    return im

FACETS = [("i", "Характер", "ваш ведущий архетип"), ("ii", "Отношения", "стиль привязанности"),
          ("iii", "Сценарии", "что у вас повторяется"), ("iv", "Ресурс", "сколько у вас сил"), ("v", "Состояние", "как вы сейчас")]

def s_facets(t):
    im = blank()
    put(im, t, 0.05, lambda d, l: draw_text(d, (90, 420), "АВТОРСКИЙ ФОРМАТ", "sans-b", 32, MUTED, track=6))
    put(im, t, 0.2, lambda d, l: draw_text(d, (86, 560), "Пять граней", "serif", 150, INK))
    for i, (n, title, sub) in enumerate(FACETS):
        y = 760 + i * 158
        def row(d, l, n=n, title=title, sub=sub, y=y):
            d.line((90, y - 70, W - 150, y - 70), fill=LINE, width=2)
            draw_text(d, (90, y + 8), n, "serif-it", 60, SAND)
            draw_text(d, (200, y + 8), title, "serif", 76, INK)
            draw_text(d, (202, y + 62), sub, "sans", 36, MUTED)
        put(im, t, 0.75 + i * 0.55, row, rise=24)
    return im

TAGS = ["#энергия", "#вдумчивость", "#осторожная_близость", "#есть_ресурс"]

def s_profile(t):
    im = blank()
    def card(d, l):
        d.rounded_rectangle((70, 380, W - 150, 1500), radius=48, fill=CARD, outline=LINE, width=2)
        l.paste(avatar, (120, 440), mask)
        draw_text(d, (300, 500), "ПЯТЬ ГРАНЕЙ", "sans-b", 28, MUTED, track=5)
        draw_text(d, (300, 556), "Виктор Уханов", "sans-b", 38, INK)
        draw_text(d, (120, 730), "Ваш профиль", "serif", 104, INK)
        draw_text(d, (120, 800), "архетип · привязанность · сценарии", "sans", 34, MUTED)
    put(im, t, 0.05, card, rise=30)
    x, y = 120, 900
    for i, tag in enumerate(TAGS):
        w = text_w(tag, "sans-b", 38) + 60
        if x + w > W - 200: x, y = 120, y + 98
        def chip(d, l, x=x, y=y, w=w, tag=tag, alt=i == 3):
            d.rounded_rectangle((x, y, x + w, y + 76), radius=38, fill=CARD if alt else PINE, outline=LINE if alt else PINE, width=2)
            draw_text(d, (x + 30, y + 51), tag, "sans-b", 38, PINE if alt else CARD)
        put(im, t, 0.6 + i * 0.32, chip, rise=16)
        x += w + 18
    def quote(d, l):
        draw_text(d, (120, 1240), "«Профиль — это карта,", "serif-it", 58, SOFT)
        draw_text(d, (120, 1312), "а не территория»", "serif-it", 58, SOFT)
    put(im, t, 2.0, quote)
    return im

def s_cta(t):
    im = blank(PINE)
    def top(d, l):
        l.paste(avatar, (int(W / 2 - 75), 430), mask)
        draw_text(d, (W / 2, 680), "СЕССИЯ ЗНАКОМСТВА", "sans-b", 32, (183, 198, 191), "c", track=6)
    put(im, t, 0.05, top)
    for i, line in enumerate(["Пройдите", "«Пять граней»", "и давайте", "познакомимся"]):
        put(im, t, 0.3 + i * 0.22, lambda d, l, line=line, i=i: draw_text(d, (W / 2, 860 + i * 118), line, "serif", 110, CARD, "c"))
    def link(d, l):
        txt = "uhanovpsy.ru/chekap"; w = text_w(txt, "sans-b", 46) + 90
        d.rounded_rectangle((W / 2 - w / 2, 1380, W / 2 + w / 2, 1480), radius=50, fill=CARD)
        draw_text(d, (W / 2, 1446), txt, "sans-b", 46, PINE, "c")
        draw_text(d, (W / 2, 1560), "ссылка — в шапке профиля", "sans", 38, (183, 198, 191), "c")
    put(im, t, 1.4, link)
    return im


SCENES = [(s_hook, 3.2), (s_portrait, 3.6), (s_facets, 4.6), (s_profile, 3.8), (s_cta, 4.6)]
XF = 0.35  # длительность перехода между сценами


def render():
    total = sum(d for _, d in SCENES)
    frames = int(total * FPS)
    starts, acc = [], 0.0
    for _, d in SCENES:
        starts.append(acc); acc += d
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k", str(OUT),
    ], stdin=subprocess.PIPE)

    def scene_img(k, ts):
        fn, d = SCENES[k]
        return fn(ts, d) if fn is s_portrait else fn(ts)

    cover_saved = False
    for f in range(frames):
        t = f / FPS
        k = max(i for i, s in enumerate(starts) if s <= t)
        im = scene_img(k, t - starts[k])
        nxt = k + 1
        if nxt < len(SCENES) and t > starts[nxt] - XF:
            a = (t - (starts[nxt] - XF)) / XF
            im = Image.blend(im.convert("RGB"), scene_img(nxt, 0).convert("RGB"), ease(a)).convert("RGBA")
        if not cover_saved and k == 2 and t - starts[2] > 3.6:
            im.convert("RGB").save(HERE / "reel-cover.jpg", quality=90); cover_saved = True
        ff.stdin.write(im.convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()
    print("ok", OUT.name, f"{total:.1f} c", OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    render()
