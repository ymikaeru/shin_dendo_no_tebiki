# -*- coding: utf-8 -*-
"""Fase B — fila de PROPOSTAS de notas (a IA propõe, o usuário aprova no /nav).

Cada marcador cru de OCR (\\*N) no .md vira uma VAGA na fila `_notes_proposals.json`.
As fontes (PT _ForSite, JP OCR traduzido, scans) preenchem `texto` e `trecho`;
o usuário revisa no /nav e APROVA (vira ==trecho==[^id] + def no ## Notas),
REJEITA (fica como está) ou DESCARTA o marcador (marcador espúrio: some do .md).

Nada mexe no .md sem aprovação. Toda gravação passa pela trava de prosa
(_notes_guard.normalize) e faz backup, como o resto do servidor.

Funções usadas pelo servidor.py:
    load() / save()                     -> fila
    approve(pid, texto, trecho)         -> coloca a nota no .md
    drop_marker(pid)                    -> remove só o marcador cru
    set_status(pid, status, **campos)   -> rejeitar / reabrir / editar
Inventário (tools/notes_inventory.py): scan_markers(), merge_inventory().
"""
import os, re, json, time, shutil, subprocess, sys, difflib, unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(ROOT, '_notes_proposals.json')
BACKUP_DIR = os.path.join(ROOT, '_backup_editor')
MD_GLOB_RE = re.compile(r'^ShinDendo_C(\d)_Item(\d+)\.md$')

# marcador cru de OCR, 2 formas:
#   asterisco:  \*3  ou  *3        (não pega ênfase *itálico*, nem **negrito**)
#   colado:     boca2.  Isso6 é  "Mal"3   (dígito grudado na palavra, sem asterisco)
RAW_MK = re.compile(r'(?<![\*\\])(\\?\*)(\d{1,2})(?![\d\*])')
GLUED_MK = re.compile(r'(?:(?<=[a-zà-ÿ]{2})|(?<=[a-zà-ÿ][)"”»]))()(\d{1,2})(?![\d\*])(?=[\s.,;:!?)"”»\]\\]|$)')


def iter_markers(text):
    """-> matches dos marcadores crus (as 2 formas), em ordem de posição."""
    ms = list(RAW_MK.finditer(text)) + list(GLUED_MK.finditer(text))
    return sorted(ms, key=lambda m: m.start())
STATUSES = ('pendente', 'sem-fonte', 'aprovada', 'rejeitada', 'descartada')


# ---------------------------------------------------------------------------
# utilidades de texto
# ---------------------------------------------------------------------------
def unesc(s):
    return re.sub(r'\\(.)', r'\1', s or '')


def clean(s):
    """Texto comparável: sem escapes, grifos, refs [^id], marcadores crus, ênfase."""
    s = re.sub(r'\[\^[^\]]+\]', '', s or '')
    s = re.sub(r'\\?\*\d{1,2}(?!\d)', '', s)
    s = s.replace('==', '')
    s = re.sub(r'\{\{\w+\}\}', '', s)
    s = unesc(s).replace('*', '')
    return re.sub(r'\s+', ' ', s).strip()


