# -*- coding: utf-8 -*-
"""Conversor .md -> JSON do livro (shin-dendo-tebiki.json).

Reaproveita a classificacao de cabecalhos do _build_tree.py e adiciona o parsing
do CORPO de cada folha num objeto 'ensinamento' (fonte / preambulo / texto /
posfacio / data / explicacao / notas / anexo), conforme _sample_apostila.json e o
renderEnsinamento() do _nav_proto.html.

Modelo do corpo = FLUXO DE BLOCOS (block stream): cada bloco e tipado pelo marcador
***[...]*** que o abre; paragrafos romanos (nao-italicos) = texto. Sem set-on-sight.

Uso:
    python _build_book.py                       -> processa todos os ShinDendo_*.md
    python _build_book.py ShinDendo_C1_Item01.md -> piloto: so esse arquivo
"""
import re, json, glob, os, sys

# ----------------------------------------------------------------------------
# Classificacao de cabecalhos  (copiado de _build_tree.py, sem alteracao)
# ----------------------------------------------------------------------------
CIRCLED = {chr(c): i + 1 for i, c in enumerate(range(0x2460, 0x2474))}
ROMAN_UP = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX']
ROMAN_LO = [r.lower() for r in ROMAN_UP]
HEAD = re.compile(r'^(#{1,6})[ \t]*(.*?)[ \t]*$')
RANK = {'Parte':2,'Numero':3,'Circulo':4,'romano':5,'Letra':6,'letra':7}
NIVEL_PT = {'Parte':'parte','Numero':'numero','Circulo':'circulo','romano':'romano','Letra':'letra','letra':'letra_min'}

def strip_emph(s):
    s = s.strip(); s = re.sub(r'^[\*\\\s]+','',s); s = re.sub(r'[\*\\\s]+$','',s)
    return s.strip()

def classify(raw, fhp):
    t = strip_emph(raw)
    if not t: return ('VAZIO','','')
    if re.match(r'^Cap[íi]tulo\b',t): return ('Capitulo','',t)
    if re.match(r'^Item\b',t): return ('Item','',t)
    if t[0] in CIRCLED: return ('Circulo',str(CIRCLED[t[0]]),t[1:].strip())
    m = re.match(r'^([A-Za-z]+|\d+)\\?\.?[ \t)]',t+' ')
    if not m: return (None,None,t)
    tok = m.group(1); rest = t[m.end()-1:].strip()
    if tok.isdigit(): return ('Numero',tok,rest)
    low = tok.lower()
    if tok in ROMAN_UP and fhp: return ('Parte',tok,rest)
    if len(tok)>1 and tok in ROMAN_UP: return ('Parte',tok,rest)
    if low in ROMAN_LO and (len(low)>1 or low in ('i','v','x')): return ('romano',low,rest)
    if len(tok)==1: return ('Letra' if tok.isupper() else 'letra', tok, rest)
    return (None,None,t)

def unesc(s):
    """Remove os escapes de markdown (\\. \\~ \\< \\[ ...) deixando a prosa limpa."""
    return re.sub(r'\\(.)', r'\1', s or '')

# ----------------------------------------------------------------------------
# Paginas (de _editor_map.json)  -- mesma logica do _build_tree.py
# ----------------------------------------------------------------------------
def _page_key(s):
    # o mapa foi gravado com o título da época (ex. "...habitou?*1"); depois o título ganhou nota/grifo
    # ("...habitou?[^c1i1-2-1]") -> compara sem escapes, notas, grifos, tags e marcadores crus *N
    s = re.sub(r'\\(.)', r'\1', s)
    s = re.sub(r'\[\^[^\]]+\]|==|\{\{\w+\}\}', '', s)
    s = re.sub(r'\*\s?\d{1,3}(?!\d)|\*+\s*$', '', s)
    return re.sub(r'\s+', ' ', s).strip()

