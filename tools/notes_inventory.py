# -*- coding: utf-8 -*-
"""Inventário dos marcadores crus de nota (\\*N) -> fila _notes_proposals.json.

Cada marcador vira uma VAGA (status 'sem-fonte') com o nó do ensinamento, o
contexto e um palpite de trecho. Rodar de novo é seguro: preserva status/texto
das vagas já trabalhadas e só acrescenta as novas.

Uso (na raiz):  python tools/notes_inventory.py          -> atualiza a fila + resumo
                python tools/notes_inventory.py --dry    -> só mostra o resumo
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import _notes_review as R


def main():
    items = R.scan_markers()
    q = R.merge_inventory(items)
    if '--dry' not in sys.argv:
        R.save(q)
        print('fila gravada em', os.path.relpath(R.QUEUE))
    print('marcadores crus no .md: %d' % len(items))
    print('%-24s %9s %9s %9s %9s %9s' % ('arquivo', 'pendente', 'sem-fonte', 'aprovada', 'rejeitada', 'descart.'))
    for fn, d in sorted(R.summary(q).items()):
        print('%-24s %9d %9d %9d %9d %9d' % (fn, d['pendente'], d['sem-fonte'], d['aprovada'], d['rejeitada'], d['descartada']))


if __name__ == '__main__':
    main()
