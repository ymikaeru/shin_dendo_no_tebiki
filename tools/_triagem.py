# -*- coding: utf-8 -*-
"""Triagem de TIPAGEM (book-wide): conservacao=0 garante que nada se perdeu, mas
conteudo editorial (epigrafe/salmo/lista-de-referencia/resumo/fragmento-JP) pode
estar em ensinamento.texto como se fosse fala de Meishu-Sama. Classifica TODOS os
nos com ensinamento (folha E pai), nao so os intros."""
import json, re
from collections import Counter

b = json.load(open('shin-dendo-tebiki.json', encoding='utf-8'))
idx = {}
def walk(n):
    idx[n['id']] = n
    for c in n.get('children', []):
        walk(c)
for s in b['sections']:
    walk(s)

REF    = re.compile(r'artigos de refer|artigos relacionad|ensinamentos? de refer|artigos? de consulta', re.I)
RESUMO = re.compile(r'pode-se resumir|pontos principais|estes são os pontos|resumir nestes', re.I)
SALMO  = re.compile(r'\bsalmo\b|gyoei|御詠|coletânea de salmos', re.I)
CJK    = re.compile(r'[぀-ヿ一-鿿]')

def is_jp_fragment(txt):
    t = txt.strip().strip('()').strip()
    if not t:
        return False
    cjk = len(CJK.findall(t))
    return cjk >= 3 and cjk >= len(re.sub(r'\s', '', t)) * 0.5

def classify(n):
    e = n['ensinamento']
    title = n.get('title', '')
    texto = e.get('texto') or ''
    blob = title + ' ' + texto + ' ' + ' '.join(a.get('texto', '') for a in e.get('anexo', []))
    if texto and is_jp_fragment(texto):  return 'fragmento-JP'
    if REF.search(blob):                 return 'lista-referencia'
    if RESUMO.search(blob):              return 'resumo'
    if SALMO.search(title) or SALMO.search(texto): return 'salmo/epigrafe'
    if texto:                            return 'prosa (quote)'
    if e.get('explicacao'):              return 'so-explicacao'
    if e.get('fonte') or e.get('anexo'): return 'so-fonte/anexo'
    return 'vazio'

leaf_cnt, parent_cnt = Counter(), Counter()
flagged = {'lista-referencia': [], 'resumo': [], 'fragmento-JP': [], 'so-fonte/anexo': []}
for id_, n in idx.items():
    if not n.get('ensinamento'):
        continue
    t = classify(n)
    (parent_cnt if n.get('children') else leaf_cnt)[t] += 1
    if t in flagged:
        flagged[t].append(id_)

print('=== TIPAGEM de TODOS os nos com ensinamento (folha | pai-intro) ===')
keys = sorted(set(leaf_cnt) | set(parent_cnt))
print('  %-18s %6s %6s' % ('tipo', 'folha', 'pai'))
for k in keys:
    print('  %-18s %6d %6d' % (k, leaf_cnt.get(k, 0), parent_cnt.get(k, 0)))
print('  %-18s %6d %6d' % ('TOTAL', sum(leaf_cnt.values()), sum(parent_cnt.values())))

print('\n=== nos a decidir campo dedicado / limpar ===')
for k in ('lista-referencia', 'resumo', 'fragmento-JP', 'so-fonte/anexo'):
    print('  %-16s (%d): %s' % (k, len(flagged[k]), ', '.join(sorted(flagged[k]))))
