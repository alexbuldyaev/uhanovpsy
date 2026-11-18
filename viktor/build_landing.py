"""Собирает тестовую статью-лендинг «Избегающий тип привязанности» в один файл."""
import base64, io
from pathlib import Path
from PIL import Image

here = Path(__file__).parent

def jpg(img, quality=78):
    buf = io.BytesIO(); img.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

photo = Image.open(here / "assets" / "photos" / "2.jpg")
avatar = Image.open(here / "assets" / "photos" / "3.jpg").crop((380, 180, 700, 500)).resize((120, 120), Image.LANCZOS)

out = (here / "landing-avoidant-template.html").read_text(encoding="utf-8")
for k, v in {
    "__AVATAR__": jpg(avatar, 82), "__PHOTO__": jpg(photo),
    "__TG__": "https://t.me/uhanovv", "__ABOUT__": "https://uhanovpsy.ru/", "__CHEKAP__": "https://uhanovpsy.ru/chekap.html",
}.items():
    out = out.replace(k, v)
assert "__" not in out.split("<script>")[0].replace("__proto__", ""), "остался незаменённый плейсхолдер"
(here / "landing-avoidant.html").write_text(out, encoding="utf-8")
print("ok", len(out.encode()) // 1024, "KB")
