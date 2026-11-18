"""Собирает сайт Виктора в папку site/ и архив site.zip.

site/
  index.html   — страница о Викторе (из o-viktore.html)
  chekap.html  — экспресс-чекап «Пять граней» (из pyat-granej.html)
  favicon.svg
  img/         — фото, сканы документов и логотипы отдельными файлами

Перед запуском пересоберите исходные страницы: build_about.py и build_express.py.
"""
import base64
import hashlib
import re
import shutil
from pathlib import Path

here = Path(__file__).parent
site = here / "site"
# Очищаем сайт, но сохраняем историю git (.git) и служебные файлы хостинга.
KEEP = {".git", ".nojekyll", "CNAME"}
if site.exists():
    for item in site.iterdir():
        if item.name in KEEP:
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()
(site / "img").mkdir(parents=True, exist_ok=True)

EXT = {"image/jpeg": "jpg", "image/png": "png", "image/svg+xml": "svg"}
written = {}


def extract_images(html: str, prefix: str) -> str:
    """Заменяет data:-картинки на файлы в img/ (одинаковые картинки — один файл)."""
    def repl(m):
        mime, data = m.group(1), m.group(2)
        raw = base64.b64decode(data)
        key = hashlib.sha1(raw).hexdigest()[:10]
        if key not in written:
            name = f"{prefix}-{len(written) + 1}-{key}.{EXT[mime]}"
            (site / "img" / name).write_bytes(raw)
            written[key] = name
        return f"img/{written[key]}"
    return re.sub(r"data:(image/[a-z+]+);base64,([A-Za-z0-9+/=]+)", repl, html)


FAVICON = '<link rel="icon" href="favicon.svg" type="image/svg+xml">'
DOMAIN = "uhanovpsy.ru"
SITE_URL = f"https://{DOMAIN}/"


METRIKA_ID = 114350995


def add_metrika(html, webvisor, notice=True):
    """Счётчик Яндекс Метрики и короткое уведомление об использовании cookie."""
    opts = f"ssr:true, webvisor:{'true' if webvisor else 'false'}, clickmap:{'true' if webvisor else 'false'}, referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true"
    counter = f"""<!-- Yandex.Metrika counter -->
<script type="text/javascript">
    (function(m,e,t,r,i,k,a){{
        m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
        m[i].l=1*new Date();
        for (var j = 0; j < document.scripts.length; j++) {{if (document.scripts[j].src === r) {{ return; }}}}
        k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
    }})(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id={METRIKA_ID}', 'ym');
    ym({METRIKA_ID}, 'init', {{{opts}}});
</script>
<noscript><div><img src="https://mc.yandex.ru/watch/{METRIKA_ID}" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
<!-- /Yandex.Metrika counter -->
"""
    note_html = """<div id="cookie-note" hidden style="position:fixed;left:max(16px,env(safe-area-inset-left,0px));bottom:calc(16px + env(safe-area-inset-bottom,0px));z-index:50;max-width:360px;background:#1e2422;color:#fbfaf7;border-radius:16px;padding:14px 16px;font:13px/1.45 Manrope,-apple-system,'Segoe UI',Roboto,sans-serif;box-shadow:0 10px 30px rgba(0,0,0,.25);display:flex;gap:12px;align-items:center">
  <span>Сайт использует cookie и Яндекс Метрику, чтобы считать посещения. Ответы чекапа не передаются. <a href="privacy.html" style="color:#cbd8d2">Подробнее</a></span>
  <button type="button" id="cookie-ok" style="flex:none;border:0;border-radius:999px;background:#fbfaf7;color:#2d4a43;font:600 13px Manrope,-apple-system,sans-serif;padding:9px 14px;cursor:pointer">Понятно</button>
</div>
<script>
(function () {
  var note = document.getElementById("cookie-note"), KEY = "vu-cookie-ok";
  try { if (localStorage.getItem(KEY)) return; } catch (e) {}
  // над нижней панелью профиля, если она есть
  var lift = function () { var d = document.querySelector(".dock"); note.style.bottom = d ? "calc(" + (d.offsetHeight + 12) + "px + env(safe-area-inset-bottom,0px))" : "calc(16px + env(safe-area-inset-bottom,0px))"; };
  note.hidden = false; lift(); setInterval(lift, 1000);
  document.getElementById("cookie-ok").addEventListener("click", function () { note.remove(); try { localStorage.setItem(KEY, "1"); } catch (e) {} });
})();
</script>
"""
    html = html.replace("</head>", counter + "</head>", 1)
    return html.replace("</body>", note_html + "</body>", 1) if notice else html


