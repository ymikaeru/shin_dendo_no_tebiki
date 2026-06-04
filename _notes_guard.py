# -*- coding: utf-8 -*-
"""Guarda de integridade da prosa — Fase B (notas).

Garante a invariante da Fase A ("só ênfase/marcador mudou, NENHUMA palavra"):
a prosa dos dois arquivos, removidos TODOS os tokens de nota, deve ser idêntica.

Normalização (aplicada IGUALMENTE aos dois):
  - corta o bloco final '## Notas' (as defs [^id]: ... diferem de propósito);
  - remove refs de nota   [^id];
  - remove marcadores crus de OCR escapados  \\*1  \\*2  \\*  (NÃO toca em ênfase
    *itálico*/***rótulo***, que é asterisco SEM barra);
  - colapsa espaços.

O que SOBRA como diferença deve ser só o "dígito colado" de marcador
(ex.: backup 'instrumento1'  ->  edição 'instrumento'); QUALQUER outra diferença
(palavra trocada, trecho some/entra) é corrupção de prosa -> FALHA.

Uso:  python _notes_guard.py <antes.md> <depois.md>
"""
import re, sys, difflib

def normalize(t):
    t = re.split(r'(?m)^[ \t]*##[ \t]+Notas[ \t]*$', t)[0]   # tudo antes de '## Notas'
    t = re.sub(r'\[\^[^\]]+\]', '', t)                       # refs de nota [^id]
    t = re.sub(r'==', '', t)                                 # delimitadores de grifo do trecho citado
    t = re.sub(r'\{\{\w+\}\}', '', t)                         # marcas de tipo do anexo {{salmo}} etc.
    t = re.sub(r'\\\*+\d*', '', t)                           # marcadores escapados \*1 \* \*\*
    t = re.sub(r'[ \t]+', ' ', t)
    t = '\n'.join(ln.rstrip() for ln in t.split('\n'))
    return t.split()

def main():
    if len(sys.argv) != 3:
        sys.exit('uso: python _notes_guard.py <antes.md> <depois.md>')
    a = normalize(open(sys.argv[1], encoding='utf-8').read())
    b = normalize(open(sys.argv[2], encoding='utf-8').read())
    if a == b:
        print('OK — prosa idêntica (módulo marcadores). %d palavras.' % len(a))
        return
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    print('!! DIFERENÇAS — confirme que cada uma é só um dígito-colado de marcador:')
    n = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        n += 1
        print('  [%s]' % tag)
        print('    antes : ...%s...' % ' '.join(a[max(0, i1 - 2):i2 + 2]))
        print('    depois: ...%s...' % ' '.join(b[max(0, j1 - 2):j2 + 2]))
    print('(%d bloco(s) de diferença)' % n)
    sys.exit(1)

if __name__ == '__main__':
    main()
