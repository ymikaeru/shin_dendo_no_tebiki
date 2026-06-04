# -*- coding: utf-8 -*-
"""Desitaliza os 5 titulos Letra (###### *X* -> ###### X) do C2_Item03. So titulos, nada de corpo."""
import re
path = 'ShinDendo_C2_Item03.md'
RE = re.compile(r'^(######) \*(.+)\*(\s*)$')
lines = open(path, encoding='utf-8').read().split('\n')
n = 0
for i, l in enumerate(lines):
    m = RE.match(l)
    if m:
        lines[i] = m.group(1) + ' ' + m.group(2) + m.group(3)
        n += 1
open(path, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
print('Titulos Letra desitalizados em C2_Item03:', n)