PAGES = {}
if os.path.exists('_editor_map.json'):
    for fn, secs in json.load(open('_editor_map.json', encoding='utf-8')).items():
        PAGES[fn] = {}
        for k, v in secs.items():
            if isinstance(v, dict):
                PAGES[fn][_page_key(k)] = v.get('pag')

def page_of(fn, raw_after_hash):
    return PAGES.get(fn, {}).get(_page_key(raw_after_hash))

# ----------------------------------------------------------------------------
# Marcadores editoriais  ***[Explicacao] / [Trecho do Preambulo ...] / [Anexo ...]***
# (LABEL de _markers.py, ampliado com Resumo e um Trecho generico)
# ----------------------------------------------------------------------------
LABEL = r'(Explicação|Resumo[^\]]*|Trecho do Preâmbulo[^\]]*|Trecho do Posfácio[^\]]*|Trecho[^\]]*|Anexo[^\]]*)'
MARKER = re.compile(r'^[ \t]*(?P<pre>\**)\\?\[(?P<label>' + LABEL + r')\\?\](?P<post>\**)(?P<rest>.*)$')

def marker_type(label):
    if label.startswith('Trecho do Posfácio'): return 'posfacio'
    if label.startswith('Trecho'):             return 'preambulo'   # Preambulo + Trecho generico
    if label.startswith('Anexo'):              return 'anexo'
    if label.startswith('Resumo'):             return 'resumo'      # [Resumo dos Relatos] -> campo resumo
    return 'explicacao'

# ----------------------------------------------------------------------------
# Citacao (fonte) e data
# ----------------------------------------------------------------------------
# Uma "fonte" parece citacao: tem pag/col/vol/secao/linha OU sigla de obra OU =/<>.
CIT = re.compile(
    r'(p[áa]g\.?|col\.|\bvol\b|se[çc][ãa]o|linha|\bl\.\s|\bNo\.|＝|=|〈|<'
    r'|\bRon\b|\bShu\b|\bKyo\b|\bIshi\b|\bEi\b|\bChi\b|\bSui\b|\bKigo\b|\bSan\b|\bToko\b'
    r'|\bHikari\b|\bRonbetsu\b|\bRonbetu\b|Zenk[oôó]u?|Zench[oôó]|\bGe\b)', re.I)
def is_cit(s): return bool(CIT.search(s or ''))

MONTHS = (r'janeiro|fevereiro|mar[çc]o|abril|maio|junho|julho|agosto|'
          r'setembro|outubro|novembro|dezembro')
DATE = re.compile(r'\b\d{4}\b|Era Showa|(?:' + MONTHS + r')', re.I)

TRAIL_PAREN = re.compile(r'\(([^()]*)\)\s*$')   # ultimo (...) sem parenteses internos, no fim

# --- tipagem editorial (conservador: falso-positivo e' pior que perda) ---
SALMO_TITLE = re.compile(r'\bsalmo\b|gyoei|御詠', re.I)              # salmo: por TITULO
REF_LEAD = re.compile(r'^\s*\**\\?\[?\s*(artigos?\s+de\s+refer|artigos?\s+relacionad'
                      r'|ensinamentos?\s+de\s+refer|artigos?\s+de\s+(?:consulta|leitura))', re.I)
REF_ITEM = re.compile(r'^\s*[-–—•]\s')                              # item de lista "- ..."
CJK_RE = re.compile(r'[぀-ヿ一-鿿]')
def is_jp_only(s):
    """Texto dominado por CJK (heading japones nao-traduzido). Conservador."""
    if not s:
        return False
    t = re.sub(r'[\s()（）「」、。]', '', s)
    if len(t) < 3:
        return False
    return len(CJK_RE.findall(t)) >= max(4, len(t) * 0.5)

# ----------------------------------------------------------------------------
# Limpeza de paragrafos
# ----------------------------------------------------------------------------
def clean_romano(lines):
    """Texto do ensinamento (romano): une linhas com espaco, desescapa. Mantem *1 etc."""
    return unesc(' '.join(l.strip() for l in lines)).strip()

