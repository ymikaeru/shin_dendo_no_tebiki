# -*- coding: utf-8 -*-
"""DIAGNÓSTICO Fase B: parseia os blocos [Notas] do _ForSite por ensinamento e
mede cobertura. NÃO injeta nada ainda — só relatório.

Bloco formato A:  [Notas] <ancora> N <texto ... (Livro pág. N).> <ancora> N+1 ...
Uso: python _notes_extract.py            (resumo dos 8)
     python _notes_extract.py C1 1       (detalha Capítulo 1, Item 1)
"""
import re, sys, os

SRC = os.path.join('Nao Organizados', 'Shin-DendoNoTebiki_ForSite.md')
def unesc(s): return re.sub(r'\\(.)', r'\1', s or '')

HEAD = re.compile(r'^(#{1,6})\s+(.*?)\s*$')
NOTAS = re.compile(r'\**\\?\[Notas\\?\]\**\s*(.*)$')          # linha do bloco [Notas]
# entrada de nota: número (talvez *N) + texto terminando em (Livro pág. N).
NOTE_ENTRY = re.compile(r'\*?(\d+)\s+(.+?\(Livro\s+p[áa]g\.?\s*\d+\)\.)', re.S)

def parse_block(txt):
    """Devolve {n:int -> texto} a partir do conteúdo do bloco [Notas]."""
    t = unesc(txt)
    t = re.sub(r'^\s*Nota:?\s*', '', t)
    out = {}
    for m in NOTE_ENTRY.finditer(t):
        out[int(m.group(1))] = m.group(2).strip()
    return out, t

def walk():
    """Itera ensinamentos do _ForSite com (capítulo, item, num, título, bloco_notas?)."""
    lines = open(SRC, encoding='utf-8').read().split('\n')
    cap = item = None
    teachings = []   # (cap, item, marc, title, line_idx)
    for i, ln in enumerate(lines):
        h = HEAD.match(ln)
        if not h:
            continue
        lvl, txt = len(h.group(1)), unesc(h.group(2)).strip()
        if re.match(r'^Cap[íi]tulo\s+(\d)', txt):
            cap = re.match(r'^Cap[íi]tulo\s+(\d)', txt).group(1); item = None
        elif re.match(r'^Item\s+(\d)', txt):
            item = re.match(r'^Item\s+(\d)', txt).group(1)
        else:
            mk = re.match(r'^(\d+)\b', txt)
            if mk and cap and item:
                teachings.append([cap, item, mk.group(1), txt[:40], i])
    # acha o bloco [Notas] de cada ensinamento (entre seu heading e o próximo)
    head_lines = [t[4] for t in teachings]
    res = []
    for k, t in enumerate(teachings):
        start = t[4]; end = head_lines[k+1] if k+1 < len(teachings) else len(lines)
        notas = None
        for ln in lines[start:end]:
            nm = NOTAS.search(ln)
            if nm:
                notas = parse_block(nm.group(1))[0]; break
        res.append((t[0], t[1], t[2], t[3], notas))
    return res

def main():
    res = walk()
    args = sys.argv[1:]
    if len(args) == 2:
        capf, itemf = args[0].lstrip('Cc'), args[1]
        print('=== Capítulo %s, Item %s ===' % (capf, itemf))
        for (c, it, n, title, notas) in res:
            if c == capf and it == itemf:
                tag = ('%d notas' % len(notas)) if notas else 'ÓRFÃO (sem [Notas])'
                print('  %s.%-3s %-42s %s' % (n, '', title, tag))
                if notas:
                    for k in sorted(notas): print('       [%d] %s' % (k, notas[k][:70]))
        return
    # resumo por capítulo/item
    from collections import defaultdict
    tot = com = 0
    by = defaultdict(lambda: [0, 0])
    for (c, it, n, title, notas) in res:
        tot += 1
        key = 'c%s.i%s' % (c, it)
        by[key][0] += 1
        if notas: com += 1; by[key][1] += 1
    print('Ensinamentos numerados no _ForSite: %d | com [Notas]: %d (%.0f%%)' % (tot, com, 100*com/max(tot,1)))
    for key in sorted(by):
        print('  %-8s %d/%d com notas' % (key, by[key][1], by[key][0]))

if __name__ == '__main__':
    main()
