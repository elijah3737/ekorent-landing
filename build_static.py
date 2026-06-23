#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вариант Б: чистый статический index.html из _template.src.html.
Разворачивает DSL (sc-for/sc-if/{{ }}) в готовый HTML, переносит интерактив
на ванильный JS (табы/аккордеон/FAB/RU-EN), style-hover -> CSS :hover,
добавляет SEO-голову, Google Fonts, robots/sitemap уже отдельными файлами.
Запуск: python3 build_static.py  ->  index.html
"""
import re, json

SRC = "_template.src.html"
OUT = "index.html"
URL = "https://eco-rent.ru/"
src = open(SRC, encoding="utf-8").read()
head_src = src[:src.find('<script type="text/x-dc"')]

# ---------- данные ----------
PERIODS = ['1–3 сут', '4–7 сут', '8–15 сут', '16–31 сут', '31+ сут']
# Реальный парк клиента (5 авто). Цены — от клиента (актуальные).
# Фото — проверенные Unsplash-ID (плейсхолдеры под реальные фото клиента).
IMG = lambda i: f"https://images.unsplash.com/photo-{i}?auto=format&fit=crop&w=720&q=75"
CARS = [
    dict(brand="Tesla",   model="Model Y", year="2022", rng="533", accel="5,0", battery="75",
         prices=['12 000', '11 000', '10 000', '9 000', '8 000'], img=IMG("1669625397388-32934837bd3a")),
    dict(brand="Tesla",   model="Model 3", year="2022", rng="510", accel="6,1", battery="60",
         prices=['10 000', '9 000', '8 000', '7 000', '6 000'], img=IMG("1606016159991-dfe4f2746ad5")),
    dict(brand="Evolute", model="i-Sky",   year="2024", rng="405", accel="9,5", battery="62",
         prices=['9 000', '8 000', '7 000', '6 000', '5 000'], img=IMG("1767949374180-e5895daa1990")),
    dict(brand="Evolute", model="i-Pro",   year="2022", rng="433", accel="9,9", battery="54",
         prices=['4 500', '4 000', '3 500', '3 000', '2 500'], img=IMG("1711921127505-f4a8727329a5")),
    dict(brand="BMW",     model="i3",      year="",     rng="300", accel="7,3", battery="42",
         prices=['4 500', '4 200', '3 900', '3 600', '3 300'], img=IMG("1666005336445-3b5fdcc6cc3b")),
]

# EN-словарь из шаблона + патч под новые/изменённые строки (чтобы EN-перевод не сломался)
mEN = re.search(r'var EN = (\{.*?\});', src, re.S)
_en = json.loads(mEN.group(1))
_en.update({
    "Аренда от 1 суток": "Rental from 1 day",
    "ОСАГО на всех, КАСКО частично": "OSAGO on all, CASCO on some",
    "Позвоните на круглосуточную линию поддержки — мы оформим документы, при необходимости пришлём эвакуатор и подменный автомобиль. Все авто застрахованы по ОСАГО, на части машин действует КАСКО — ваша ответственность минимальна.": "Call our 24/7 support line — we'll handle the paperwork and, if needed, send a tow truck and a replacement car. All cars have OSAGO insurance, some also have CASCO — your liability is minimal.",
    "Достаточно паспорта и водительского удостоверения. Возраст — от 22 лет, стаж вождения — от 2 лет. Оформление занимает 10–15 минут.": "A passport and a driver's license are enough. Age — from 22, driving experience — from 2 years. Registration takes 10–15 minutes.",
    "В посуточной аренде включено 200 км в сутки, далее — 10 ₽/км. В аренде по подписке пробег безлимитный.": "Daily rental includes 200 km per day, then 10 ₽/km. Subscription rental has unlimited mileage.",
})
EN_JSON = json.dumps(_en, ensure_ascii=False)

# ---------- извлечь тело (#top целиком, с FAB) ----------
bi = src.find('<div id="top"')
xdc = src.find('</x-dc>')
body = src[bi: src.rfind('</div>', bi, xdc) + 6]

# ---------- стили из шаблона (keyframes, mobile-css, faq placeholder, contactRise) ----------
styles = "\n".join(re.findall(r'<style[^>]*>.*?</style>', head_src, re.S))
# все <style> переезжают в head — из тела убираем
body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.S)

# ============ ТРАНСФОРМАЦИИ ТЕЛА ============

def find_scfor(s, marker):
    """вернуть (start, inner_start, inner_end, end) для sc-for, корректно при вложенности."""
    o = s.find(marker)
    inner0 = s.find('>', o) + 1
    depth = 1; i = inner0
    while depth:
        nxt_open = s.find('<sc-for', i)
        nxt_close = s.find('</sc-for>', i)
        if nxt_open != -1 and nxt_open < nxt_close:
            depth += 1; i = nxt_open + 7
        else:
            depth -= 1; i = nxt_close + 9
    return o, inner0, nxt_close, i

# --- 1. ТАБЫ: удалить чипсы целиком (вместе с обёрткой) ---
o, i0, ic, e = find_scfor(body, '<sc-for list="{{ tabs }}"')
wrap_start = body.rfind('<div', 0, o)
wrap_end = body.index('</div>', e) + 6
body = body[:wrap_start] + body[wrap_end:]

# --- 2. КАРТОЧКИ АВТО -> КАРУСЕЛЬ ---
o, i0, ic, e = find_scfor(body, '<sc-for list="{{ visibleCars }}"')
card_tpl = body[i0:ic]
# извлечь шаблон строки таблицы цен (ladder)
lo, li0, lic, le = find_scfor(card_tpl, '<sc-for list="{{ car.ladder }}"')
tier_tpl = card_tpl[li0:lic]
# карта без ladder-sc-for (заменим маркером)
card_wo = card_tpl[:lo] + "@@LADDER@@" + card_tpl[le:]
# убрать hideLadder-ветку, развернуть showLadder
card_wo = re.sub(r'<sc-if value="\{\{ hideLadder \}\}".*?</sc-if>', '', card_wo, flags=re.S)
card_wo = re.sub(r'<sc-if value="\{\{ showLadder \}\}"[^>]*>(.*?)</sc-if>', r'\1', card_wo, flags=re.S)

cards_html = ""
for c in CARS:
    ladder = ""
    for p, price in zip(PERIODS, c['prices']):
        t = tier_tpl.replace('{{ tier.period }}', p).replace('{{ tier.price }}', price)
        ladder += t
    card = card_wo.replace('@@LADDER@@', ladder)
    # бейдж: год выпуска (вместо класса); без года — убрать бейдж
    if c['year']:
        card = card.replace('{{ car.clsLabel }}', c['year'])
    else:
        card = re.sub(r'<span style="position:absolute;top:16px;left:16px;[^"]*">\{\{ car\.clsLabel \}\}</span>', '', card)
    card = (card.replace('{{ car.brand }}', c['brand'])
                .replace('{{ car.model }}', c['model'])
                .replace('{{ car.range }}', c['rng'])
                .replace('{{ car.accel }}', c['accel'])
                .replace('{{ car.battery }}', c['battery'])
                .replace("url('{{ car.img }}')", f"url('{c['img']}')")
                .replace('{{ car.img }}', c['img']))
    card = card.replace('onclick="{{ car.book }}"', 'data-act="contact"')
    # карточка = слайд карусели (фикс. ширина + snap)
    card = card.replace('<div style="background:#fff;border:1px solid rgba(10,11,13,0.07);border-radius:24px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 1px 2px rgba(0,0,0,0.04)',
                        '<div class="car-card" style="flex:0 0 330px;scroll-snap-align:start;background:#fff;border:1px solid rgba(10,11,13,0.07);border-radius:24px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 1px 2px rgba(0,0,0,0.04)')
    cards_html += card

CHEV_L = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0A0B0D" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"></path></svg>'
CHEV_R = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0A0B0D" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"></path></svg>'
ARROW = lambda cls, lbl, pos, chev: (f'<button class="{cls}" aria-label="{lbl}" style="position:absolute;top:130px;{pos};transform:translateY(-50%);width:48px;height:48px;border-radius:50%;background:#fff;border:1px solid rgba(10,11,13,0.1);box-shadow:0 10px 28px rgba(0,0,0,0.14);cursor:pointer;display:flex;align-items:center;justify-content:center;z-index:5;transition:transform .15s ease" style-hover="transform:translateY(-50%) scale(1.08)">' + chev + '</button>')
carousel = ('<div class="cat-carousel" style="position:relative">'
            '<div class="cat-track" style="display:flex;gap:24px;overflow-x:auto;scroll-behavior:smooth;padding:6px 0 16px">'
            + cards_html + '</div>'
            + ARROW('cat-prev', 'Назад', 'left:-8px', CHEV_L)
            + ARROW('cat-next', 'Вперёд', 'right:-8px', CHEV_R)
            + '</div>')
grid_open = body.rfind('<div', 0, o)
grid_close = body.index('</div>', e) + 6
body = body[:grid_open] + carousel + body[grid_close:]

# --- 3. FAQ ---
o, i0, ic, e = find_scfor(body, '<sc-for list="{{ faqItems }}"')
faq_tpl = body[i0:ic]
faqs = []
for m in re.finditer(r"\{ q: '((?:[^'\\]|\\.)*)', a: '((?:[^'\\]|\\.)*)' \}", src):
    faqs.append((m.group(1).replace("\\'", "'"), m.group(2).replace("\\'", "'")))
faqs = faqs[:5]
# выделить chevron (open=up, closed=down) и answer из шаблона
chev_up = re.search(r'<sc-if value="\{\{ f\.open \}\}"[^>]*><span[^>]*>.*?</span></sc-if>', faq_tpl, re.S).group(0)
chev_up = re.sub(r'</?sc-if[^>]*>', '', chev_up)
chev_down = re.search(r'<sc-if value="\{\{ f\.closed \}\}"[^>]*><span[^>]*>.*?</span></sc-if>', faq_tpl, re.S).group(0)
chev_down = re.sub(r'</?sc-if[^>]*>', '', chev_down)
ans_block = re.search(r'<sc-if value="\{\{ f\.open \}\}"[^>]*>\s*<div style="padding:0 2px 22px.*?</div>\s*</sc-if>', faq_tpl, re.S).group(0)
ans_inner = re.search(r'(<div style="padding:0 2px 22px.*?</div>)', ans_block, re.S).group(1)
faq_html = ""
for idx, (q, a) in enumerate(faqs):
    ans = ans_inner.replace('{{ f.a }}', a)
    faq_html += (
        '<div style="border-top:1px solid rgba(10,11,13,0.1)">'
        f'<button class="faq-q" data-faq="{idx}" style="width:100%;display:flex;align-items:center;justify-content:space-between;gap:18px;background:none;border:none;padding:22px 2px;cursor:pointer;text-align:left;font-family:Manrope">'
        f'<span style="font-weight:700;font-size:17px;color:#0A0B0D;line-height:1.35">{q}</span>'
        f'<span class="faq-chev-down">{chev_down}</span><span class="faq-chev-up" style="display:none">{chev_up}</span>'
        '</button>'
        f'<div class="faq-a" style="display:none">{ans}</div>'
        '</div>')
faq_html += '<div style="border-top:1px solid rgba(10,11,13,0.1)"></div>'
body = body[:o] + faq_html + body[e:]

# --- 4. ШАПКА: переключатель языка ---
lang_block_re = re.compile(r'<div style="display:flex;background:#F4F6F5;border-radius:999px;padding:3px;gap:2px">.*?</div>', re.S)
lang_new = ('<div style="display:flex;background:#F4F6F5;border-radius:999px;padding:3px;gap:2px">'
 '<button class="lang-btn is-active" data-lang="ru" style="border:none;background:#fff;border-radius:999px;padding:6px 11px;font-family:Manrope;font-weight:700;font-size:12px;color:#0A0B0D;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.1)">RU</button>'
 '<button class="lang-btn" data-lang="en" style="border:none;background:none;border-radius:999px;padding:6px 11px;font-family:Manrope;font-weight:700;font-size:12px;color:#6E7378;cursor:pointer">EN</button>'
 '</div>')
body = lang_block_re.sub(lang_new, body, count=1)

# --- 5. FAB (контакты): заменить весь showAssistant-блок чистой статикой ---
items_inner = re.search(r'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:13px">(.*?)</div>\s*</sc-if>', src, re.S).group(1)
for k, v in {'{{ maxUrl }}': 'https://max.ru/', '{{ tgUrl }}': 'https://t.me/',
             '{{ waUrl }}': 'https://wa.me/79119371888', '{{ phoneUrl }}': 'tel:+79119371888'}.items():
    items_inner = items_inner.replace(k, v)
PHONE_SVG = '<svg class="fab-phone" width="27" height="27" viewBox="0 0 24 24" fill="none" stroke="#04140B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.8.4 1.6.7 2.3a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.7-1.3a2 2 0 0 1 2.1-.4c.7.3 1.5.6 2.3.7a2 2 0 0 1 1.7 2z"></path></svg>'
X_SVG = '<svg class="fab-x" style="display:none" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#04140B" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"></path></svg>'
fab_static = (
 '<div style="position:fixed;right:24px;bottom:24px;z-index:95;display:flex;flex-direction:column;align-items:flex-end;gap:13px">'
 '<div class="fab-items" style="display:none;flex-direction:column;align-items:flex-end;gap:13px">' + items_inner + '</div>'
 '<button data-act="fab" aria-label="Связаться" style-hover="transform:scale(1.07)" style="position:relative;width:62px;height:62px;border-radius:50%;border:none;cursor:pointer;background:linear-gradient(135deg,#00E05B,#00B84D);box-shadow:0 14px 34px rgba(0,224,91,0.46);display:flex;align-items:center;justify-content:center;transition:transform .18s ease">'
 '<span style="position:absolute;inset:0;border-radius:50%;background:#00E05B;animation:ecoPulse 2.6s ease-out infinite;z-index:-1"></span>'
 + PHONE_SVG + X_SVG +
 '</button></div>')
body = re.sub(r'<sc-if value="\{\{ showAssistant \}\}".*</sc-if>', lambda m: fab_static, body, flags=re.S)

# --- 6. простые sc-if (isHeroA) -> оставить содержимое (без вложенности) ---
body = re.sub(r'<sc-if value="\{\{ isHeroA \}\}"[^>]*>(.*?)</sc-if>', r'\1', body, flags=re.S)

# --- 7. биндинги {{ }} ---
binds = {
 '{{ city }}': 'Санкт-Петербург',
 '{{ maxUrl }}': 'https://max.ru/', '{{ tgUrl }}': 'https://t.me/',
 '{{ waUrl }}': 'https://wa.me/79119371888', '{{ phoneUrl }}': 'tel:+79119371888',
}
for k, v in binds.items():
    body = body.replace(k, v)
# обработчики
body = body.replace('onclick="{{ openChatPlain }}"', 'data-act="contact"')
body = body.replace('onclick="{{ toggleContact }}"', 'data-act="fab"')

# --- 8. onclick на ссылках контактов уже href; убрать остаточные {{ }} в href (нет) ---

# --- 9. style-hover -> CSS :hover ---
hover_css = []
def repl_hover(m):
    rules = m.group(1)
    n = len(hover_css)
    hover_css.append(f'.eh{n}:hover{{{rules}}}')
    return f' data-eh="{n}"'
body = re.sub(r' style-hover="([^"]*)"', repl_hover, body)
# проставить класс eh{n} элементам с data-eh
def add_class(m):
    n = m.group(1)
    return f' class="eh{n}"'
body = re.sub(r' data-eh="(\d+)"', add_class, body)

# --- 10. чистка служебных атрибутов ---
body = re.sub(r' data-reveal=""', '', body)
body = re.sub(r' data-parallax=""', '', body)
body = re.sub(r' hint-placeholder(?:-count|-val)?="[^"]*"', '', body)
# опасный leftover: opacity:0 от reveal (на всякий) — уже opacity:1 в исходнике

# проверка: не осталось ли DSL
leftover = re.findall(r'\{\{|sc-for|sc-if|onclick="\{\{', body)
if leftover:
    import sys
    for mm in re.finditer(r'\{\{[^}]*\}\}|<sc-if[^>]*>|<sc-for[^>]*>', body):
        print("LEFT:", repr(body[max(0,mm.start()-50):mm.end()+12]), file=sys.stderr)
    sys.exit("остался DSL")

# ============ HEAD ============
TITLE = "Аренда электромобилей в Санкт-Петербурге — ЭкоРент | прокат и подписка"
DESC = ("Прокат премиальных электромобилей в Санкт-Петербурге: посуточно, по подписке и с водителем. "
        "Без залога, КАСКО включено, бесплатная зарядка. Бронирование за пару минут.")
faqs_ld = [(q, a) for q, a in faqs]
ld = {"@context": "https://schema.org", "@graph": [
    {"@type": ["AutoRental", "LocalBusiness"], "@id": URL + "#org", "name": "ЭкоРент",
     "description": "Прокат премиальных электромобилей в Санкт-Петербурге — посуточно, по подписке и с водителем.",
     "url": URL, "telephone": "+79119371888", "email": "info@eco-rent.ru", "priceRange": "₽₽",
     "image": URL + "og-image.jpg",
     "address": {"@type": "PostalAddress", "streetAddress": "Уральская ул., 10, корпус 2, офис 39", "addressLocality": "Санкт-Петербург", "addressCountry": "RU"},
     "geo": {"@type": "GeoCoordinates", "latitude": 59.9486, "longitude": 30.2549},
     "areaServed": {"@type": "City", "name": "Санкт-Петербург"},
     "openingHoursSpecification": {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], "opens": "09:00", "closes": "21:00"},
     "sameAs": ["https://wa.me/79119371888", "https://t.me/"]},
    {"@type": "FAQPage", "@id": URL + "#faq",
     "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs_ld]},
]}
ld_json = json.dumps(ld, ensure_ascii=False)

base_css = """*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:Manrope,system-ui,sans-serif;color:#0A0B0D;background:#fff;-webkit-font-smoothing:antialiased;overflow-x:hidden}
img,video{max-width:100%}
.cat-track{scrollbar-width:none}
.cat-track::-webkit-scrollbar{display:none}
@media(max-width:760px){.cat-prev,.cat-next{display:none!important}.car-card{flex:0 0 84%!important}}
"""

JS = """
(function(){
  // карусель каталога
  var track=document.querySelector('.cat-track');
  function carStep(){var c=track&&track.querySelector('.car-card');return c?c.getBoundingClientRect().width+24:340;}
  var pv=document.querySelector('.cat-prev'), nx=document.querySelector('.cat-next');
  if(pv)pv.addEventListener('click',function(){track.scrollLeft-=carStep();});
  if(nx)nx.addEventListener('click',function(){track.scrollLeft+=carStep();});
  // аккордеон FAQ
  document.querySelectorAll('.faq-q').forEach(function(b){b.addEventListener('click',function(){
    var wrap=b.parentElement, ans=wrap.querySelector('.faq-a'), open=ans.style.display!=='none';
    wrap.parentElement.querySelectorAll('.faq-a').forEach(function(a){a.style.display='none';});
    wrap.parentElement.querySelectorAll('.faq-chev-up').forEach(function(s){s.style.display='none';});
    wrap.parentElement.querySelectorAll('.faq-chev-down').forEach(function(s){s.style.display='';});
    if(!open){ans.style.display='';b.querySelector('.faq-chev-down').style.display='none';b.querySelector('.faq-chev-up').style.display='';}
    applyLang();
  });});
  // FAB
  var fabBtn=document.querySelector('[data-act="fab"]'), fabItems=document.querySelector('.fab-items'), fabX=document.querySelector('.fab-x'), fabPhone=fabBtn&&fabBtn.querySelector('svg:not(.fab-x)');
  function fabToggle(){var open=fabItems.style.display!=='none';fabItems.style.display=open?'none':'';if(fabX)fabX.style.display=open?'none':'';if(fabPhone)fabPhone.style.display=open?'':'none';}
  if(fabBtn)fabBtn.addEventListener('click',fabToggle);
  // CTA "contact" -> открыть FAB
  document.querySelectorAll('[data-act="contact"]').forEach(function(el){el.addEventListener('click',function(e){e.preventDefault();if(fabItems&&fabItems.style.display==='none')fabToggle();window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'});});});
  // i18n
  var EN=__EN__, lang='ru';
  function applyLang(){
    var en=lang==='en';
    var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),n,b=[];
    while(n=w.nextNode())b.push(n);
    b.forEach(function(tn){if(en){var k=tn.nodeValue.trim();if(k&&EN[k]&&!tn.__t){tn.__o=tn.nodeValue;tn.nodeValue=tn.nodeValue.replace(k,EN[k]);tn.__t=1;}}else if(tn.__t){tn.nodeValue=tn.__o;tn.__t=0;}});
    document.querySelectorAll('[placeholder]').forEach(function(el){if(en){var k=el.getAttribute('placeholder');if(EN[k]&&!el.__t){el.__o=k;el.setAttribute('placeholder',EN[k]);el.__t=1;}}else if(el.__t){el.setAttribute('placeholder',el.__o);el.__t=0;}});
  }
  window.applyLang=applyLang;
  document.querySelectorAll('.lang-btn').forEach(function(b){b.addEventListener('click',function(){
    lang=b.dataset.lang;
    document.querySelectorAll('.lang-btn').forEach(function(x){x.classList.remove('is-active');x.style.background='none';x.style.color='#6E7378';x.style.boxShadow='none';});
    b.classList.add('is-active');b.style.background='#fff';b.style.color='#0A0B0D';b.style.boxShadow='0 1px 3px rgba(0,0,0,0.1)';
    applyLang();
  });});
})();
""".replace('__EN__', EN_JSON)

html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{URL}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="ЭкоРент">
<meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{URL}og-image.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{URL}og-image.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Montserrat:wght@600;700;800&display=swap" rel="stylesheet">
<script type="application/ld+json">{ld_json}</script>
<style>
{base_css}
{chr(10).join(hover_css)}
</style>
{styles}
</head>
<body>
{body}
<script>{JS}</script>
</body>
</html>
"""
open(OUT, "w", encoding="utf-8").write(html)
print(f"OK: {OUT} собран ({len(html)//1024} КБ). Авто: {len(CARS)}, FAQ: {len(faqs)}, hover-правил: {len(hover_css)}")
