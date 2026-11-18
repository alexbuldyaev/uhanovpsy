"""Собирает pyat-granej.html («Пять граней») из express-template.html."""
import json, re
from pathlib import Path

here = Path(__file__).parent
tpl = (here / "express-template.html").read_text(encoding="utf-8")
methods = json.loads((here / "methods.json").read_text(encoding="utf-8"))
data = {"lt": methods["lt"]}
qr = re.sub(r'\s(width|height)="[^"]*"', "", (here / "qr.svg").read_text(encoding="utf-8"), count=2)
out = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")).replace("__QR__", qr)
(here / "pyat-granej.html").write_text(out, encoding="utf-8")
print("ok", len(out), "bytes")
