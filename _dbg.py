# -*- coding: utf-8 -*-
import re, os
NAO='Nao Organizados'
FOR=os.path.join(NAO,'Shin-DendoNoTebiki_ForSite.md')
PAGE=re.compile(r'^\**\\?\[P[áa]g\.?\s*(\d+)\\?\]\**\s*$')
HEAD=re.compile(r'^#{1,6}\s+(.*?)\s*$')
JPAR=re.compile(r'[(（][^)）]*[぀-鿿][^)）]*[)）]')
CIT=re.compile(r'[(（][^)）]*(p[áa]g|col\.|vol|se[çc]|linha)[^)）]*[)）]',re.I)
def norm(s):
    s=re.sub(r'\\(.)',r'\1',s)
    s=re.sub(r'\s*\[(Explicação|Notas|Trecho|Resumo)\b.*$','',s)
    s=JPAR.sub('',s); s=CIT.sub('',s)
    s=s.lower().replace('.',' ')
    s=re.sub(r'["“”,;:]',' ',s)
    return re.sub(r'\s+',' ',s).strip()
# index ForSite
idx=[]; cur=None
for ln in open(FOR,encoding='utf-8').read().split('\n'):
    m=PAGE.match(ln.strip())
    if m: cur=int(m.group(1)); continue
    h=HEAD.match(ln)
    if h and cur is not None:
        k=norm(h.group(1))
        if k: idx.append((k,cur))
# C2_Item04 headings
md=open('ShinDendo_C2_Item04.md',encoding='utf-8').read().split('\n')
heads=[norm(HEAD.match(l).group(1)) for l in md if HEAD.match(l)]
print('=== C2_Item04: cada heading -> existe no indice ForSite? (com pagina) ===')
fdict={}
for k,p in idx:
    fdict.setdefault(k,[]).append(p)
for k in heads:
    pgs=fdict.get(k)
    print(('  OK  ' if pgs else '  --  ')+k[:55]+('  pág '+str(pgs) if pgs else ''))
