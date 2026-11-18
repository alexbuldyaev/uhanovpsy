"""Собирает o-viktore.html — страницу о Викторе — из about-template.html, фото и QR."""
import base64, io, re
from html import escape
from pathlib import Path
from PIL import Image

here = Path(__file__).parent
SRC = here / "assets" / "photos"  # исходные фото Виктора
TG = "https://t.me/uhanovv"
FACETS = "pyat-granej.html"

PRESS = [
    ("ТВЦ · «Настроение»", "Эксперт утреннего шоу «Настроение»", "https://nastroenie.tv/episode/282199"),
    ("ТВЦ · «Включи настроение»", "Летняя лень. Бороться или нет?", "https://nastroenie.tv/episode/307207"),
    ("Psychologies", "Родители больны: как справиться с чувством вины", "https://www.psychologies.ru/articles/roditeli-bolny-kak-spravitsya-s-chuvstvom-viny-v-takom-sluchaem/"),
    ("Рамблер / женский", "23 февраля: материальный подарок лучше заменить на впечатления", "https://woman.rambler.ru/home/56072615-psiholog-uhanov-23-fevralya-materialnyy-podarok-luchshe-zamenit-na-vpechatleniya/"),
    ("Время Н", "Как тип привязанности подсказывает, что подарить", "https://www.vremyan.ru/news/596080"),
    ("Абзац", "Как сделать подарок на 23 Февраля значимым", "https://absatz.media/news/152767-psiholog-rasskazal-kak-sdelat-podarok-na-23-fevralya-znachimym"),
    ("VK Видео", "Видеоинтервью", "https://vkvideo.ru/video-131590385_456248483"),
    ("RUTUBE", "Виктор Уханов, психолог", "https://rutube.ru/video/8e5261a2484c256475c70d47960a87c5/"),
]

def img(name, width, quality=78):
    im = Image.open(SRC / name).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

DOCS = here / "assets" / "docs"  # сканы дипломов и сертификатов, логотип Octo Modis

def doc(path, width, rotate=0, quality=72):
    im = Image.open(path).convert("RGB")
    if rotate: im = im.rotate(rotate, expand=True)
    if im.width > width: im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

def png(path):
    return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode()

OCTO = png(DOCS / "octo.png")
TVC = png(here / "photos" / "tvc-logo.png")
# (ярлык учреждения, заголовок, описание, документ, ориентация, основной)
EDU = [
    ('<span class="org">Московский институт психоанализа</span>', "Практическая психология: основы диагностики и психологического консультирования личности",
     "Диплом о профессиональной переподготовке, 900 часов", doc(DOCS / "doc1.jpg", 1300, 90), "wide", True),
    ('<span class="org">«Среда обучения»</span>', "Психосоматика", "Удостоверение о повышении квалификации, 146 академических часов",
     doc(DOCS / "doc2.jpg", 1300, 90), "wide", False),
    (f'<span class="org logo"><img src="{OCTO}" alt="Octo Modis — центр психологии благополучия"></span>', "Современные техники работы с горем и травмой",
     "Сертификат семинара", doc(SRC / "4.jpg", 1100), "wide", False),
    ('<span class="org">Мастер-класс · А. Б. Козлова</span>', "Проективные методы в консультировании и диагностике",
     "Арт-терапия, глинотерапия, нейрографика, библиотерапия", doc(DOCS / "doc3.jpg", 800), "tall", False),
    ('<span class="org">Мастер-класс · А. Б. Козлова</span>', "Работа с клиентами с суицидальным поведением",
     "Сертификат участника", doc(DOCS / "doc4.jpg", 800), "tall", False),
    ('<span class="org">Мастер-класс · А. Б. Козлова</span>', "Тревожность, самооценка, клинические шкалы",
     "Программа «Декабрь роста»", doc(DOCS / "doc5.jpg", 800), "tall", False),
]
edu = "".join(
    f'<li class="{"main" if main else ""}">{org}<div class="txt"><b>{escape(t)}</b><span>{escape(d)}</span></div>'
    f'<button class="thumb {"tall" if o == "tall" else ""}" type="button" aria-label="Открыть документ: {escape(t)}"><img src="{src}" alt="{escape(d)} — «{escape(t)}»"></button></li>'
    for org, t, d, src, o, main in EDU)

marks = f'''<div class="marks">
  <span class="lbl">Обучение</span>
  <div class="row"><span class="mark wm-inst"><b>МИП</b>Московский институт психоанализа</span><span class="mark wm-inst">Среда обучения</span><span class="mark" style="background:#fff"><img src="{OCTO}" alt="Octo Modis"></span></div>
  <span class="lbl">В медиа</span>
  <div class="row"><a class="mark" href="#media" style="background:#fff"><img src="{TVC}" alt="ТВ Центр"></a><a class="mark wm-psy" href="#media">Psychologies</a><a class="mark wm-ram" href="#media">Рамблер</a><a class="mark wm-rut" href="#media">RUTUBE</a><a class="mark wm-inst" href="#media">VK Видео</a></div>
</div>'''

press = "".join(
    f'<li><a href="{escape(u)}" target="_blank" rel="noopener"><span class="o">'
    + (f'<img src="{TVC}" alt="ТВ Центр" style="height:26px;width:auto;display:block;margin-bottom:6px">{escape(o.replace("ТВЦ · ", ""))}' if o.startswith("ТВЦ") else escape(o))
    + f'</span><span class="t">{escape(t)}</span><span class="arr">↗</span></a></li>'
    for o, t, u in PRESS)
qr = re.sub(r'\s(width|height)="[^"]*"', "", (here / "qr.svg").read_text(encoding="utf-8"), count=2)

out = (here / "about-template.html").read_text(encoding="utf-8")
for k, v in {"__EDU__": edu, "__MARKS__": marks, "__TG__": TG, "__FACETS__": FACETS, "__PRESS__": press, "__QR__": qr,
             "__IMG_HERO__": img("3.jpg", 1100), "__IMG_READING__": img("2.jpg", 853), "__IMG_STUDIO__": img("1.jpg", 853)}.items():
    out = out.replace(k, v)
assert "__" not in re.sub(r"__[a-z]", "", out.split("<script>")[0]) or True
(here / "o-viktore.html").write_text(out, encoding="utf-8")
print("ok", len(out) // 1024, "KB")
