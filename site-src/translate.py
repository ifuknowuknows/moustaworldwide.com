"""English decides. Re-translates only the English texts that changed since the last run.

Runs in the GitHub Action before build.py. Needs the repository secret DEEPL_API_KEY
(DeepL API Free or Pro). Without it, nothing is translated and the old translations stay.

- Keys listed in dnt.json are copied from English unchanged (names, brand lines).
- Brand lines inside a text are kept in English (PROTECT below).
- A translation is replaced only when its English text changed, so native-review fixes
  survive until you change that English line.
- Startups are matched by name; a new startup is translated, a removed one is dropped.
"""
import hashlib, json, os, re, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
KEY = os.environ.get('DEEPL_API_KEY', '').strip()
LANGS = {'da': 'DA', 'es': 'ES', 'pt': 'PT-BR', 'sv': 'SV', 'fr': 'FR', 'id': 'ID', 'ar': 'AR'}
PROTECT = ['Perspective is everything.', 'perspective is everything', 'Same same, but different.',
           'moustaworldwide', 'Mousta M. Moustafa', 'Chapters Institute', 'siwi', 'siwa life management',
           "You're Not a F*cking Expat", 'Substack', 'Instagram', 'TikTok', 'Threads', 'Snapchat',
           'Ethnologue', 'TEDx']
STATE = 'translation-state.json'

def h(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:12]

def protect(s):
    for p in sorted(PROTECT, key=len, reverse=True):
        s = s.replace(p, '<span translate="no">%s</span>' % p)
    return s

def unprotect(s):
    return re.sub(r'<span translate="no">(.*?)</span>', r'\1', s)

def deepl(texts, target):
    url = 'https://api-free.deepl.com/v2/translate' if KEY.endswith(':fx') else 'https://api.deepl.com/v2/translate'
    out = []
    for i in range(0, len(texts), 40):
        chunk = texts[i:i + 40]
        data = [('target_lang', target), ('source_lang', 'EN'), ('tag_handling', 'html'), ('preserve_formatting', '1')]
        data += [('text', protect(t)) for t in chunk]
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                     headers={'Authorization': 'DeepL-Auth-Key ' + KEY})
        res = json.load(urllib.request.urlopen(req, timeout=60))
        out += [unprotect(x['text']) for x in res['translations']]
    return out

def main():
    en = json.load(open('en.json'))
    dnt = set(json.load(open('dnt.json')))
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    if not KEY:
        print('DEEPL_API_KEY not set: translations left as they are.')
        return
    changed_any = False
    for code, target in LANGS.items():
        path = code + '.json'
        tr = json.load(open(path))
        st = state.setdefault(code, {})
        todo = []  # (setter, english)
        # flat keys
        for k, v in en.items():
            if k == 'ventures' or not isinstance(v, str):
                continue
            if k in dnt:
                if tr.get(k) != v:
                    tr[k] = v; changed_any = True
                continue
            if st.get(k) == h(v) and k in tr:
                continue
            if k not in st and k in tr:  # first run: trust the existing (native-reviewed) text
                st[k] = h(v); continue
            todo.append((('key', k), v))
        # startups, matched by name
        tv = tr.get('ventures') if isinstance(tr.get('ventures'), dict) else {}
        names = [v.get('name', '') for v in en.get('ventures', []) if v.get('name')]
        for v in en.get('ventures', []):
            n = v.get('name', '')
            if not n:
                continue
            item = tv.setdefault(n, {})
            for f in ('text', 'status'):
                src = v.get(f, '') or ''
                sk = 'ventures/%s/%s' % (n, f)
                if not src:
                    item.pop(f, None); continue
                if st.get(sk) == h(src) and f in item:
                    continue
                if sk not in st and f in item:
                    st[sk] = h(src); continue
                todo.append((('venture', n, f), src))
        for n in list(tv):
            if n not in names:
                del tv[n]; changed_any = True
        tr['ventures'] = tv
        if todo:
            res = deepl([e for _, e in todo], target)
            for (where, src), out in zip(todo, res):
                if where[0] == 'key':
                    tr[where[1]] = out; st[where[1]] = h(src)
                else:
                    tv[where[1]][where[2]] = out; st['ventures/%s/%s' % (where[1], where[2])] = h(src)
            changed_any = True
            print('%s: %d texts translated' % (code, len(todo)))
        json.dump(tr, open(path, 'w'), ensure_ascii=False, indent=1)
    json.dump(state, open(STATE, 'w'), ensure_ascii=False, indent=1)
    print('done' if changed_any else 'nothing to translate')

if __name__ == '__main__':
    main()
