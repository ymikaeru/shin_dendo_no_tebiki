# -*- coding: utf-8 -*-
"""Check de CONSERVACAO: cada linha de CORPO do .md cai em algum campo do JSON?
Checa cada arquivo contra a SUBARVORE do seu item (c{cap}.i{item}) + campos
proprios do capitulo -> evita mascaramento cruzado entre arquivos.

Uso:
    python _conserva.py                       -> todos os 8 (resumo + misses)
    python _conserva.py ShinDendo_C2_Item03.md -> so esse arquivo (verboso)
"""
import json, re, sys, glob, os

def norm(s):
    s = re.sub(r'\\(.)', r'\1', s or '')      # desescapa \X
    s = re.sub(r'\[\^[^\]]+\]', '', s)         # tira marcadores de nota [^id]
    s = s.replace('*', '')                     # tira asteriscos
    s = re.sub(r'[―—]{2,}', ' ', s)            # ―― -> espaco (igual ao conversor no subtitulo)
    s = re.sub(r'\s+', ' ', s)                 # colapsa espaco
    return s.strip().lower()

SKIP_KEYS = ('id', 'nivel', 'marcador', 'level', 'file')

def own_strings(n):
    """Campos string DIRETOS de n (sem descer em children)."""
    out = []
    for k, v in n.items():
        if k in SKIP_KEYS or k == 'children':
            continue
        _collect(v, out)
    return out

def subtree_strings(n):
    out = []
    def rec(x):
        if isinstance(x, str):
            out.append(norm(x))
        elif isinstance(x, dict):
            for k, v in x.items():
                if k not in SKIP_KEYS:
                    rec(v)
        elif isinstance(x, list):
            for v in x:
                rec(v)
    rec(n)
    return out

def _collect(x, out):
    if isinstance(x, str):
        out.append(norm(x))
    elif isinstance(x, dict):
        for k, v in x.items():
            if k not in SKIP_KEYS:
                _collect(v, out)
    elif isinstance(x, list):
        for v in x:
            _collect(v, out)

b = json.load(open('shin-dendo-tebiki.json', encoding='utf-8'))
IMAGENS = b.get('imagens', {})
IDX = {}
CAP_OF = {}
def walk(n, cap):
    IDX[n['id']] = n
    CAP_OF[n['id']] = cap
    for c in n.get('children', []):
        walk(c, cap if cap else n)
for s in b['sections']:
    walk(s, None)

HEAD = re.compile(r'^#{1,6}\s')
MARK = re.compile(r'^\**\\?\[(Explicação|Resumo|Trecho|Anexo)')
NOTEDEF = re.compile(r'^\s*\[\^[^\]]+\]:')

def item_id(fn):
    m = re.match(r'ShinDendo_C(\d)_Item(\d+)\.md', fn)
    return 'c%s.i%s' % (m.group(1), str(int(m.group(2))))

def split_ok(s, BLOB):
    """Linha '(título JP)(fonte) texto' que o conversor DIVIDE em campos (título/fonte/texto):
    conservada se CADA pedaço (grupos iniciais + resto) estiver em algum campo."""
    from _build_book import lead_groups, unesc
    groups, rest = lead_groups(unesc(s).strip())
    if not groups:
        return False
    pieces = [g for g in groups] + ([rest] if rest.strip() else [])
    for p in pieces:
        q = norm(p).strip('() ').strip()
        if len(q) >= 4 and q[:40] not in BLOB:
            return False
    return True

def check(md, verbose):
    fn = os.path.basename(md)
    iid = item_id(fn)
    item = IDX.get(iid)
    if not item:
        print('  !! sem no JSON para', iid); return (0, 0, [])
    cap = CAP_OF.get(iid)
    blob_parts = subtree_strings(item)
    if cap:
        blob_parts += own_strings(cap)      # explicacao/subtitulo do capitulo (no Item01)
    BLOB = ' \n '.join(blob_parts)

    lines = open(md, encoding='utf-8').read().split('\n')
    body, missing = 0, []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or s in ('---', '***'):
            continue
        if HEAD.match(s) or MARK.match(s) or NOTEDEF.match(s):
            continue
        im = re.match(r'^\[(image\d+)\]:\s*<data:', s)          # imagem embutida -> book['imagens']
        if im and im.group(1) in IMAGENS:
            continue
        n = re.sub(r'^[-–—•]\s*', '', norm(s)).strip('() ').strip()
        if len(n) < 4:
            continue
        body += 1
        if n[:50] not in BLOB and not split_ok(s, BLOB):
            missing.append((i + 1, s[:96]))
    if verbose:
        print('%s (%s): %d/%d linhas de corpo NAO conservadas' % (fn, iid, len(missing), body))
        for (ln, txt) in missing:
            print('  L%-5d %s' % (ln, txt))
    return (body, len(missing), missing)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    files = sorted(args) if args else sorted(glob.glob('ShinDendo_*.md'))
    verbose = len(files) == 1
    tot_body = tot_miss = 0
    rows = []
    for f in files:
        body, miss, misses = check(f, verbose)
        tot_body += body; tot_miss += miss
        rows.append((os.path.basename(f), body, miss, misses))
    if not verbose:
        print('%-26s corpo  perdidas' % 'arquivo')
        for (name, body, miss, _) in rows:
            flag = '  <<<' if miss else ''
            print('  %-24s %5d   %4d%s' % (name[10:], body, miss, flag))
        print('  %-24s %5d   %4d' % ('TOTAL', tot_body, tot_miss))
        print('\n--- misses por arquivo (cap 25/arq) ---')
        for (name, body, miss, misses) in rows:
            if not miss:
                continue
            print('\n[%s] %d perdidas:' % (name[10:], miss))
            for (ln, txt) in misses[:25]:
                print('  L%-5d %s' % (ln, txt))
            if miss > 25:
                print('  ... +%d' % (miss - 25))

if __name__ == '__main__':
    main()
