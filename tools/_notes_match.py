# -*- coding: utf-8 -*-
"""Casamento de notas por ÂNCORA (não por hierarquia). Parseia blocos [Notas] do
_ForSite em trios (âncora, N, texto) e casa cada bloco ao ensinamento do JSON cujo
texto contém as âncoras. Robusto à hierarquia bagunçada das fontes.
Uso: python _notes_match.py [c1.i1]"""
import re, json, os, sys, unicodedata

NAO = 'Nao Organizados'
PT = os.path.join(NAO, 'Shin-DendoNoTebiki_ForSite.md')
def unesc(s): return re.sub(r'\\(.)', r'\1', s or '')

def norm(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^a-z0-9 ]', ' ', s.lower())
    return re.sub(r'\s+', ' ', s).strip()

NOTE_TXT = re.compile(r'\*?(\d+)\s+(.+?\(Livro\s*p[áa]g\.?\s*\d+\)\.)', re.S)

def parse_block(txt):
    """[Notas] cru -> [{n, anchor, text}]. anchor = frase antes do número."""
    t = re.sub(r'^\s*Nota:?\s*', '', unesc(txt)).strip()
    notes, last = [], 0
    for m in NOTE_TXT.finditer(t):
        anchor = t[last:m.start()].strip().strip('*').strip()
        notes.append({'n': int(m.group(1)), 'anchor': anchor,
                      'text': re.sub(r'\s+', ' ', m.group(2)).strip()})
        last = m.end()
    return notes

def all_blocks(path):
    """Todos os blocos [Notas] (crus), em ordem, exceto marcadores de página."""
    out = []
    for ln in open(path, encoding='utf-8').read().split('\n'):
        if '[Notas' in ln and not re.search(r'\[P[áa]g', ln):
            body = re.sub(r'.*?\[Notas\\?\]\**\s*', '', unesc(ln)).strip()
            if body and NOTE_TXT.search(body):
                out.append(body)
    return out

# --- JSON: ensinamentos de c1.i1 com texto pesquisável ---
b = json.load(open('shin-dendo-tebiki.json', encoding='utf-8'))
idx = {}
def w(n):
    idx[n['id']] = n
    [w(c) for c in n.get('children', [])]
[w(s) for s in b['sections']]

def searchable(n):
    e = n.get('ensinamento') or {}
    parts = [n.get('title', '')] + [str(e.get(k) or '') for k in ('texto', 'preambulo', 'explicacao', 'posfacio')]
    parts += [a.get('texto', '') for a in e.get('anexo', [])]
    return norm(' '.join(parts))

want = sys.argv[1] if len(sys.argv) > 1 else 'c1.i1'
teach = {id_: searchable(n) for id_, n in idx.items() if id_.startswith(want + '.') or id_ == want}

def best_match(block_notes):
    """Ensinamento com maior fração de âncoras presentes."""
    best, score = None, 0.0
    for id_, txt in teach.items():
        anchors = [norm(nt['anchor']) for nt in block_notes if len(norm(nt['anchor'])) >= 4]
        if not anchors: continue
        hit = sum(1 for a in anchors if a in txt)
        frac = hit / len(anchors)
        if frac > score or (frac == score and best and len(id_) < len(best)):
            best, score = id_, frac
    return best, score

print('=== Casamento por âncora — blocos PT de %s ===' % want)
for raw in all_blocks(PT):
    notes = parse_block(raw)
    if not notes: continue
    m, sc = best_match(notes)
    if not m: continue
    if not (m.startswith(want + '.') or m == want): continue   # só os que casam em c1.i1
    print('\n→ %s  (confiança %.0f%%, %d notas)  título: %r' % (m, sc*100, len(notes), idx[m]['title'][:38]))
    for nt in notes:
        print('   [%d] âncora=%r' % (nt['n'], nt['anchor'][:30]))
        print('        %s' % nt['text'][:90])
