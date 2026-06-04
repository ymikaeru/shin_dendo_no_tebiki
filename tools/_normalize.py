# -*- coding: utf-8 -*-
"""
Analisador/normalizador de hierarquia para os .md do Shin Dendo.

FASE A (estrutura). Por enquanto roda em modo RELATORIO (nao escreve):
- classifica cada titulo pelo TIPO de marcador (Item / Parte I. / Numero 1. /
  Circulo (1) / romano i. / Letra A. / letra a.)
- calcula a profundidade logica "compactada por arquivo" (sem buracos)
- sinaliza titulos vazios, nao-classificados e saltos de nivel
"""
import re, sys, glob, os

# (1)..(20) circulados -> 1..20
CIRCLED = {chr(c): i + 1 for i, c in enumerate(range(0x2460, 0x2474))}

ROMAN_UP = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX']
ROMAN_LO = [r.lower() for r in ROMAN_UP]

# ordem canonica dos niveis (Capitulo sai para titulo/frontmatter)
ORDER = ['Item', 'Parte', 'Numero', 'Circulo', 'romano', 'Letra', 'letra']

HEAD_RE = re.compile(r'^(#{1,6})[ \t]*(.*?)[ \t]*$')

def strip_emph(s):
    # remove asteriscos/barras de enfase e lixo de rodape nas pontas
    s = s.strip()
    s = re.sub(r'^[\*\\\s]+', '', s)
    s = re.sub(r'[\*\\\s]+$', '', s)
    return s.strip()

def classify(raw_title, file_has_parte=False):
    """Retorna (nivel, marcador_norm, resto) ou (None, None, titulo) se nao for marcador.
    file_has_parte: True se o arquivo contem um titulo 'II.' (prova de nivel Parte real)."""
    t = strip_emph(raw_title)
    if not t:
        return ('VAZIO', '', '')

    # Capitulo / Item
    m = re.match(r'^Cap[íi]tulo\b', t)
    if m:
        return ('Capitulo', 'Cap', t)
    m = re.match(r'^Item\b', t)
    if m:
        return ('Item', 'Item', t)

    # Circulo (1)(2)...
    if t[0] in CIRCLED:
        return ('Circulo', str(CIRCLED[t[0]]), t[1:].strip())

    # primeiro token + separador (espaco, ponto, ponto-escapado)
    m = re.match(r'^([A-Za-z]+|\d+)\\?\.?[ \t)]', t + ' ')
    token = m.group(1) if m else None
    if token is None:
        # tenta token sozinho colado (ex.: "1A..." improvavel) -> nao classifica
        return (None, None, t)

    rest = t[m.end()-1:].strip() if m else t

    # Numero arabico
    if token.isdigit():
        return ('Numero', token, rest)

    low = token.lower()

    # Romano MAIUSCULO -> Parte, mas SO se o arquivo tem nivel Parte real
    # (existe um 'II'). Um 'I'/'V'/'X' solitario num arquivo sem Parte e,
    # na verdade, uma LETRA (ex.: ...H, I, J, K).
    if token in ROMAN_UP and file_has_parte:
        return ('Parte', token, rest)
    if len(token) > 1 and token in ROMAN_UP:
        return ('Parte', token, rest)          # 'II','III'... sempre Parte

    # romano minusculo (i, ii, iii, iv, v, vi...) -> romano.
    # letra minuscula usa a-h (pula i/v/x), entao i/v/x sozinhos = romano.
    if low in ROMAN_LO and (len(low) > 1 or low in ('i', 'v', 'x')):
        return ('romano', low, rest)

    # Letra isolada
    if len(token) == 1:
        if token.isupper():
            return ('Letra', token, rest)      # A. B. C. ... (inclui 'I' sem Parte)
        else:
            return ('letra', token, rest)      # a. b. c. ...

    # token de varias letras que nao e romano -> nao e marcador estrutural
    return (None, None, t)

