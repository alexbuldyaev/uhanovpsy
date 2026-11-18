"""Собирает pyat-granej.html («Пять граней») из express-template.html."""
import base64, io, json, re
from PIL import Image
from pathlib import Path

here = Path(__file__).parent
tpl = (here / "express-template.html").read_text(encoding="utf-8")
methods = json.loads((here / "methods.json").read_text(encoding="utf-8"))
data = {"lt": methods["lt"]}
qr = re.sub(r'\s(width|height)="[^"]*"', "", (here / "qr.svg").read_text(encoding="utf-8"), count=2)
# Мини-аватар Виктора: лицо из портрета на главной
_im = Image.open(here / "assets" / "photos" / "3.jpg").convert("RGB").crop((380, 180, 700, 500)).resize((192, 192), Image.LANCZOS)
_buf = io.BytesIO(); _im.save(_buf, "JPEG", quality=82, optimize=True)
AVATAR = "data:image/jpeg;base64," + base64.b64encode(_buf.getvalue()).decode()
tpl = tpl.replace("__AVATAR__", AVATAR)
out = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")).replace("__QR__", qr)
(here / "pyat-granej.html").write_text(out, encoding="utf-8")
print("ok", len(out), "bytes")
