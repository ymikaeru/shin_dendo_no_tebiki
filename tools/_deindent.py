# -*- coding: utf-8 -*-
"""De-indenta cabeçalhos markdown (manda o # pra coluna 0) num .md.
O conversor só reconhece '#' no início da linha; cabeçalhos indentados viram corpo.
Uso: python tools/_deindent.py ShinDendo_C2_Item04.md   (roda da raiz do projeto)
"""
import re, sys, os

fn = sys.argv[1]
lines = open(fn, encoding='utf-8').read().split('\n')
HEAD_INDENT = re.compile(r'^[ \t]+(#{1,6})(?:[ \t].*)?$')   # ws + 1-6# + (espaço+resto | nada)
out, n = [], 0
for l in lines:
    if HEAD_INDENT.match(l):
        out.append(l.lstrip()); n += 1
    else:
        out.append(l)
open(fn, 'w', encoding='utf-8', newline='').write('\n'.join(out))
print('cabeçalhos de-indentados em %s: %d' % (fn, n))
print('restantes indentados:', sum(1 for l in out if HEAD_INDENT.match(l)))
