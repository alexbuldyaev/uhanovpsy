"""Собирает viktor-uhanov.html из template.html, methods.json и qr.svg."""
import json, re
from pathlib import Path

here = Path(__file__).parent
tpl = (here / "template.html").read_text(encoding="utf-8")
data = json.loads((here / "methods.json").read_text(encoding="utf-8"))
qr = (here / "qr.svg").read_text(encoding="utf-8")
qr = re.sub(r'\s(width|height)="[^"]*"', "", qr, count=2)

# Проверка ключа Шмишека: каждый из 88 вопросов ровно в одной шкале, максимум 24.
keys = re.findall(r'yes: \[([\d,]*)\], no: \[([\d,]*)\], k: (\d)', tpl)
seen = []
for yes, no, k in keys:
    items = [int(x) for x in (yes + "," + no).split(",") if x]
    assert len(items) * int(k) == 24, (items, k)
    seen += items
assert sorted(seen) == list(range(1, 89)), "ключ покрывает не все вопросы"
assert len(keys) == 10

out = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")).replace("__QR__", qr)
(here / "viktor-uhanov.html").write_text(out, encoding="utf-8")
print("ok", len(out), "bytes; key verified for", len(keys), "scales")
