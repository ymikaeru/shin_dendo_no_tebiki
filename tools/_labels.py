# -*- coding: utf-8 -*-
import re, glob
from collections import Counter
c = Counter()
for p in glob.glob('ShinDendo_*.md'):
    for line in open(p, encoding='utf-8'):
        m = re.match(r'^\**\\\[([^(\]]+)', line)
        if m:
            key = m.group(1).strip().rstrip('\\')
            c[key] += 1
for k, n in c.most_common():
    print('%4d  %s' % (n, k))