def social(path, title, desc):
    """Карточка ссылки для Telegram, VK и других соцсетей."""
    return "".join([
        f'\n<link rel="canonical" href="{SITE_URL}{path}">',
        f'\n<meta property="og:type" content="website">',
        f'\n<meta property="og:url" content="{SITE_URL}{path}">',
        f'\n<meta property="og:title" content="{title}">',
        f'\n<meta property="og:description" content="{desc}">',
        f'\n<meta property="og:image" content="{SITE_URL}img/og.jpg">',
        '\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">',
        '\n<meta property="og:locale" content="ru_RU">',
        '\n<meta name="twitter:card" content="summary_large_image">',
    ])

about = (here / "o-viktore.html").read_text(encoding="utf-8")
about = about.replace('href="pyat-granej.html"', 'href="chekap.html"')
about = about.replace("</title>", "</title>\n" + FAVICON
                      + social("", "Виктор Уханов — практикующий психолог", "Давайте познакомимся. Экспресс-чекап «Пять граней» за 10 минут."), 1)
about = extract_images(about, "about")
# Отложенная загрузка для всего, что ниже первого экрана (портрет и ярлыки грузятся сразу).
EAGER = ("Виктор Уханов, портрет", "Octo Modis", "ТВ Центр")
about = re.sub(r'<img (src="img/[^"]+" alt="([^"]*)")', lambda m: m.group(0) if m.group(2).startswith(EAGER) else f'<img loading="lazy" decoding="async" {m.group(1)}', about)
about = add_metrika(about, webvisor=True)
(site / "index.html").write_text(about, encoding="utf-8")

chekap = (here / "pyat-granej.html").read_text(encoding="utf-8")
chekap = chekap.replace('href="o-viktore.html"', 'href="index.html"')
chekap = chekap.replace("</title>", "</title>\n" + FAVICON
                        + social("chekap.html", "«Пять граней» — экспресс-чекап Виктора Уханова", "Пять граней личности за 10 минут: архетип, привязанность, сценарии, ресурс и состояние."), 1)
chekap = extract_images(chekap, "chekap")
# На чекапе запись сеанса и карта кликов выключены: они показали бы выбранные ответы.
chekap = add_metrika(chekap, webvisor=False, notice=False)  # про cookie сказано на стартовом экране чекапа
(site / "chekap.html").write_text(chekap, encoding="utf-8")

(site / "privacy.html").write_text(add_metrika((here / "privacy.html").read_text(encoding="utf-8"), webvisor=True), encoding="utf-8")

# Свой домен для GitHub Pages
(site / "CNAME").write_text(DOMAIN + "\n", encoding="utf-8")

# Картинка для превью ссылки 1200×630: портрет Виктора на льняном фоне с именем
from PIL import Image, ImageDraw, ImageFont
og = Image.new("RGB", (1200, 630), (242, 240, 235))
photo = Image.open(here / "assets" / "photos" / "3.jpg").convert("RGB")
ph = photo.crop((150, 0, 150 + 1000, 1000)).resize((630, 630), Image.LANCZOS)
og.paste(ph, (570, 0))
d = ImageDraw.Draw(og)
def font(size, bold=False):
    for f in (["DejaVuSerif-Bold.ttf", "DejaVuSerif.ttf"] if bold else ["DejaVuSerif.ttf"]):
        for base in ("/usr/share/fonts/truetype/dejavu/", ""):
            try:
                return ImageFont.truetype(base + f, size)
            except OSError:
                pass
    return ImageFont.load_default()
d.text((70, 150), "Виктор", font=font(72), fill=(30, 36, 34))
d.text((70, 235), "Уханов", font=font(72), fill=(30, 36, 34))
d.text((72, 345), "Практикующий психолог", font=font(30), fill=(108, 114, 109))
d.rounded_rectangle((70, 430, 388, 492), radius=31, fill=(45, 74, 67))
d.text((100, 444), "uhanovpsy.ru", font=font(28), fill=(251, 250, 247))
og.save(site / "img" / "og.jpg", "JPEG", quality=85, optimize=True)

(site / "favicon.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="32" fill="#2d4a43"/>'
    '<text x="32" y="41" text-anchor="middle" font-family="Georgia, serif" font-style="italic" font-size="26" fill="#fbfaf7">ВУ</text></svg>',
    encoding="utf-8")

import zipfile
archive = here / "site.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:  # без .git — архив для ручной загрузки на хостинг
    for f in sorted(site.rglob("*")):
        if f.is_file() and ".git" not in f.relative_to(site).parts:
            z.write(f, f.relative_to(site))
total = sum(f.stat().st_size for f in site.rglob("*") if f.is_file())
print(f"site/: {len(list(site.rglob('*.*')))} файлов, {total // 1024} КБ; архив {Path(archive).name} — {Path(archive).stat().st_size // 1024} КБ")
for f in sorted(site.rglob("*")):
    if f.is_file():
        print(" ", f.relative_to(site), f.stat().st_size // 1024, "КБ")