def clean_romano_verse(lines):
    """Salmo: PRESERVA as quebras de linha (1 verso/data/fonte por linha), desescapa.
    Mantem *N, {{tag}} e ==grifo== (sem barra invertida, intactos no unesc). O leitor
    (renderAnexoBody) segmenta cada linha em verso/data/fonte."""
    return unesc('\n'.join(l.strip() for l in lines if l.strip())).strip()

def strip_ital_line(t):
    t = t.strip()
    t = re.sub(r'^\*+\s*', '', t)
    t = re.sub(r'\s*\*+$', '', t)
    return t

def clean_italic(lines):
    """Bloco editorial (italico): tira os * de borda de cada linha, une com espaco."""
    return unesc(' '.join(strip_ital_line(l) for l in lines)).strip()

def split_paras(body_lines):
    """Agrupa linhas em paragrafos separados por linha em branco; ignora '---'."""
    paras, cur = [], []
    for ln in body_lines:
        s = ln.strip()
        if s == '' or s == '---' or s == '***':
            if cur: paras.append(cur); cur = []
        else:
            cur.append(ln)
    if cur: paras.append(cur)
    return paras

def clean_anexo(label, first_body, rest_paras):
    """Anexo = sub-documento. Captura cru ate o proximo header, engolindo marcadores
    internos. Preserva quebras de paragrafo."""
    titulo = unesc(re.sub(r'[\\\s]+$', '', label)).strip()
    blocks = []
    if any(l.strip() for l in first_body):
        blocks.append('\n'.join(strip_ital_line(l) for l in first_body if l.strip()))
    for p in rest_paras:
        blocks.append('\n'.join(strip_ital_line(l) for l in p if l.strip()))
    txt = unesc('\n\n'.join(b for b in blocks if b.strip())).strip()
    return {'titulo': titulo, 'texto': txt}

# ----------------------------------------------------------------------------
# Parsing de um ENSINAMENTO a partir do titulo + corpo
# ----------------------------------------------------------------------------
SUBT = re.compile(r'^[―—]{2,}.*?[―—]{2,}')   # subtitulo EMOLDURADO: ――Tema――  (dialogo só-abre NAO conta)
MK_INLINE = re.compile(r'\**\\?\[(?:Explicação|Resumo|Trecho|Anexo)')

def split_heading(resto):
    """Cabecalho com CORPO grudado (OCR sem quebra de linha): separa em titulo +
    linhas de corpo. Casos: 'titulo (citacao) texto...' e 'titulo [Explicação] texto'.
    Conservador: so divide se houver marcador inline OU citacao com >40 chars depois."""
    mk = MK_INLINE.search(resto)
    citm = None
    for m in re.finditer(r'\(([^()]*)\)', resto):
        if is_cit(m.group(1)):
            citm = m; break
    cands = []
    if mk:
        cands.append(('mk', mk.start()))
    if citm and len(resto[citm.end():].strip()) > 40:
        cands.append(('cit', citm.start()))
    if not cands:
        return resto, []
    kind, pos = min(cands, key=lambda x: x[1])
    if kind == 'mk':
        return resto[:pos].strip(), [resto[pos:].strip()]
    after = resto[citm.end():].strip()
    return resto[:citm.start()].strip(), ['(' + citm.group(1).strip() + ')', '', after]

