# -*- coding: utf-8 -*-
"""Extrai a HIERARQUIA dos 8 .md (árvore de navegação, até 9 níveis) -> _tree.json.
Reaproveita a classificação por marcador; pega a página de _editor_map.json.
Nó = {id, nivel, marcador, title, pagina, children}."""
import re, json, glob, os, collections

CIRCLED = {chr(c): i + 1 for i, c in enumerate(range(0x2460, 0x2474))}
ROMAN_UP = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX']
ROMAN_LO = [r.lower() for r in ROMAN_UP]
HEAD = re.compile(r'^(#{1,6})[ \t]*(.*?)[ \t]*$')
RANK = {'Parte':2,'Numero':3,'Circulo':4,'romano':5,'Letra':6,'letra':7}
NIVEL_PT = {'Parte':'parte','Numero':'numero','Circulo':'circulo','romano':'romano','Letra':'letra','letra':'letra_min'}

def strip_emph(s):
    s = s.strip(); s = re.sub(r'^[\*\\\s]+','',s); s = re.sub(r'[\*\\\s]+$','',s)
    return s.strip()

def classify(raw, fhp):
    t = strip_emph(raw)
    if not t: return ('VAZIO','','')
    if re.match(r'^Cap[íi]tulo\b',t): return ('Capitulo','',t)
    if re.match(r'^Item\b',t): return ('Item','',t)
    if t[0] in CIRCLED: return ('Circulo',str(CIRCLED[t[0]]),t[1:].strip())
    m = re.match(r'^([A-Za-z]+|\d+)\\?\.?[ \t)]',t+' ')
    if not m: return (None,None,t)
    tok = m.group(1); rest = t[m.end()-1:].strip()
    if tok.isdigit(): return ('Numero',tok,rest)
    low = tok.lower()
    if tok in ROMAN_UP and fhp: return ('Parte',tok,rest)
    if len(tok)>1 and tok in ROMAN_UP: return ('Parte',tok,rest)
    # romano de uma letra só em MINÚSCULA (i. v. x.); "I." maiúsculo sem Parte no arquivo é a 9ª Letra (…H, I, J)
    if low in ROMAN_LO and (len(low)>1 or tok in ('i','v','x')): return ('romano',low,rest)
    if len(tok)==1: return ('Letra' if tok.isupper() else 'letra', tok, rest)
    return (None,None,t)

# páginas: {arquivo: {titulo_normalizado: pag}}
PAGES = {}
if os.path.exists('_editor_map.json'):
    for fn, secs in json.load(open('_editor_map.json', encoding='utf-8')).items():
        PAGES[fn] = {}
        for k, v in secs.items():
            if isinstance(v, dict):
                PAGES[fn][k] = v.get('pag')

def page_of(fn, raw_after_hash):
    key = re.sub(r'\\(.)', r'\1', raw_after_hash).strip()
    return PAGES.get(fn, {}).get(key)

book = {'id':'shin-dendo','title':'Novo Manual de Difusão','titleJa':'新・伝道の手引き','children':[]}
caps = {}
stats = collections.Counter()

for f in sorted(glob.glob('ShinDendo_*.md')):
    fn = os.path.basename(f)
    mm = re.match(r'ShinDendo_C(\d)_Item(\d+)\.md', fn)
    capn, itemn = mm.group(1), str(int(mm.group(2)))
    if capn not in caps:
        caps[capn] = {'id':'c'+capn,'nivel':'capitulo','marcador':'Capítulo '+capn,'title':'','children':[]}
        book['children'].append(caps[capn])
    cap = caps[capn]
    lines = open(f, encoding='utf-8').read().split('\n')
    # acha se tem Parte real (existe 'II')
    fhp = any(HEAD.match(l) and strip_emph(HEAD.match(l).group(2)).split(' ')[0].rstrip('\\.')=='II' for l in lines)
    item = {'id':'%s.i%s'%(cap['id'],itemn),'nivel':'item','marcador':'Item '+itemn,
            'title':'','pagina':None,'children':[]}
    cap['children'].append(item)
    stack = [(1, item)]
    for l in lines:
        hm = HEAD.match(l)
        if not hm: continue
        nivel, marc, resto = classify(hm.group(2), fhp)
        if nivel == 'Capitulo':
            t = re.sub(r'\\(.)',r'\1',resto).split('(')[0].strip()
            cap['title'] = re.sub(r'^Cap[íi]tulo\s*\d+\W*','',t).strip(); continue
        if nivel == 'Item':
            t = re.sub(r'\\(.)',r'\1',resto).split('(')[0].strip()
            item['title'] = re.sub(r'^Item\s*\d+\W*','',t).strip()
            item['pagina'] = page_of(fn, hm.group(2)); continue
        if nivel in (None,'VAZIO'): continue
        rank = RANK[nivel]
        while len(stack) > 1 and stack[-1][0] >= rank: stack.pop()
        parent = stack[-1][1]
        title = re.sub(r'\\(.)',r'\1',resto).strip()
        node = {'id':parent['id']+'.'+marc,'nivel':NIVEL_PT[nivel],'marcador':marc,
                'title':title,'pagina':page_of(fn,hm.group(2)),'children':[]}
        parent['children'].append(node)
        stack.append((rank, node))
        stats[NIVEL_PT[nivel]] += 1

json.dump(book, open('_tree.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)

def depth(n, d=1): return max([depth(c,d+1) for c in n['children']], default=d)
def count(n): return 1 + sum(count(c) for c in n['children'])
print('Árvore gravada em _tree.json')
print('  total de nós:', count(book)-1, '| profundidade máx:', depth(book))
print('  por nível:', dict(stats))
print('\n  Capítulos/Itens:')
for c in book['children']:
    for it in c['children']:
        print('   %-6s %-32s %d sub-nós, pág %s' % (it['id'], (it['title'][:30]), count(it)-1, it['pagina']))
