# -*- coding: utf-8 -*-
"""Lista os blocos [Trecho]/[Anexo] do C1_Item04 e classifica cada paragrafo:
italico? termina com data (ensinamento)? e Salmo? -> para decidir o que volta a romano."""
import re, sys

path = sys.argv[1] if len(sys.argv) > 1 else 'ShinDendo_C1_Item04.md'
lines = open(path, encoding='utf-8').read().split('\n')

HEAD = re.compile(r'^#{1,6}\s')
MARK = re.compile(r'^\*\*\*\\\[(Explicação|Trecho[^\]]*|Anexo[^\]]*|Resumo[^\]]*)\\\]')
DATE = re.compile(r'\((?:\d{1,2} de \w+ de )?\d{4}')   # (1952  ou (6 de abril de 1952

def paragraphs(start):
    """Coleta paragrafos (blocos separados por linha vazia) ate o proximo titulo/marcador."""
    out = []
    i = start
    while i < len(lines):
        if HEAD.match(lines[i]) or MARK.match(lines[i]):
            break
        if lines[i].strip():
            j = i
            buf = []
            while j < len(lines) and lines[j].strip() and not HEAD.match(lines[j]) and not MARK.match(lines[j]):
                buf.append(lines[j])
                j += 1
            out.append((i + 1, '\n'.join(buf)))
            i = j
        else:
            i += 1
    return out

for idx, line in enumerate(lines):
    m = MARK.match(line)
    if not m:
        continue
    label = m.group(1)
    if label.startswith('Explicação') or label.startswith('Resumo'):
        continue
    short = label[:38]
    print('L%-4d [%s]' % (idx + 1, short))
    for (ln, para) in paragraphs(idx + 1):
        txt = para.strip()
        ital = txt.startswith('*') and txt.rstrip().endswith('*') and not txt.startswith('**')
        salmo = ('御詠' in txt) or ('Gyoei' in txt) or txt.lstrip('*').startswith('Salmo')
        date = bool(DATE.search(txt))
        flag = 'ITALICO' if ital else 'romano '
        tag = []
        if salmo: tag.append('SALMO')
        if date: tag.append('data')
        teach = (ital and date and not salmo and len(txt) > 180)
        if teach: tag.append('>>> ENSINAMENTO? (voltar romano)')
        print('    L%-4d %s len=%-4d %-22s %s' % (ln, flag, len(txt), ' '.join(tag), txt[:55].replace(chr(10), ' ')))
    print()