def lead_groups(s):
    """'(a)(b) resto' -> (['a','b'], 'resto'), casando parenteses balanceados no INICIO da linha."""
    groups, i, s = [], 0, (s or '').strip()
    while i < len(s) and s[i] == '(':
        depth, j = 0, i
        while j < len(s):
            if s[j] == '(':
                depth += 1
            elif s[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= len(s):                      # sem fechamento: nao e' grupo
            break
        groups.append(s[i + 1:j]); i = j + 1
        while i < len(s) and s[i] == ' ':
            i += 1
    return groups, s[i:]

def parse_ensinamento(title_raw, body_lines):
    title = unesc(title_raw).strip()
    fonte = None
    # fonte no titulo: ultimo (...) que pareca citacao
    m = TRAIL_PAREN.search(title)
    if m and is_cit(m.group(1)):
        fonte = m.group(1).strip()
        title = title[:m.start()].strip()
    is_salmo = bool(SALMO_TITLE.search(title))   # salmo: preserva quebras de linha do verso

    paras = split_paras(body_lines)
    # subtitulo: 1o paragrafo EMOLDURADO por ―― (―― Tema ――). Dialogo iniciando com ―― (sem fechar) NAO conta.
    sub = None
    if paras and SUBT.match(unesc(paras[0][0]).strip()):
        sub = re.sub(r'\s+', ' ', re.sub(r'[―—]{2,}', ' ', unesc(' '.join(l.strip() for l in paras[0])))).strip()
        paras = paras[1:]
    texto_parts, exp_list, resumo_list = [], [], []
    referencias = []
    ref_mode = False
    preamb = posf = None
    anexos = []
    pending = None      # campo aguardando corpo no proximo paragrafo
    i = 0
    while i < len(paras):
        para = paras[i]
        mk = MARKER.match(para[0])
        if mk:
            typ = marker_type(mk.group('label'))
            inline = mk.group('rest')
            body_ls = ([inline] if inline.strip() else []) + para[1:]
            if typ == 'anexo':
                anexos.append(clean_anexo(mk.group('label'), body_ls, paras[i+1:]))
                break                                   # anexo engole ate o fim do corpo
            if not body_ls:
                pending = typ; i += 1; continue
            val = clean_italic(body_ls)
            if   typ == 'explicacao': exp_list.append(val)
            elif typ == 'resumo':     resumo_list.append(val)
            elif typ == 'preambulo':  preamb = val if not preamb else preamb + '\n\n' + val
            elif typ == 'posfacio':   posf   = val if not posf   else posf   + '\n\n' + val
            i += 1; continue
        # paragrafo nao-marcador
        if pending:
            val = clean_italic(para)
            if   pending == 'explicacao': exp_list.append(val)
            elif pending == 'resumo':     resumo_list.append(val)
            elif pending == 'preambulo':  preamb = val
            elif pending == 'posfacio':   posf = val
            pending = None; i += 1; continue
        para_txt = clean_romano(para)
        # referencias: bloco que COMECA com lead-in (Artigos de ref/rel, Ensinamento de ref).
        # Misto ("...tendo os seguintes artigos:" no meio) NAO casa -> fica como quote.
        if not ref_mode and REF_LEAD.match(para_txt):
            referencias.append(para_txt.strip('*').strip())      # conserva cabecalho/linha-inline
            after = para_txt.split(':', 1)[1].strip() if ':' in para_txt else ''
            if not (after and ('"' in after or is_cit(after))):
                ref_mode = True                                  # cabecalho-so: itens seguem em paragrafos
            i += 1; continue
        if ref_mode:
            if REF_ITEM.match(para_txt):
                referencias.append(re.sub(r'^[-–—•*\s]+', '', para_txt).strip().strip('*').strip())
                i += 1; continue
            ref_mode = False     # acabou a lista; reprocessa este paragrafo como texto
        # fonte no corpo: 1a LINHA do 1o paragrafo e' uma citacao (...) sozinha.
        # O resto do paragrafo (texto colado sem linha em branco) vira texto.
        # Parenteses BALANCEADOS: "(fonte <..>) Texto... (1952)" nao pode virar fonte inteira
        # (a regra gulosa antiga engolia o ensinamento quando o texto terminava em data entre parenteses).
        if fonte is None and not texto_parts:
            fl = unesc(para[0]).strip()
            groups, rest = lead_groups(fl)
            k = next((j for j, g in enumerate(groups) if is_cit(g)), None)
            if k is not None:
                fonte = groups[k].strip()
                for g in groups[:k]:                     # ex.: (人間の獣性を消滅させる) antes da fonte -> titulo
                    title = (title + ' (' + g.strip() + ')').strip()
                rest = (' '.join('(' + g + ')' for g in groups[k + 1:]) + ' ' + rest).strip()
                # "(Ronbetsu 826 ...) [Zencho Vol. 12, pág. 359] Trecho" -> o [..] e o "Trecho" (抄) sao da fonte
                mb = re.match(r'^(\[[^\]]*\](?:\s*(?:Trecho|抄)\b\.?)?)\s*', rest)
                if mb and is_cit(mb.group(1)) and not groups[k + 1:]:
                    fonte = fonte + ' ' + mb.group(1).strip()
                    rest = rest[mb.end():]
                body = ([rest] if rest else []) + para[1:]
                if body:
                    texto_parts.append((clean_romano_verse if is_salmo else clean_romano)(body))
                i += 1; continue
        texto_parts.append(clean_romano_verse(para) if is_salmo else para_txt)
        i += 1

    texto = '\n\n'.join(texto_parts).strip()
    # data = ultimo (...) do texto que contenha data/ano/Era
    data = None
    md = TRAIL_PAREN.search(texto)
    if md and DATE.search(md.group(1)):
        data = md.group(1).strip()
        texto = texto[:md.start()].rstrip()

    explicacao = '\n\n'.join(e for e in exp_list if e).strip() or None
    resumo = '\n\n'.join(r for r in resumo_list if r).strip() or None
    ens = {
        'fonte': fonte,
        'preambulo': preamb,
        'texto': texto or None,
        'posfacio': posf,
        'data': data,
        'explicacao': explicacao,
        'resumo': resumo,
        'referencias': referencias,
        'notas': [],
        'anexo': anexos,
    }
    return title, sub, ens

# ----------------------------------------------------------------------------
# Notas: renumera [^id] por ensinamento (titulo conta primeiro) e liga as defs.
# ----------------------------------------------------------------------------
NOTE_REF = re.compile(r'\[\^([^\]]+)\]')
IMG_DEF = re.compile(r'^\[(image\d+)\]:\s*<(data:image/[a-z]+;base64,[A-Za-z0-9+/=]+)>\s*$')

def apply_notes(title, ens, defs):
    order, seen = [], set()
    def scan(s):
        for mid in NOTE_REF.findall(s or ''):
            if mid not in seen:
                seen.add(mid); order.append(mid)
    scan(title)
    for f in ('preambulo', 'texto', 'posfacio', 'explicacao'):
        scan(ens.get(f))
    for ax in ens.get('anexo', []):
        scan(ax.get('texto'))
    if not order:
        ens['notas'] = []
        return title
    remap = {mid: i + 1 for i, mid in enumerate(order)}
    def repl(s):
        if not s: return s
        return NOTE_REF.sub(lambda m: '[^%d]' % remap[m.group(1)] if m.group(1) in remap else m.group(0), s)
    title = repl(title)
    for f in ('preambulo', 'texto', 'posfacio', 'explicacao'):
        if ens.get(f): ens[f] = repl(ens[f])
    for ax in ens.get('anexo', []):
        ax['texto'] = repl(ax.get('texto'))
    ens['notas'] = [{'n': remap[mid], 'id': mid, 'texto': defs.get(mid, '')} for mid in order]
    return title

# ----------------------------------------------------------------------------
# Construcao do livro
# ----------------------------------------------------------------------------
def build(files):
    book = {
        'id': 'shin-dendo-tebiki',
        'title': 'Novo Manual de Difusão',
        'titleJa': '新・伝道の手引き',
        'kickerLabel': 'Apostila para Ministros',
        'author': 'Comitê de Compilação das Escrituras',
        'file': 'shin-dendo-tebiki.json',
        'sections': [],
    }
    caps = {}
    stats = {'leaf': 0, 'intro': 0, 'notas': 0, 'fonte': 0, 'anexo': 0, 'explic': 0,
             'resumo': 0, 'refs': 0, 'salmo': 0, 'jp': 0}

    for f in files:
        fn = os.path.basename(f)
        mm = re.match(r'ShinDendo_C(\d)_Item(\d+)\.md', fn)
        if not mm:
            continue
        capn, itemn = mm.group(1), str(int(mm.group(2)))
        lines = open(f, encoding='utf-8').read().split('\n')
        # imagens embutidas (export do Google Docs):  [imageN]: <data:image/...>  -> book['imagens'];
        # no texto fica a referência ![][imageN], que o leitor troca pela imagem.
        for i, ln in enumerate(lines):
            im = IMG_DEF.match(ln)
            if im:
                book.setdefault('imagens', {})[im.group(1)] = im.group(2)
                lines[i] = ''

        # ---- headers crus (limitam os corpos) e secao [## Notas] ----
        heads = []                       # (line_idx, raw_after_hash)
        notas_span = None                # (start, end) das definicoes [^id]:
        for i, ln in enumerate(lines):
            hm = HEAD.match(ln)
            if hm:
                heads.append((i, hm.group(2)))
        head_lines = [h[0] for h in heads]
        def body_span(line_idx):
            nxt = next((h for h in head_lines if h > line_idx), len(lines))
            return lines[line_idx + 1:nxt]
        for (li, raw) in heads:
            if strip_emph(raw).lower() == 'notas':
                nxt = next((h for h in head_lines if h > li), len(lines))
                notas_span = (li + 1, nxt)

        # ---- defs de notas (globais do arquivo) ----
        defs = {}
        if notas_span:
            for ln in lines[notas_span[0]:notas_span[1]]:
                dm = re.match(r'^\s*\[\^([^\]]+)\]:\s*(.*)$', ln)
                if dm:
                    defs[dm.group(1)] = unesc(dm.group(2)).strip()

        # ---- tem Parte real? (existe 'II') ----
        fhp = any(HEAD.match(l) and strip_emph(HEAD.match(l).group(2)).split(' ')[0].rstrip('\\.') == 'II'
                  for l in lines)

        # ---- capitulo / item (com explicacao do intro) ----
        if capn not in caps:
            caps[capn] = {'id': 'c' + capn, 'level': 1, 'nivel': 'capitulo',
                          'marcador': 'Capítulo ' + capn, 'title': '', 'pagina': None,
                          'children': []}
            book['sections'].append(caps[capn])
        cap = caps[capn]
        item = {'id': '%s.i%s' % (cap['id'], itemn), 'level': 2, 'nivel': 'item',
                'marcador': 'Item ' + itemn, 'title': '', 'pagina': None, 'children': []}
        cap['children'].append(item)

        stack = [(1, item)]
        for (li, raw) in heads:
            nivel, marc, resto = classify(raw, fhp)
            if nivel == 'Capitulo':
                t = unesc(resto).split('(')[0].strip()
                cap['title'] = re.sub(r'^Cap[íi]tulo\s*\d+\W*', '', t).strip()
                _, sub, ens = parse_ensinamento('', body_span(li))
                cap['_sub'], cap['_ens'], cap['_defs'] = sub, ens, defs
                continue
            if nivel == 'Item':
                t = unesc(resto).split('(')[0].strip()
                item['title'] = re.sub(r'^Item\s*\d+\W*', '', t).strip()
                item['pagina'] = page_of(fn, raw)
                _, sub, ens = parse_ensinamento('', body_span(li))
                item['_sub'], item['_ens'], item['_defs'] = sub, ens, defs
                continue
            if nivel in (None, 'VAZIO'):
                continue
            rank = RANK[nivel]
            while len(stack) > 1 and stack[-1][0] >= rank:
                stack.pop()
            parent = stack[-1][1]
            node = {'id': parent['id'] + '.' + marc, 'level': parent['level'] + 1,
                    'nivel': NIVEL_PT[nivel], 'marcador': marc, 'title': '',
                    'pagina': page_of(fn, raw), 'children': []}
            title_part, prepend = split_heading(resto)
            title, sub, ens = parse_ensinamento(title_part, prepend + body_span(li))
            node['title'] = title
            node['_sub'], node['_ens'], node['_defs'] = sub, ens, defs
            parent['children'].append(node)
            stack.append((rank, node))

    # ---- 2a passada (apos TODOS os arquivos): atribui subtitulo/ensinamento/explicacao ----
    # Folha -> ensinamento. PAI com conteudo de ensino (texto/preambulo/anexo/...) -> 'ensinamento' (intro)
    # + filhos; pai so com explicacao -> campo 'explicacao'. Nada de intro e' descartado.
    def tally(ens):
        stats['notas'] += len(ens['notas'])
        stats['fonte'] += 1 if ens['fonte'] else 0
        stats['anexo'] += len(ens['anexo'])
        stats['explic'] += 1 if ens['explicacao'] else 0
        stats['resumo'] += 1 if ens.get('resumo') else 0
        stats['refs'] += 1 if ens.get('referencias') else 0

    def finalize(node):
        sub = node.pop('_sub', None)
        ens = node.pop('_ens', None)
        defs = node.pop('_defs', {})
        if sub:
            node['subtitulo'] = sub
        for c in node.get('children', []):
            finalize(c)
        if not ens:
            return
        teaching = (any(ens.get(k) for k in ('fonte', 'preambulo', 'texto', 'posfacio', 'data', 'anexo', 'resumo'))
                    or bool(ens.get('notas')) or bool(ens.get('referencias')))
        attached = False
        if node['children']:
            if teaching:
                node['title'] = apply_notes(node['title'], ens, defs)
                node['ensinamento'] = ens; stats['intro'] += 1; tally(ens); attached = True
            elif ens.get('explicacao'):
                node['explicacao'] = ens['explicacao']
        elif teaching or ens.get('explicacao'):
            node['title'] = apply_notes(node['title'], ens, defs)
            node['ensinamento'] = ens; stats['leaf'] += 1; tally(ens); attached = True
        # tipagem editorial (conservador): salmo por TITULO; jp-pendente por conteudo CJK dominante
        if attached:
            e = node['ensinamento']
            if SALMO_TITLE.search(node.get('title', '')):
                e['tipo'] = 'salmo'; stats['salmo'] += 1
            elif is_jp_only(e.get('texto')) or is_jp_only(e.get('fonte')):
                e['tipo'] = 'jp-pendente'; stats['jp'] += 1

    for cap in book['sections']:
        finalize(cap)

    return book, stats

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    files = sorted(args) if args else sorted(glob.glob('ShinDendo_*.md'))
    book, stats = build(files)
    out = 'shin-dendo-tebiki.json'
    json.dump(book, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    def count(n): return 1 + sum(count(c) for c in n.get('children', []))
    total = sum(count(c) for c in book['sections'])
    print('Livro gravado em', out)
    print('  arquivos:', len(files), '| nos:', total)
    print('  folhas c/ ensinamento: %d | intros de pai c/ ensinamento: %d' % (stats['leaf'], stats['intro']))
    print('  com fonte: %d | com explicacao: %d | com anexo: %d | notas: %d'
          % (stats['fonte'], stats['explic'], stats['anexo'], stats['notas']))
    print('  referencias: %d | resumo: %d | salmo(tipo): %d | jp-pendente(tipo): %d'
          % (stats['refs'], stats['resumo'], stats['salmo'], stats['jp']))

if __name__ == '__main__':
    main()
