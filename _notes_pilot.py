# -*- coding: utf-8 -*-
"""UNIÃO de notas PT (_ForSite) + JP (OCR) por caminho de hierarquia, p/ medir
cobertura real e extrair as notas. Reusa classify() do _build_book.
Uso: python _notes_pilot.py [c1.i1]   (default c1.i1)"""
import re, os, sys
import _build_book as B

NAO = 'Nao Organizados'
PT = os.path.join(NAO, 'Shin-DendoNoTebiki_ForSite.md')
JP = os.path.join(NAO, '新・伝道の手引き_OCR.md')
JNUM = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}

def jp_capitulo(t):
    m = re.match(r'第([一二三四五六七八九十])章', t)
    return JNUM.get(m.group(1)) if m else None
def jp_item(t):
    m = re.match(r'([一二三四五六七八九十])項', t)
    return JNUM.get(m.group(1)) if m else None

def extract(path, jp):
    """Devolve {caminho c{c}.i{i}.{...}: [blocos_notas_crus]} do arquivo."""
    lines = open(path, encoding='utf-8').read().split('\n')
    fhp = any(B.HEAD.match(l) and B.strip_emph(B.HEAD.match(l).group(2)).split(' ')[0].rstrip('\\.') == 'II' for l in lines)
    cap = item = None
    stack = []                      # (rank, marc) abaixo do item
    notes = {}
    def cur():
        if not (cap and item): return None
        p = 'c%s.i%s' % (cap, item)
        for (_, m) in stack: p += '.' + m
        return p
    PAG = re.compile(r'\[P[áa]g')
    for ln in lines:
        hm = B.HEAD.match(ln)
        if hm:
            raw = hm.group(2); t = B.strip_emph(raw)
            # capítulo / item (PT ou JP)
            cnum = (re.match(r'Cap[íi]tulo\s*(\d)', t) and re.match(r'Cap[íi]tulo\s*(\d)', t).group(1)) or jp_capitulo(t)
            if cnum: cap = str(cnum); item = None; stack = []; continue
            inum = (re.match(r'Item\s*(\d+)', t) and re.match(r'Item\s*(\d+)', t).group(1)) or jp_item(t)
            if inum: item = str(int(inum)); stack = []; continue
            nivel, marc, _ = B.classify(raw, fhp)
            if nivel in (None, 'VAZIO', 'Capitulo', 'Item'): continue
            rank = B.RANK[nivel]
            while stack and stack[-1][0] >= rank: stack.pop()
            stack.append((rank, marc))
            continue
        # bloco de notas?
        if '[Notas' in ln or '\\[Notas' in ln:
            if PAG.search(ln): continue                    # marcador de página, não nota
            if jp and '註' not in ln: continue             # JP: só linhas com 註
            p = cur()
            if p:
                body = re.sub(r'.*?\[Notas\\?\]\s*', '', B.unesc(ln)).strip()
                body = re.sub(r'^註\s*', '', body)
                if body: notes.setdefault(p, []).append(body)
    return notes

def main():
    want = (sys.argv[1] if len(sys.argv) > 1 else 'c1.i1')
    pt = extract(PT, jp=False)
    jp = extract(JP, jp=True)
    keys = sorted(set(k for k in (set(pt) | set(jp)) if k.startswith(want + '.') or k == want))
    print('=== %s — cobertura de notas (PT _ForSite | JP OCR) ===' % want)
    cpt = cjp = cboth = cnone = 0
    for k in keys:
        hp, hj = k in pt, k in jp
        tag = ('PT+JP' if hp and hj else 'PT' if hp else 'JP' if hj else '—')
        if hp and hj: cboth += 1
        elif hp: cpt += 1
        elif hj: cjp += 1
        print('  %-14s %s' % (k, tag))
    tot = len(keys)
    print('\n  nós: %d | PT+JP: %d | só PT: %d | só JP: %d | órfãos(scan): %d'
          % (tot, cboth, cpt, cjp, tot - cboth - cpt - cjp))
    print('  → União digital cobre %d/%d (%.0f%%)' % (cboth + cpt + cjp, tot, 100 * (cboth + cpt + cjp) / max(tot, 1)))

if __name__ == '__main__':
    main()
