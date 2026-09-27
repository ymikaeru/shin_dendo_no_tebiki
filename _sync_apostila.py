# -*- coding: utf-8 -*-
"""Loop de iteração da apostila Shin Dendō (branch feat/apostila-shin-dendo).

Regenera o JSON e copia pros 3 destinos do site:
  - data/books/            (repo — vai pro commit/publicação)
  - site_data/books/       (revisão LOCAL deslogado; gitignored)
  - .local-edits/teachings/books/  (espelho p/ `npm run storage:push`)

Uso:
    python _sync_apostila.py            # regenera (8 arquivos) + copia + valida
    python _sync_apostila.py --check    # também roda a conservação
    python _sync_apostila.py --publish  # + commita o JSON no repo do site (falta só o git push)

Depois:
    revisar LOCAL (deslogado):  localhost:<porta>/reader.html?pub=disciples&book=shin-dendo-tebiki
    subir pro Supabase:         (em caminho_da_felicidade) npm run storage:push -- --confirm
"""
import os, sys, shutil, subprocess, json

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, '..', 'caminho_da_felicidade')
BOOK = 'shin-dendo-tebiki.json'
DESTS = [
    os.path.join(SITE, 'data', 'books'),                       # repo + revisão local (hook localhost lê daqui)
    os.path.join(SITE, '.local-edits', 'teachings', 'books'),  # espelho p/ storage:push (na publicação)
]

def main():
    # 1. regenera o livro (todos os 8)
    print('▶ regenerando', BOOK, '...')
    r = subprocess.run([sys.executable, '_build_book.py'], cwd=HERE)
    if r.returncode != 0:
        sys.exit('!! _build_book.py falhou')
    src = os.path.join(HERE, BOOK)
    json.load(open(src, encoding='utf-8'))   # valida JSON

    # 2. conservação opcional
    if '--check' in sys.argv:
        print('▶ conservação:')
        subprocess.run([sys.executable, '_conserva.py'], cwd=HERE)

    # 3. copia pros 3 destinos
    for d in DESTS:
        if not os.path.isdir(d):
            print('  (pulado, não existe):', d); continue
        shutil.copy2(src, os.path.join(d, BOOK))
        print('  ✓ copiado →', os.path.relpath(os.path.join(d, BOOK), SITE))

    print('\nRevisar LOCAL (deslogado): shin-dendo.html  (leitor de estudo publicado, lê data/books/ do repo)')
    print('  (reserva antiga: reader.html?pub=disciples&book=shin-dendo-tebiki)')

    # 4. publicação opcional: commita o JSON no repo do site (1 comando git por vez,
    # em foreground — git nesta máquina já travou com comandos em background)
    if '--publish' in sys.argv:
        rel = 'data/books/' + BOOK
        print('\n▶ publicando (git em %s):' % os.path.abspath(SITE))
        r = subprocess.run(['git', 'add', rel], cwd=SITE)
        if r.returncode != 0:
            sys.exit('!! git add falhou — se travou: matar git.exe orfao e remover .git/index.lock')
        r = subprocess.run(['git', 'commit', '-m', 'chore(shin-dendo): atualiza conteudo da apostila'], cwd=SITE)
        if r.returncode != 0:
            print('  (nada novo para commitar — JSON identico ao ultimo commit)')
        else:
            print('  ✓ commitado. Falta: git push (e merge pro main, se estiver em branch)')
    else:
        print('Publicar: python _sync_apostila.py --publish   (commita o JSON no repo do site)')

if __name__ == '__main__':
    main()