def analyze(path):
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()

    # pre-varredura: o arquivo tem nivel Parte real? (existe um titulo 'II')
    file_has_parte = False
    for line in lines:
        m = HEAD_RE.match(line.rstrip('\n'))
        if m and strip_emph(m.group(2)).split(' ')[0].rstrip('\\.') == 'II':
            file_has_parte = True
            break

    heads = []  # (lineno, hashes, nivel, marcador, resto, raw)
    levels_present = set()
    for i, line in enumerate(lines, 1):
        m = HEAD_RE.match(line.rstrip('\n'))
        if not m:
            continue
        hashes, title = m.group(1), m.group(2)
        nivel, marc, resto = classify(title, file_has_parte)
        heads.append([i, len(hashes), nivel, marc, resto, title])
        if nivel in ORDER:
            levels_present.add(nivel)

    # mapeia niveis presentes -> profundidade compactada 1..k (ordem canonica)
    present_sorted = [lv for lv in ORDER if lv in levels_present]
    depth_of = {lv: idx + 1 for idx, lv in enumerate(present_sorted)}
    overflow = {lv for lv, d in depth_of.items() if d > 6}

    print('=' * 78)
    print(os.path.basename(path))
    print('  niveis presentes (ordem):', ' > '.join(present_sorted),
          '   [%d niveis]' % len(present_sorted))
    if overflow:
        print('  *** OVERFLOW (>6, vira NEGRITO):', ', '.join(overflow))
    print('-' * 78)

    prev_depth = 0
    for (ln, h, nivel, marc, resto, raw) in heads:
        if nivel == 'VAZIO':
            print('  L%-5d [VAZIO]  %s  -> APAGAR' % (ln, '#' * h))
            continue
        if nivel is None:
            print('  L%-5d [??????]  %s %s' % (ln, '#' * h, raw[:60]))
            continue
        if nivel == 'Capitulo':
            print('  L%-5d Capitulo  %s -> TITULO/frontmatter  | %s' % (ln, '#' * h, resto[:50]))
            continue
        nd = depth_of[nivel]
        if nivel in overflow:
            newmark = '**negrito**'
        else:
            newmark = '#' * nd
        jump = ''
        if prev_depth and nd > prev_depth + 1:
            jump = '  <<< SALTO de nivel (%d->%d)' % (prev_depth, nd)
        prev_depth = nd
        print('  L%-5d %-8s %s->%-7s %s%s' %
              (ln, nivel, '#' * h, newmark, (marc + ' ' + resto)[:46], jump))

def compute(lines):
    """Retorna (file_has_parte, depth_of, overflow, heads)."""
    file_has_parte = False
    for line in lines:
        m = HEAD_RE.match(line.rstrip('\n'))
        if m and strip_emph(m.group(2)).split(' ')[0].rstrip('\\.') == 'II':
            file_has_parte = True
            break
    heads, levels_present = [], set()
    for i, line in enumerate(lines):
        m = HEAD_RE.match(line.rstrip('\n'))
        if not m:
            continue
        nivel, marc, resto = classify(m.group(2), file_has_parte)
        heads.append((i, len(m.group(1)), nivel, marc, resto))
        if nivel in ORDER:
            levels_present.add(nivel)
    present = [lv for lv in ORDER if lv in levels_present]
    depth_of = {lv: idx + 1 for idx, lv in enumerate(present)}
    overflow = {lv for lv, d in depth_of.items() if d > 6}
    return file_has_parte, depth_of, overflow, heads


def transform(path):
    """Fase A: reescreve profundidade dos titulos por tipo de marcador,
    rebaixa overflow para negrito, remove titulos vazios. NAO mexe em
    marcadores editoriais nem em ancoras de nota."""
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()
    fhp, depth_of, overflow, _ = compute(lines)

    out, n_empty, n_rehash, n_bold = [], 0, 0, 0
    for line in lines:
        raw = line.rstrip('\n')
        m = HEAD_RE.match(raw)
        if not m:
            out.append(line)
            continue
        hashes, title = m.group(1), m.group(2)
        nivel, marc, resto = classify(title, fhp)

        if nivel == 'VAZIO':
            n_empty += 1
            continue                      # remove a linha vazia
        if nivel in ('Capitulo', None):
            out.append(line)              # Capitulo e nao-titulos: intactos
            continue

        nd = depth_of[nivel]
        tail = raw[len(hashes):]          # texto do titulo, byte a byte
        if nivel in overflow:             # vira negrito run-in
            txt = strip_emph(tail)
            out.append('**' + txt + '**\n')
            n_bold += 1
        else:
            new = '#' * nd + tail
            out.append(new + '\n')
            if nd != len(hashes):
                n_rehash += 1

    text = ''.join(out)
    text = re.sub(r'\n{3,}', '\n\n', text)   # colapsa linhas em branco extras
    return text, n_empty, n_rehash, n_bold


if __name__ == '__main__':
    args = sys.argv[1:]
    write = '--write' in args
    files = [a for a in args if not a.startswith('--')]
    if not files:
        files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), 'ShinDendo_*.md')))
    if write:
        for p in files:
            text, ne, nr, nb = transform(p)
            with open(p, 'w', encoding='utf-8', newline='') as f:
                f.write(text)
            print('%-32s reprofundados=%-4d negrito=%-4d vazios_removidos=%d'
                  % (os.path.basename(p), nr, nb, ne))
    else:
        for p in files:
            analyze(p)
