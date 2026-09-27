# -*- coding: utf-8 -*-
"""Gera o SITE PÚBLICO estático (somente leitura) em site/.

O leitor é o mesmo _nav_proto.html do /nav local — aqui ele recebe
window.SD_STATIC=true, que esconde as ferramentas de edição/revisão e os
marcadores de nota pendente, e lê o livro de book.json (sem servidor Python).

Uso (na raiz):  python tools/build_site.py            -> site/
                python -m http.server -d site 8080    -> testar em localhost:8080
Publicação: .github/workflows/pages.yml roda isto e publica no GitHub Pages.
"""
import os, json, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'site')

HEAD_EXTRA = '''<meta name="description" content="Novo Manual de Difusão (新・伝道の手引き) — apostila de estudo navegável: busca no texto completo, notas e referências cruzadas.">
<meta property="og:title" content="Novo Manual de Difusão — 新・伝道の手引き">
<meta name="robots" content="noindex">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📖</text></svg>">
<script>window.SD_STATIC=true;</script>
'''


def main():
    html = open(os.path.join(ROOT, '_nav_proto.html'), encoding='utf-8').read()
    html = html.replace('<title>Apostila — protótipo de navegação</title>',
                        '<title>Novo Manual de Difusão — 新・伝道の手引き</title>', 1)
    assert '</head>' in html
    html = html.replace('</head>', HEAD_EXTRA + '</head>', 1)
    book = json.load(open(os.path.join(ROOT, 'shin-dendo-tebiki.json'), encoding='utf-8'))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)
    with open(os.path.join(OUT, 'book.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(book, f, ensure_ascii=False, separators=(',', ':'))
    open(os.path.join(OUT, '.nojekyll'), 'w').close()

    size = sum(os.path.getsize(os.path.join(OUT, x)) for x in os.listdir(OUT))
    print('site gerado em %s (%d arquivos, %.1f MB)' % (os.path.relpath(OUT), len(os.listdir(OUT)), size / 1e6))


if __name__ == '__main__':
    main()
