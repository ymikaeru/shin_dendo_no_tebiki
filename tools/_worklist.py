# -*- coding: utf-8 -*-
"""Gera checklist dos corpos editoriais SEM italico (para correcao manual da Fase A.3)."""
import re, glob, os
BS = chr(92)
LABEL = r'(Explicação|Trecho[^\]]*|Anexo[^\]]*|Resumo[^\]]*)'
RE = re.compile(r'^(?P<pre>\**)\\?\[(?P<label>' + LABEL + r')\\?\](?P<post>\**)(?P<rest>.*)$')

def kind(label):
    if label.startswith('Explicação') or label.startswith('Resumo'):
        return ('Explicação/Resumo', 'corpo INTEIRO em italico (ate o proximo titulo/marcador)')
    if label.startswith('Trecho'):
        return ('Trecho', 'so o PARAGRAFO DE CONTEXTO em italico; o ensinamento fica ROMANO')
    if label.startswith('Anexo'):
        return ('Anexo', 'DEPENDE: titulo/Salmo em italico; ensinamento embutido fica ROMANO')
    return ('?', '?')

lines_out = []
total = 0
for path in sorted(glob.glob('ShinDendo_*.md')):
    rows = open(path, encoding='utf-8').read().split('\n')
    for i, l in enumerate(rows):
        m = RE.match(l)
        if not m or m.group('rest').strip():
            continue
        j = i + 1
        while j < len(rows) and not rows[j].strip():
            j += 1
        s = rows[j].strip() if j < len(rows) else ''
        if s.startswith('*') and not s.startswith('**'):
            continue  # ja italico
        total += 1
        lab = m.group('label').rstrip(BS).strip()
        k, action = kind(lab)
        snippet = (s[:75] + '...') if len(s) > 75 else s
        lines_out.append('[ ] %-22s L%-4d  %-18s -> %s' % (os.path.basename(path), j + 1, k, action))
        lines_out.append('        corpo: %s' % snippet)

header = [
    'CHECKLIST FASE A.3 - corpos editoriais sem italico (%d itens)' % total,
    'Convencao: rotulo ***[X]***  |  corpo editorial em *italico*  |  ensinamento em romano',
    '=' * 78, '']
open('_corpos_sem_italico.txt', 'w', encoding='utf-8').write('\n'.join(header + lines_out) + '\n')
print('\n'.join(header + lines_out[:24]))
print('...\n(lista completa em _corpos_sem_italico.txt - %d itens)' % total)
