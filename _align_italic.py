# -*- coding: utf-8 -*-
"""Alinha C1_Item04 ao padrao dos outros 7:
1) tira italico dos titulos nivel Letra (#####/###### *X* -> X)
2) em cada bloco [Trecho]/[Anexo]: 1o paragrafo (contexto) fica italico;
   paragrafos seguintes (ensinamento) voltam a romano. Salmo (御詠) continua italico.
   Blocos complexos (com sub-itens ***...***) sao PULADOS e sinalizados p/ revisao manual.
Modo relatorio por padrao; --write aplica.
"""
import re, sys

path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'ShinDendo_C1_Item04.md'
write = '--write' in sys.argv
lines = open(path, encoding='utf-8').read().split('\n')

HEAD = re.compile(r'^#{1,6}\s')
MARK = re.compile(r'^\*\*\*\\\[(Explicação|Trecho[^\]]*|Anexo[^\]]*|Resumo[^\]]*)\\\]')
HEAD_ITAL = re.compile(r'^(#{5,6}) \*(.+)\*(\s*)$')
LINE_ITAL = re.compile(r'^(\s*)\*([^*].*?)\*(\s*)$')   # *texto* (nao **; permite \* interno)
BOLD = re.compile(r'^\s*\*\*\*')

def is_salmo(s):
    return ('御詠' in s) or ('Gyoei' in s) or s.lstrip('*').strip().startswith('Salmo')

SKIP = {353, 239}      # L354 e L240 (0-based): revisao manual com o usuario
unital_lines = set()   # indices a desitalizar
report = []
flagged = []
n_head = 0

# 1) titulos Letra
for i, l in enumerate(lines):
    if HEAD_ITAL.match(l):
        unital_lines.add(('head', i))
        n_head += 1

# 2) blocos Trecho/Anexo
i = 0
while i < len(lines):
    m = MARK.match(lines[i])
    if not m:
        i += 1
        continue
    label = m.group(1)
    if label.startswith('Explicação') or label.startswith('Resumo'):
        i += 1
        continue
    # delimita o bloco
    j = i + 1
    block = []
    while j < len(lines) and not HEAD.match(lines[j]) and not MARK.match(lines[j]):
        block.append(j)
        j += 1
    # paragrafos (separados por linha vazia)
    paras, cur = [], []
    for k in block:
        if lines[k].strip():
            cur.append(k)
        elif cur:
            paras.append(cur); cur = []
    if cur:
        paras.append(cur)
    complex_block = any(BOLD.match(lines[k]) for k in block)
    short = label[:34]
    if i in SKIP:
        flagged.append('L%-4d [%s] PULADO -> revisao manual com usuario' % (i + 1, short))
        i = j
        continue
    if complex_block:
        flagged.append('L%-4d [%s] COMPLEXO (sub-itens ***) -> REVISAR MANUAL' % (i + 1, short))
        i = j
        continue
    # 1o paragrafo = contexto (mantem italico); resto = ensinamento (romano), exceto Salmo
    for pidx, para in enumerate(paras):
        if pidx == 0:
            continue
        for k in para:
            if is_salmo(lines[k]):
                continue
            if LINE_ITAL.match(lines[k]):
                unital_lines.add(('teach', k))
                report.append('  L%-4d romano <- %s' % (k + 1, lines[k].strip()[:60]))
    if len(paras) >= 3:
        flagged.append('L%-4d [%s] %d paragrafos -> CONFERIR limite contexto/ensino' % (i + 1, short, len(paras)))
    i = j

# aplica
out = list(lines)
for kind, idx in unital_lines:
    mm = HEAD_ITAL.match(lines[idx]) if kind == 'head' else LINE_ITAL.match(lines[idx])
    if mm:
        out[idx] = (mm.group(1) + ' ' + mm.group(2) + mm.group(3)) if kind == 'head' else (mm.group(1) + mm.group(2) + mm.group(3))

print('Titulos Letra desitalizados: %d' % n_head)
print('Linhas de ensinamento -> romano: %d' % sum(1 for k, _ in unital_lines if k == 'teach'))
print('\n--- BLOCOS SINALIZADOS p/ revisao (%d) ---' % len(flagged))
for f in flagged:
    print(' ', f)
print('\n--- amostra de linhas revertidas p/ romano (primeiras 12) ---')
for r in report[:12]:
    print(r)

if write:
    open(path, 'w', encoding='utf-8', newline='').write('\n'.join(out))
    print('\n>>> ESCRITO em', path)
else:
    print('\n(relatorio; use --write para aplicar)')
