# -*- coding: utf-8 -*-
"""Analisa as formas dos marcadores editoriais [Explicacao]/[Trecho...]/[Anexo...]."""
import re, glob, os
from collections import Counter

LABEL = r'(Explicação|Trecho do Preâmbulo[^\]]*|Trecho do Posfácio[^\]]*|Anexo[^\]]*)'
RE = re.compile(r'^(?P<pre>\**)\\?\[(?P<label>' + LABEL + r')\\?\](?P<post>\**)(?P<rest>.*)$')

def body_italic(rest, lines, idx):
    """rest = texto apos o fecho na mesma linha; se vazio, olha proxima linha nao-vazia."""
    r = rest.strip()
    if r:
        # inline: corpo comeca aqui; considera italico se termina com '*'
        return r.endswith('*')
    # bloco: proxima linha com conteudo
    j = idx + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j < len(lines):
        nxt = lines[j].strip()
        return nxt.startswith('*') and not nxt.startswith('**')
    return False

shapes = Counter()
italic = Counter()
examples = {}
noital = []

for path in sorted(glob.glob('ShinDendo_*.md')):
    with open(path, encoding='utf-8') as f:
        lines = f.read().split('\n')
    for i, line in enumerate(lines):
        m = RE.match(line)
        if not m:
            continue
        pre, post, rest = m.group('pre'), m.group('post'), m.group('rest')
        kind = 'inline' if rest.strip() else 'bloco'
        shape = 'pre=%d post=%d %s' % (len(pre), len(post), kind)
        shapes[shape] += 1
        ital = body_italic(rest, lines, i)
        italic[(kind, ital)] += 1
        examples.setdefault(shape, '%s:%d  %s' % (os.path.basename(path), i + 1, line[:90]))
        if not ital:
            noital.append('%s:%d  %s' % (os.path.basename(path), i + 1, line[:80]))

print('=== FORMAS (pre=asteriscos antes de [ , post=depois de ]) ===')
for s, c in shapes.most_common():
    print('  %-28s x%-4d  ex: %s' % (s, c, examples[s]))
print('\n=== CORPO EM ITALICO? ===')
for k, c in italic.most_common():
    print('  %-18s x%d' % (str(k), c))
print('\n=== CORPO SEM ITALICO (amostra, max 15) ===')
for e in noital[:15]:
    print('  ' + e)
print('\n  total marcadores:', sum(shapes.values()), '| sem italico:', len(noital))
