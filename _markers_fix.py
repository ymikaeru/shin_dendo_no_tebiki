# -*- coding: utf-8 -*-
"""Fase A.2: uniformiza marcadores editoriais para ***\\[Rotulo\\]*** (bloco).
- bloco (rotulo sozinho na linha): normaliza os asteriscos para 3+3.
- inline (corpo na mesma linha): converte para bloco, corpo em italico.
NAO altera corpos de bloco multi-linha (Fase A.3).
"""
import re, glob, os, sys

LABEL = r'(Explicação|Trecho[^\]]*|Anexo[^\]]*|Resumo[^\]]*)'
RE = re.compile(r'^(?P<pre>\**)\\?\[(?P<label>' + LABEL + r')\\?\](?P<post>\**)(?P<rest>.*)$')

def fix_file(path, write):
    with open(path, encoding='utf-8') as f:
        lines = f.read().split('\n')
    out, n_block, n_inline = [], 0, 0
    for line in lines:
        m = RE.match(line)
        if not m:
            out.append(line)
            continue
        label = m.group('label').rstrip('\\').rstrip()
        rest = m.group('rest').strip()
        if not rest:                                   # BLOCO (rotulo sozinho)
            new = '***\\[' + label + '\\]***   '
            if new.rstrip() != line.rstrip():
                n_block += 1
            out.append(new)
        else:                                          # INLINE -> BLOCO
            body = rest.strip('*').strip()
            out.append('***\\[' + label + '\\]***   ')
            out.append('')
            out.append('*' + body + '*')
            n_inline += 1
    if write:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(out))
    return n_block, n_inline

if __name__ == '__main__':
    write = '--write' in sys.argv
    files = [a for a in sys.argv[1:] if not a.startswith('--')] or sorted(glob.glob('ShinDendo_*.md'))
    for p in files:
        nb, ni = fix_file(p, write)
        print('%-32s rotulos_normalizados=%-3d inline->bloco=%d' % (os.path.basename(p), nb, ni))
