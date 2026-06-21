# ЭкоРент — лендинг проката электромобилей (СПб)

Статический одностраничник проката и подписки на электромобили в Санкт-Петербурге.

**Живая версия:** https://elijah3737.github.io/ekorent-landing/

## Состав
- `index.html` — готовый статический сайт (контент в разметке, SEO/GEO-готов, RU/EN, адаптив).
- `favicon.svg`, `map.webp`, `og-image.jpg` — ассеты.
- `robots.txt`, `sitemap.xml` — для поисковиков.
- `build_static.py` — генератор `index.html` из шаблона.
- `_template.src.html` — редактируемый исходник дизайна.

## Пересборка статики
```bash
python3 build_static.py    # _template.src.html -> index.html
```

## Технологии
Чистый HTML/CSS/JS без зависимостей. Шрифты Manrope + Montserrat (Google Fonts).
Структурированные данные: JSON-LD (LocalBusiness/AutoRental + FAQPage).
