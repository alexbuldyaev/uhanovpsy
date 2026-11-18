# Исходники сайта Виктора Уханова

Эта ветка (`source`) хранит исходники. GitHub Pages публикует ветку `main`, в ней лежит только готовый сайт.

## Что где

- `viktor/about-template.html` — шаблон страницы о Викторе
- `viktor/express-template.html` — шаблон экспресс-чекапа «Пять граней» (вопросы, подсчёт, тексты профиля)
- `viktor/privacy.html` — политика обработки персональных данных
- `viktor/methods.json` — тексты опросника жизненных ловушек (мужской и женский бланк)
- `viktor/assets/` — исходные фото и сканы документов
- `viktor/photos/` — логотип ТВ Центр
- `viktor/build_*.py` — скрипты сборки
- `bot/`, `webapp/` — Telegram-бот и Mini App из первой версии проекта

## Как пересобрать сайт

```bash
cd viktor
python3 build_about.py && python3 build_express.py && python3 build_site.py
```

Готовый сайт появится в `viktor/site/`. Его содержимое копируется в ветку `main`.

Для `build_about.py` нужна библиотека Pillow: `pip install pillow`.
