# -*- coding: utf-8 -*-
"""Mapa de paginas para o editor. Alinha (em ordem) os titulos dos .md limpos com
o PT desorganizado, le a [Pag. N], interpola faltantes, converte pagina->imagem
(img=pag//2+21) e grava os pins. Usa o _Traduzido e, p/ arquivos que ele nao cobre,
cai no _ForSite.  Modo relatorio; --write grava _editor_map.json."""
import re, json, glob, os, sys

NAO = 'Nao Organizados'
SOURCES = [os.path.join(NAO, 'Shin-DendoNoTebiki_Traduzido.md'),
           os.path.join(NAO, 'Shin-DendoNoTebiki_ForSite.md')]
PAGE = re.compile(r'^\**\\?\[P[áa]g\.?\s*(\d+)\\?\]\**\s*$')      # [Pág. N] ou **[Pág. N]**
HEAD = re.compile(r'^#{1,6}\s+(.*?)\s*$')
JPAR = re.compile(r'[(（][^)）]*[぀-鿿][^)）]*[)）]')
CIT  = re.compile(r'[(（][^)）]*(p[áa]g|col\.|vol|se[çc]|linha)[^)）]*[)）]', re.I)

def norm(s):
    s = re.sub(r'\\(.)', r'\1', s)
    s = re.sub(r'\s*\[(Explicação|Notas|Trecho|Resumo)\b.*$', '', s)   # corta run-on editorial grudado
    s = JPAR.sub('', s); s = CIT.sub('', s)
    s = s.lower().replace('.', ' ')
    s = re.sub(r'["“”,;:]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def index(path):
    """[Pág. N] marca o FIM da pág N, entao cada titulo recebe a pagina do PROXIMO marcador."""
    out, pend = [], []
    for ln in open(path, encoding='utf-8').read().split('\n'):
        m = PAGE.match(ln.strip())
        if m:
            n = int(m.group(1))
            for k in pend:
                out.append((k, n))
            pend = []
            continue
        h = HEAD.match(ln)
        if h:
            k = norm(h.group(1))
            if k:
                pend.append(k)
    return out

IDX = {p: index(p) for p in SOURCES}
def page_to_img(p): return p // 2 + 21

def align(heads, trad):
    """heads: [(line, key)]. 1o casamento busca a fonte inteira (acha a regiao do arquivo);
    depois de ancorado, janela curta forward."""
    ti = 0; res = []; anchored = False
    for (_, k) in heads:
        found = None
        hi = len(trad) if not anchored else min(len(trad), ti + 90)
        for j in range(ti, hi):
            if trad[j][0] == k:
                found = trad[j][1]; ti = j + 1; anchored = True; break
        res.append(found)
    return res

def interp(heads, pages):
    known = [(heads[i][0], pages[i]) for i in range(len(heads)) if pages[i] is not None]
    out = []
    for (line, _) in heads:
        if not known:
            out.append(None); continue
        if line <= known[0][0]: out.append(known[0][1]); continue
        if line >= known[-1][0]: out.append(known[-1][1]); continue
        v = known[-1][1]
        for a in range(len(known) - 1):
            (l1, p1), (l2, p2) = known[a], known[a + 1]
            if l1 <= line <= l2:
                v = round(p1 + (p2 - p1) * (line - l1) / max(1, l2 - l1)); break
        out.append(v)
    return out

mapping, report = {}, []
for f in sorted(glob.glob('ShinDendo_*.md')):
    name = os.path.basename(f)
    lines = open(f, encoding='utf-8').read().split('\n')
    heads = [(i, norm(HEAD.match(ln).group(1)), re.sub(r'\\(.)', r'\1', HEAD.match(ln).group(1)))
             for i, ln in enumerate(lines) if HEAD.match(ln)]
    hk = [(i, k) for (i, k, _) in heads]
    # combina as duas fontes (Traduzido preferido; ForSite preenche lacunas)
    pa = [align(hk, IDX[s]) for s in SOURCES]
    pages = [next((pa[s][i] for s in range(len(SOURCES)) if pa[s][i] is not None), None)
             for i in range(len(hk))]
    nmatch = sum(1 for p in pages if p is not None)
    # filtro monotonico: descarta ancoras que quebram a ordem crescente das paginas
    last = -1
    for i in range(len(pages)):
        if pages[i] is not None:
            if pages[i] < last:
                pages[i] = None
            else:
                last = pages[i]
    pages = interp(hk, pages)
    fm = {key: {'img': page_to_img(p), 'pag': p} for (i, _, key), p in zip(heads, pages) if p is not None}
    if fm:
        mapping[name] = fm
        ps = [p for p in pages if p]
        report.append((name, 'T+F', nmatch, len(heads), min(ps), max(ps)))

print('%-22s fonte     casados/tot   pág' % 'arquivo')
for (n, src, nm, tot, a, b) in report:
    print('  %-20s %-9s %3d/%-3d      %d–%d (img %d–%d)' % (n[10:], src, nm, tot, a, b, page_to_img(a), page_to_img(b)))
print('\ntotal pins:', sum(len(v) for v in mapping.values()), '| arquivos cobertos:', len(mapping), '/ 8')

if '--write' in sys.argv:
    old = json.load(open('_editor_map.json', encoding='utf-8')) if os.path.exists('_editor_map.json') else {}
    for n, fm in mapping.items():
        old.setdefault(n, {}).update(fm)
    json.dump(old, open('_editor_map.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n>>> _editor_map.json gravado.')
else:
    print('\n(relatorio; use --write para gravar)')