def fold(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', s.lower()).strip()


def md_pat(catchword):
    """Regex que casa o trecho no .md tolerando escapes \\x, espaços/quebras e
    ênfase * no meio (mesma ideia do servidor._md_pat, um pouco mais tolerante)."""
    out = []
    for c in catchword:
        if c == ' ':
            out.append(r'[\s\*]+')
        elif c.isalnum():
            out.append(re.escape(c))
        else:
            out.append(r'\\?' + re.escape(c))
    return ''.join(out)


def md_file_of(node_id):
    m = re.match(r'^c(\d+)\.i(\d+)', node_id or '')
    return ('ShinDendo_C%s_Item%02d.md' % (m.group(1), int(m.group(2)))) if m else None


# ---------------------------------------------------------------------------
# mapa linha -> nó (mesma hierarquia do _build_book.build)
# ---------------------------------------------------------------------------
def _bb():
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    cwd = os.getcwd()
    os.chdir(ROOT)                      # _build_book lê _editor_map.json relativo
    try:
        import _build_book as bb
    finally:
        os.chdir(cwd)
    return bb


def line_nodes(fn, lines):
    """-> lista [node_id por linha] seguindo a mesma pilha de níveis do conversor."""
    bb = _bb()
    m = MD_GLOB_RE.match(fn)
    capn, itemn = m.group(1), str(int(m.group(2)))
    cap_id, item_id = 'c' + capn, 'c%s.i%s' % (capn, itemn)
    fhp = any(bb.HEAD.match(l) and bb.strip_emph(bb.HEAD.match(l).group(2)).split(' ')[0].rstrip('\\.') == 'II'
              for l in lines)
    out, curr, stack, in_notas = [], item_id, [(1, item_id)], False
    for ln in lines:
        hm = bb.HEAD.match(ln)
        if hm:
            raw = hm.group(2)
            if bb.strip_emph(raw).lower() == 'notas':
                in_notas = True
            else:
                in_notas = False
                nivel, marc, _ = bb.classify(raw, fhp)
                if nivel == 'Capitulo':
                    curr = cap_id
                elif nivel == 'Item':
                    curr = item_id; stack = [(1, item_id)]
                elif nivel not in (None, 'VAZIO'):
                    rank = bb.RANK[nivel]
                    while len(stack) > 1 and stack[-1][0] >= rank:
                        stack.pop()
                    curr = stack[-1][1] + '.' + marc
                    stack.append((rank, curr))
        out.append(None if in_notas else curr)
    return out


# ---------------------------------------------------------------------------
# inventário dos marcadores crus
# ---------------------------------------------------------------------------
def guess_trecho(before):
    """Trecho provável da nota = a oração logo antes do marcador (até ~8 palavras,
    parando em pontuação forte). É só um palpite: o usuário ajusta no /nav."""
    b = clean(before).rstrip().lstrip('# ')
    q = re.search(r'["“][^"“”]{2,80}["”]$', b)          # termina numa expressão entre aspas
    if q:
        return q.group(0)
    cut = max(b.rfind(x) for x in ('. ', '; ', ': ', '? ', '! ', '— ', ', '))
    seg = b[cut + 2:] if cut >= 0 else b
    words = seg.split(' ')
    if len(words) > 8:
        seg = ' '.join(words[-8:])
    return seg.strip()


def scan_markers(root=ROOT):
    """-> [{file, node, n, line, heading, ctx, trecho}] em ordem de leitura."""
    items = []
    for fn in sorted(f for f in os.listdir(root) if MD_GLOB_RE.match(f)):
        text = open(os.path.join(root, fn), encoding='utf-8').read()
        lines = text.split('\n')
        nodes = line_nodes(fn, lines)
        for li, ln in enumerate(lines):
            if nodes[li] is None or re.match(r'^\s*\[\^', ln):
                continue
            for m in iter_markers(ln):
                before = ln[:m.start()]
                if not clean(before):           # marcador no início da linha (ex.: lista) — ignora
                    continue
                items.append({
                    'file': fn, 'node': nodes[li], 'n': int(m.group(2)), 'line': li + 1,
                    'forma': 'asterisco' if m.group(1) else 'colado',
                    'heading': ln.lstrip().startswith('#'),
                    'ctx': clean(before)[-80:],
                    'ctx_after': clean(ln[m.end():])[:40],
                    'trecho': guess_trecho(before),
                })
    return items


def slot_key(it):
    return '%s|%s|%d|%s' % (it['file'], it['node'], it['n'], fold(it['ctx'])[-40:])


def merge_inventory(items, queue=None):
    """Junta o inventário novo com a fila existente sem perder o trabalho já feito:
    vagas conhecidas mantêm id/status/texto; vagas novas entram como 'sem-fonte'."""
    queue = queue if queue is not None else load()
    by_key = {slot_key(p): p for p in queue['items']}
    used = {p['id'] for p in queue['items']}
    nxt = max([int(p['id'][1:]) for p in queue['items']] or [0]) + 1
    seen = set()
    for it in items:
        k = slot_key(it)
        p = by_key.get(k)
        if p:
            p.update({kk: it[kk] for kk in ('line', 'ctx', 'ctx_after', 'heading')})
            seen.add(p['id'])
            continue
        pid = 'p%04d' % nxt; nxt += 1
        while pid in used:
            pid = 'p%04d' % nxt; nxt += 1
        used.add(pid); seen.add(pid)
        queue['items'].append(dict(it, id=pid, status='sem-fonte', texto='', origem='',
                                   fonte_ref='', confianca=None, obs='', ref_id=None))
    # vagas cujo marcador sumiu do .md e que não foram resolvidas aqui -> marcadas
    for p in queue['items']:
        if p['id'] not in seen and p['status'] in ('pendente', 'sem-fonte'):
            p['status'] = 'descartada'
            p['obs'] = (p.get('obs') or '') + ' [marcador não encontrado no .md]'
    order = {f: i for i, f in enumerate(sorted({p['file'] for p in queue['items']}))}
    queue['items'].sort(key=lambda p: (order[p['file']], p['line']))
    return queue


# ---------------------------------------------------------------------------
# fila (persistência)
# ---------------------------------------------------------------------------
def load():
    if os.path.exists(QUEUE):
        return json.load(open(QUEUE, encoding='utf-8'))
    return {'version': 1, 'items': []}


def save(queue):
    tmp = QUEUE + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(queue, f, ensure_ascii=False, indent=1)
    os.replace(tmp, QUEUE)


def summary(queue=None):
    queue = queue or load()
    out = {}
    for p in queue['items']:
        d = out.setdefault(p['file'], {s: 0 for s in STATUSES})
        d[p['status']] = d.get(p['status'], 0) + 1
    return out


def _get(queue, pid):
    for p in queue['items']:
        if p['id'] == pid:
            return p
    raise KeyError('proposta %s não existe' % pid)


# ---------------------------------------------------------------------------
# localizar o marcador no .md atual (as posições mudam a cada aprovação)
# ---------------------------------------------------------------------------
def find_marker(md, p):
    """-> (start, end) do marcador cru da vaga no .md atual, ou None.
    Casa por N + semelhança do contexto anterior (robusto a grifos/notas já inseridos)."""
    want = fold(p['ctx'])[-60:]
    best, best_sc = None, 0.0
    for m in iter_markers(md):
        if int(m.group(2)) != p['n']:
            continue
        ls = md.rfind('\n', 0, m.start()) + 1
        got = fold(clean(md[max(ls, m.start() - 400):m.start()]))[-60:]
        if not got:
            continue
        sc = difflib.SequenceMatcher(None, want, got).ratio()
        if sc > best_sc:
            best, best_sc = (m.start(), m.end()), sc
    return best if best_sc >= 0.8 else None


# ---------------------------------------------------------------------------
# escrita no .md
# ---------------------------------------------------------------------------
def _write_md(name, base, new):
    """base = .md atual SEM o marcador removido (cortado na posição exata).
    Trava de prosa: além disso, só podem mudar ==, [^id] e o bloco ## Notas."""
    import _notes_guard as G
    if G.normalize(base) != G.normalize(new):
        raise ValueError('a mudança alteraria a prosa — abortado')
    path = os.path.join(ROOT, name)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(path, os.path.join(BACKUP_DIR, name + '.' + str(int(time.time()))))
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    subprocess.run([sys.executable, '_build_book.py'], cwd=ROOT, capture_output=True)


def _append_def(md, defline):
    nm = re.search(r'(?m)^##\s+Notas\s*$', md)
    if nm:
        defs = list(re.finditer(r'(?m)^\[\^[^\]]+\]:.*$', md[nm.end():]))
        if defs:
            pos = nm.end() + defs[-1].end()
            return md[:pos] + '\n' + defline + md[pos:]
        return md[:nm.end()] + '\n\n' + defline + md[nm.end():]
    return md.rstrip() + '\n\n## Notas\n\n' + defline + '\n'


def _new_ref(md, node_id):
    parts = node_id.split('.')
    pref = (parts[0] + parts[1] + '-' + '-'.join(parts[2:])).rstrip('-') if len(parts) >= 2 else node_id
    nums = [int(x) for x in re.findall(r'\[\^' + re.escape(pref) + r'-(\d+)\]', md)]
    return '%s-%d' % (pref, (max(nums) + 1) if nums else 1)


def place(md, p, texto, trecho):
    """Função pura: devolve (novo_md, ref_id, md_sem_marcador).
    Remove o marcador cru da vaga e coloca ==trecho==[^id] na ocorrência do trecho
    mais próxima do marcador (antes ou depois — o *N do OCR pode estar deslocado)."""
    texto = re.sub(r'\s+', ' ', texto or '').strip()
    trecho = re.sub(r'\s+', ' ', unesc(trecho or '')).strip()
    if not texto:
        raise ValueError('a nota está sem texto')
    span = find_marker(md, p)
    if not span:
        raise ValueError('marcador *%d não encontrado no .md (já resolvido?)' % p['n'])
    ms, me = span
    md2 = md[:ms] + md[me:]
    ref_id = _new_ref(md2, p['node'])
    ref = '[^%s]' % ref_id
    ls = md2.rfind('\n', 0, ms) + 1
    le = md2.find('\n', ms); le = len(md2) if le < 0 else le
    if md2[ls:ls + 1] == '#' or not trecho:
        # título (o título inteiro acende no hover) ou sem trecho: ref no lugar do marcador
        new = md2[:ms] + ref + md2[ms:]
    else:
        cands = [m for m in re.finditer(md_pat(trecho), md2)]
        # só no mesmo parágrafo do marcador, fora de grifos/refs existentes
        ok = []
        for m in cands:
            if m.start() < ls or m.end() > le:
                continue
            seg = md2[m.start():m.end()]
            if '==' in seg or '[^' in seg:
                continue
            if md2[:m.start()].count('==') % 2:      # dentro de um ==grifo== aberto
                continue
            ok.append(m)
        if not ok:
            raise ValueError('trecho «%s» não encontrado no parágrafo do marcador' % trecho[:60])
        m = min(ok, key=lambda mm: min(abs(mm.end() - ms), abs(mm.start() - ms)))
        s, e = m.start(), m.end()
        # não engole ênfase/espaço nas pontas
        while e > s and md2[e - 1] in ' *':
            e -= 1
        while s < e and md2[s] in ' *':
            s += 1
        new = md2[:s] + '==' + md2[s:e] + '==' + ref + md2[e:]
    new = _append_def(new, '[^%s]: %s' % (ref_id, texto))
    return new, ref_id, md2


def approve(pid, texto, trecho):
    q = load(); p = _get(q, pid)
    if p['status'] == 'aprovada':
        raise ValueError('proposta já aprovada')
    path = os.path.join(ROOT, p['file'])
    md = open(path, encoding='utf-8').read()
    new, ref_id, base = place(md, p, texto, trecho)
    _write_md(p['file'], base, new)
    p.update(status='aprovada', texto=re.sub(r'\s+', ' ', texto).strip(), trecho=trecho,
             ref_id=ref_id, quando=int(time.time()))
    save(q)
    return p


def drop_marker(pid):
    """Marcador espúrio: remove só o \\*N do .md (a prosa não muda)."""
    q = load(); p = _get(q, pid)
    path = os.path.join(ROOT, p['file'])
    md = open(path, encoding='utf-8').read()
    span = find_marker(md, p)
    if not span:
        raise ValueError('marcador não encontrado no .md')
    new = md[:span[0]] + md[span[1]:]
    _write_md(p['file'], new, new)
    p.update(status='descartada', quando=int(time.time()))
    save(q)
    return p


def set_status(pid, status=None, **fields):
    q = load(); p = _get(q, pid)
    if status:
        if status not in STATUSES or status == 'aprovada':
            raise ValueError('status inválido')
        if p['status'] == 'aprovada':
            raise ValueError('já aprovada — edite a nota pelo modo ✏️ Editar')
        p['status'] = status
    for k in ('texto', 'trecho', 'obs'):
        if k in fields and fields[k] is not None:
            p[k] = re.sub(r'\s+', ' ', str(fields[k])).strip()
    if p['status'] == 'sem-fonte' and p.get('texto'):
        p['status'] = 'pendente'
    save(q)
    return p
