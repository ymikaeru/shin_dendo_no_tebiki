# -*- coding: utf-8 -*-
import re, glob, os
from collections import Counter
BS = chr(92)  # backslash
LABEL = r'(Explicação|Trecho[^\]]*|Anexo[^\]]*|Resumo[^\]]*)'
RE = re.compile(r'^(?P<pre>\**)\\?\[(?P<label>' + LABEL + r')\\?\](?P<post>\**)(?P<rest>.*)$')
per = Counter(); bylabel = Counter()
for path in sorted(glob.glob('ShinDendo_*.md')):
    lines = open(path, encoding='utf-8').read().split('\n')
    for i, l in enumerate(lines):
        m = RE.match(l)
        if not m:
            continue
        if m.group('rest').strip():
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        s = lines[j].strip() if j < len(lines) else ''
        ital = s.startswith('*') and not s.startswith('**')
        if not ital:
            per[os.path.basename(path)] += 1
            lab = m.group('label').split('(')[0].strip().rstrip(BS)
            bylabel[lab.split(' refer')[0]] += 1
print('Corpos SEM italico, por arquivo:')
for k, n in per.most_common():
    print('  %-28s %d' % (k, n))
print('\nPor tipo de rotulo:')
for k, n in bylabel.most_common():
    print('  %-22s %d' % (k, n))
