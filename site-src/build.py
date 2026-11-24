import json, re, os, sys, html as H
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
tpl = open('template.html').read()
en = json.load(open('en.json'))
LANGS = [('en', 'English'), ('da', 'Dansk'), ('es', 'Español'), ('pt', 'Português'), ('sv', 'Svenska'),
         ('fr', 'Français'), ('id', 'Bahasa Indonesia'), ('ar', 'العربية')]
JS = {  # copied, selected, date locale
    'en': ('Copied', 'Selected, press copy', 'en-GB'),
    'da': ('Kopieret', 'Markeret, tryk kopiér', 'da-DK'),
    'es': ('Copiado', 'Seleccionado, pulsa copiar', 'es-ES'),
    'pt': ('Copiado', 'Selecionado, toque em copiar', 'pt-BR'),
    'sv': ('Kopierat', 'Markerat, tryck kopiera', 'sv-SE'),
    'fr': ('Copié', 'Sélectionné, appuyez sur copier', 'fr-FR'),
    'id': ('Disalin', 'Sudah dipilih, tekan salin', 'id-ID'),
    'ar': ('تم النسخ', 'تم التحديد، اضغط نسخ', 'ar-EG'),
}
SITE = 'https://www.moustaworldwide.com'
def url(code): return '/' if code == 'en' else '/' + code

def ventures(code, t):
    rows = []
    tr = t['ventures'] if code != 'en' and isinstance(t.get('ventures'), dict) else {}
    for v in en['ventures']:
        name = v.get('name', '').strip()
        if not name:
            continue
        loc = tr.get(name, {})
        shown = loc.get('name') or name
        text = loc.get('text') or v.get('text', '')
        status = loc.get('status') or v.get('status', '')
        link = (v.get('link') or '').strip()
        inner = ('<div><h3 class="title-2">%s</h3><p class="caption-2">%s</p></div><span class="s caption-2">%s</span>'
                 % (H.escape(shown, quote=False), H.escape(text, quote=False), H.escape(status, quote=False)))
        if link:
            rows.append('<a class="row" href="%s" rel="noopener" target="_blank">%s</a>' % (H.escape(link, quote=True), inner))
        else:
            rows.append('<div class="row">%s</div>' % inner)
    return '\n'.join(rows)

def build(code):
    t = dict(en)
    if code != 'en':
        t.update(json.load(open(code + '.json')))
    html = tpl
    html = html.replace('{{VENTURES}}', ventures(code, t))
    for k, v in t.items():
        if isinstance(v, str):
            html = html.replace('{{%s}}' % k, v)
    left = re.findall(r'\{\{(\w+)\}\}', html)
    assert not left, (code, left)
    # html lang/dir
    html = html.replace('<html lang="en">', '<html lang="%s"%s>' % (code, ' dir="rtl"' if code == 'ar' else ''), 1)
    # absolute asset paths (pages live at /da etc.)
    html = html.replace('src="mousta.webp"', 'src="/mousta.webp"').replace('fetch("writing.json?"', 'fetch("/writing.json?"')
    # js strings
    c, s, loc = JS[code]
    html = html.replace('b.textContent="Copied"', 'b.textContent=%s' % json.dumps(c, ensure_ascii=False))
    html = html.replace('b.textContent="Selected, press copy"', 'b.textContent=%s' % json.dumps(s, ensure_ascii=False))
    html = html.replace('b.textContent="Copy bio"', 'b.textContent=%s' % json.dumps(t['k076'], ensure_ascii=False))
    html = html.replace('toLocaleDateString("en-GB"', 'toLocaleDateString("%s"' % loc)
    # hreflang + canonical
    alts = ''.join('<link rel="alternate" hreflang="%s" href="%s%s">' % (l, SITE, url(l)) for l, _ in LANGS)
    alts += '<link rel="alternate" hreflang="x-default" href="%s/">' % SITE
    alts += '<link rel="canonical" href="%s%s">' % (SITE, url(code))
    html = html.replace('<title>', alts + '<title>', 1)
    # language switcher (in header, after nav)
    opts = ''.join('<a href="%s" lang="%s" data-l="%s"%s>%s</a>' % (url(l), l, l, ' aria-current="true"' if l == code else '', name) for l, name in LANGS)
    cur = dict(LANGS)[code]
    sw = ('<details class="lang"><summary aria-label="Language">%s</summary><div class="menu">%s</div></details>'
          % (code.upper() if code != 'ar' else 'ع', opts))
    html = html.replace('<nav', '<div class="right"><nav', 1).replace('</nav>', '</nav>' + sw + '</div>', 1)
    # remember choice when a language is picked
    remember = ('<script>document.querySelectorAll(".lang a").forEach(function(a){a.addEventListener("click",function(){try{localStorage.setItem("lang",a.dataset.l)}catch(e){}})});'
                'document.addEventListener("click",function(e){var d=document.querySelector(".lang");if(d&&d.open&&!d.contains(e.target))d.open=false});</script>')
    if code == 'en':
        # first visit only: send visitors whose browser language is one of Mousta's languages to that version
        remember = ('<script>(function(){try{if(localStorage.getItem("lang"))return}catch(e){}'
                    'var L=["da","es","pt","sv","fr","id","ar"],n=(navigator.languages||[navigator.language||""]);'
                    'for(var i=0;i<n.length;i++){var c=(n[i]||"").slice(0,2).toLowerCase();if(c==="en")return;if(c==="nb"||c==="no")c="da";if(L.indexOf(c)>-1){location.replace("/"+c+location.hash);return}}})();</script>') + remember
        html = html.replace('<title>', remember.split('</script>')[0] + '</script><title>', 1)
        remember = '<script>' + remember.split('</script>', 1)[1].split('<script>', 1)[1]
    html = html.replace('</body>', remember + '</body>', 1)
    css = ('.lang{position:relative}.lang summary{list-style:none;cursor:pointer;font-size:14px;line-height:20px;font-weight:500;color:var(--soft);'
           'border:1px solid var(--line);border-radius:9999px;padding:4px 12px;user-select:none;transition:color .3s var(--ease)}.lang summary::-webkit-details-marker{display:none}'
           '.lang summary:hover{color:var(--ink)}.lang .menu{position:absolute;right:0;top:calc(100% + 12px);background:var(--bg);border:1px solid var(--line);'
           'border-radius:16px;padding:8px;display:flex;flex-direction:column;min-width:192px;z-index:40}'
           '.lang .menu a{padding:8px 12px;border-radius:8px;text-decoration:none;font-size:14px;line-height:20px;color:var(--ink);transition:background-color .3s var(--ease)}'
           '.lang .menu a:hover,.lang .menu a[aria-current]{background:var(--alt)}')
    if code == 'ar':
        css += ('[dir=rtl] *{letter-spacing:0!important}[dir=rtl] body{font-family:"Noto Sans Arabic","Geeza Pro","Segoe UI",Tahoma,sans-serif}'
                '[dir=rtl] .lang .menu{right:auto;left:0}[dir=rtl] .arr{transform:scaleX(-1)}[dir=rtl] .tlink:hover .arr{transform:scaleX(-1) translateX(4px)}'
                '[dir=rtl] .panel .close-row{right:auto;left:24px}')
    html = html.replace('</style>', css + '\n</style>', 1)
    return html

out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
os.makedirs(out, exist_ok=True)
for code, _ in LANGS:
    if code != 'en' and not os.path.exists(code + '.json'):
        print('missing', code); continue
    name = 'index.html' if code == 'en' else code + '.html'
    open(os.path.join(out, name), 'w').write(build(code))
    print('built', name)
