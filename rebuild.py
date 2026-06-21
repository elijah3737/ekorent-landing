#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Пересборка standalone-лендинга из читаемого исходника шаблона.

Редактируем _template.src.html (обычный HTML с DSL sc-if/sc-for/{{ }}),
затем этот скрипт вшивает его обратно в <script type="__bundler/template">
внутри standalone-файла. Рантайм (manifest) не трогается.

Использование:  python3 rebuild.py
"""
import re, json, sys, shutil, os

SRC = "_template.src.html"
OUT = "Экорент Лэндинг.html"

src = open(SRC, encoding="utf-8").read()
html = open(OUT, encoding="utf-8").read()

# JSON-кодируем шаблон (как ожидает бандлер) и экранируем все "</",
# чтобы вложенные </script> внутри шаблона не закрыли внешний <script>.
encoded = json.dumps(src, ensure_ascii=False).replace("</", "<\\/")

pattern = re.compile(r'(<script type="__bundler/template">)(.*?)(</script>)', re.S)
matches = pattern.findall(html)
if len(matches) != 1:
    sys.exit(f"ОШИБКА: ожидался ровно 1 template-скрипт, найдено {len(matches)}")

# бэкап перед записью
shutil.copy2(OUT, OUT + ".bak")

new_html = pattern.sub(lambda m: m.group(1) + encoded + m.group(3), html, count=1)

# Отключаем отладочный error-оверлей бандлера (красный бокс "[bundle] error") —
# он ловит любой мелкий сбой загрузки ресурса и не предназначен для клиентов.
if "function(e) { return; /* overlay off */" not in new_html:
    new_html = new_html.replace(
        "window.addEventListener('error', function(e) {",
        "window.addEventListener('error', function(e) { return; /* overlay off */",
        1,
    )

# --- SEO / GEO: статический <head> (виден краулерам и AI БЕЗ JS) ---
if "<!--seo-head-->" not in new_html:
    TITLE = "Аренда электромобилей в Санкт-Петербурге — ЭкоРент | прокат и подписка"
    DESC = ("Прокат премиальных электромобилей в Санкт-Петербурге: посуточно, по подписке и с водителем. "
            "Без залога, КАСКО включено, бесплатная зарядка. Бронирование за пару минут.")
    URL = "https://eco-rent.ru/"
    faqs = [
        ("Что делать при ДТП или поломке?", "Позвоните на круглосуточную линию поддержки — мы оформим документы, при необходимости пришлём эвакуатор и подменный автомобиль. Все авто застрахованы по КАСКО и ОСАГО, ваша ответственность минимальна."),
        ("Могу ли я выехать за пределы Ленинградской области?", "Да, по территории России — без доплат и ограничений. Для выезда за границу нужно согласовать маршрут и оформить разрешение с менеджером заранее."),
        ("Как возвращать автомобиль — заряженным или нет?", "Заряжать перед возвратом не обязательно. Мы спишем стоимость только израсходованной энергии по тарифу."),
        ("Какие документы нужны для оформления?", "Достаточно паспорта и водительского удостоверения. Возраст — от 23 лет, стаж вождения — от 3 лет. Оформление занимает 10–15 минут."),
        ("Есть ли ограничение по пробегу?", "В посуточной аренде включено 300 км в сутки, далее — 12 ₽/км. В аренде по подписке пробег безлимитный."),
    ]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": ["AutoRental", "LocalBusiness"], "@id": URL + "#org", "name": "ЭкоРент",
         "description": "Прокат премиальных электромобилей в Санкт-Петербурге — посуточно, по подписке и с водителем.",
         "url": URL, "telephone": "+79119371888", "email": "info@eco-rent.ru", "priceRange": "₽₽",
         "address": {"@type": "PostalAddress", "streetAddress": "Уральская ул., 10, корпус 2, офис 39", "addressLocality": "Санкт-Петербург", "addressCountry": "RU"},
         "geo": {"@type": "GeoCoordinates", "latitude": 59.9486, "longitude": 30.2549},
         "areaServed": {"@type": "City", "name": "Санкт-Петербург"},
         "openingHoursSpecification": {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], "opens": "09:00", "closes": "21:00"},
         "sameAs": ["https://wa.me/79119371888", "https://t.me/"]},
        {"@type": "FAQPage", "@id": URL + "#faq",
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]},
    ]}
    ld_json = json.dumps(ld, ensure_ascii=False)
    seo = (
        '<!--seo-head-->\n'
        f'<title>{TITLE}</title>\n'
        f'<meta name="description" content="{DESC}">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="robots" content="index, follow">\n'
        f'<link rel="canonical" href="{URL}">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:site_name" content="ЭкоРент">\n'
        '<meta property="og:locale" content="ru_RU">\n'
        f'<meta property="og:title" content="{TITLE}">\n'
        f'<meta property="og:description" content="{DESC}">\n'
        f'<meta property="og:url" content="{URL}">\n'
        f'<meta property="og:image" content="{URL}og-image.jpg">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:image" content="{URL}og-image.jpg">\n'
        f'<script type="application/ld+json">{ld_json}</script>\n'
    )
    # lang + удалить старый <title>Bundled Page</title>, вставить SEO после charset
    new_html = new_html.replace("<html>", '<html lang="ru">', 1)
    new_html = new_html.replace("<title>Bundled Page</title>", "", 1)
    new_html = new_html.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + seo, 1)

open(OUT, "w", encoding="utf-8").write(new_html)

# проверка round-trip
chk = json.loads(pattern.search(new_html).group(2))
assert chk == src, "round-trip mismatch!"
print(f"OK: шаблон вшит ({len(src)} символов). Бэкап: {OUT}.bak")
