# -*- coding: utf-8 -*-
"""
Editor lado-a-lado Shin Dendo: scan original (esq) x texto .md editavel (dir).
Roda local, so com a biblioteca padrao do Python.

Uso:  python servidor.py     ->  abre http://localhost:8000
"""
import http.server, socketserver, json, os, re, glob, shutil, webbrowser, threading, time, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SCAN_DIR = os.path.join(ROOT, 'CZUR_Scan')
MAP_FILE = os.path.join(ROOT, '_editor_map.json')
BACKUP_DIR = os.path.join(ROOT, '_backup_editor')
PORT = 8000

SAFE_MD = re.compile(r'^ShinDendo_[A-Za-z0-9_]+\.md$')
SAFE_IMG = re.compile(r'^[A-Za-z0-9_.\-]+\.(jpg|jpeg|png)$', re.I)
_WLOCK = threading.Lock()   # serializa as gravacoes no .md (evita corrida de write/regen)


def md_files():
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, 'ShinDendo_*.md')))


def scan_files():
    if not os.path.isdir(SCAN_DIR):
        return []
    return sorted(f for f in os.listdir(SCAN_DIR) if SAFE_IMG.match(f))


def _md_pat(catchword):
    """Regex que casa o catchword no .md tolerando escapes \\x e espaços/quebras."""
    def ch(c):
        if c == ' ':
            return r'\s+'
        if c.isalnum():
            return re.escape(c)
        return r'\\?' + re.escape(c)
    return ''.join(ch(c) for c in catchword)


def set_grifo(name, ref_id, catchword):
    """Move o marcador [^ref_id] para envolver `catchword` (==trecho==[^ref_id]) onde o
    trecho estiver no ensinamento — ANTES ou DEPOIS da posicao atual do marcador (acha a
    ocorrencia mais proxima). catchword vazio = remove o grifo (mantem o marcador onde esta).
    Trava de prosa; backup; regenera o JSON. Devolve (ok, msg)."""
    import _notes_guard as G
    path = os.path.join(ROOT, name)
    md = open(path, encoding='utf-8').read()
    ref = '[^%s]' % ref_id
    mpos = md.find(ref)
    if mpos < 0:
        return False, 'nota nao encontrada no arquivo'
    before, after = md[:mpos], md[mpos + len(ref):]
    mx = re.search(r'==([^=]+?)==([^\[\n=]*)$', before)        # grifo antigo (==...== antes do marcador)
    if mx:
        before = before[:mx.start()] + mx.group(1) + mx.group(2)
    old_anchor = len(before)                                   # onde o marcador estava (sem o grifo antigo)
    clean = before + after                                     # .md sem o marcador nem o grifo desta nota
    catchword = re.sub(r'\s+', ' ', (catchword or '')).strip()
    if not catchword:
        new_md = before + ref + after                          # limpa o grifo, mantem o marcador
    else:
        ls = md.rfind('\n', 0, mpos) + 1                       # nota no titulo (heading)?
        if md[ls:ls + 1] == '#':
            return False, 'essa nota esta no titulo — o titulo inteiro ja acende ao passar o mouse (nao precisa grifar)'
        cands = list(re.finditer(_md_pat(catchword), clean))
        if not cands:
            return False, 'trecho nao encontrado no corpo deste ensinamento'
        m2 = min(cands, key=lambda mm: abs(mm.start() - old_anchor))   # ocorrencia mais proxima do marcador
        idx, actual = m2.start(), m2.group(0)
        new_md = clean[:idx] + '==' + actual + '==' + ref + clean[idx + len(actual):]
    if G.normalize(md) != G.normalize(new_md):
        return False, 'a mudanca alteraria a prosa — abortado'
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(path, os.path.join(BACKUP_DIR, name + '.' + str(int(time.time()))))
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new_md)
    subprocess.run([sys.executable, '_build_book.py'], cwd=ROOT, capture_output=True)
    return True, 'ok'


def set_notetext(name, ref_id, text):
    """Substitui o texto da definicao [^ref_id]: ... no bloco ## Notas do .md
    (re-traducao da nota). Backup + regenera o JSON. A prosa do corpo nao muda."""
    path = os.path.join(ROOT, name)
    md = open(path, encoding='utf-8').read()
    text = re.sub(r'\s+', ' ', (text or '')).strip()
    pat = re.compile(r'(?m)^(\[\^' + re.escape(ref_id) + r'\]:).*$')
    if not pat.search(md):
        return False, 'definicao da nota nao encontrada'
    new_md = pat.sub(lambda m: m.group(1) + ' ' + text, md, count=1)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(path, os.path.join(BACKUP_DIR, name + '.' + str(int(time.time()))))
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new_md)
    subprocess.run([sys.executable, '_build_book.py'], cwd=ROOT, capture_output=True)
    return True, 'ok'


def add_note(name, node_id, catchword, text):
    """Cria nota NOVA: envolve o trecho com ==trecho==[^novoid] (consumindo um marcador
    OCR cru logo apos, se houver) e adiciona a def no bloco ## Notas. Devolve (ok, msg/id)."""
    path = os.path.join(ROOT, name)
    md = open(path, encoding='utf-8').read()
    catchword = re.sub(r'\s+', ' ', (catchword or '')).strip()
    text = re.sub(r'\s+', ' ', (text or '')).strip()
    if not catchword:
        return False, 'selecione o trecho da nota no corpo'
    cands = list(re.finditer(_md_pat(catchword), md))
    if not cands:
        return False, 'trecho nao encontrado no texto'
    if len(cands) > 1:
        return False, 'trecho aparece em mais de um lugar — selecione um trecho mais especifico'
    mm = cands[0]; idx, actual = mm.start(), mm.group(0); end = idx + len(actual)
    mk = re.match(r'\\?\*?\d+', md[end:end + 6])           # marcador OCR cru logo apos (1, *3, \\*2)
    raw = mk.group(0) if mk else ''
    parts = node_id.split('.')
    pref = (parts[0] + parts[1] + '-' + '-'.join(parts[2:])) if len(parts) >= 2 else node_id
    nums = [int(x) for x in re.findall(r'\[\^' + re.escape(pref) + r'-(\d+)\]', md)]
    ref = '[^%s-%d]' % (pref, (max(nums) + 1) if nums else 1)
    new_body = md[:idx] + '==' + actual + '==' + ref + md[end + len(raw):]
    if new_body.replace('==' + actual + '==' + ref, actual + raw, 1) != md:   # reversivel = mudou so o marcador
        return False, 'mudanca inesperada no corpo — abortado'
    defline = '%s: %s' % (ref, text)
    nm = re.search(r'(?m)^##\s+Notas\s*$', new_body)
    if nm:
        defs = list(re.finditer(r'(?m)^\[\^[^\]]+\]:.*$', new_body[nm.end():]))
        if defs:
            pos = nm.end() + defs[-1].end()
            new_md = new_body[:pos] + '\n' + defline + new_body[pos:]
        else:
            new_md = new_body[:nm.end()] + '\n\n' + defline + new_body[nm.end():]
    else:
        new_md = new_body.rstrip() + '\n\n## Notas\n\n' + defline + '\n'
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(path, os.path.join(BACKUP_DIR, name + '.' + str(int(time.time()))))
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new_md)
    subprocess.run([sys.executable, '_build_book.py'], cwd=ROOT, capture_output=True)
    return True, ref


def set_anexotag(name, catchword, tag):
    """Marca o TIPO de um bloco do anexo: prefixa {{tag}} na linha (removendo tag anterior).
    tag 'auto'/vazio = remove a marca (volta pra auto-deteccao). So mexe nesses marcadores."""
    path = os.path.join(ROOT, name)
    md = open(path, encoding='utf-8').read()
    catchword = re.sub(r'^\{\{\w+\}\}\s*', '', re.sub(r'\s+', ' ', (catchword or '')).strip()).strip()
    if not catchword:
        return False, 'bloco vazio'
    cands = list(re.finditer(_md_pat(catchword), md))
    if not cands:
        return False, 'bloco nao encontrado'
    if len(cands) > 1:
        return False, 'bloco aparece em mais de um lugar — selecione um mais especifico'
    idx = cands[0].start(); pre = md[:idx]
    me = re.search(r'\{\{\w+\}\}\s*$', pre)
    if me:
        pre = pre[:me.start()]
    marker = '' if (not tag or tag == 'auto') else ('{{%s}}' % tag)
    new_md = pre + marker + md[idx:]
    if re.sub(r'\{\{\w+\}\}', '', new_md) != re.sub(r'\{\{\w+\}\}', '', md):
        return False, 'mudanca inesperada (so deveria mudar a marca de tipo)'
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(path, os.path.join(BACKUP_DIR, name + '.' + str(int(time.time()))))
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new_md)
    subprocess.run([sys.executable, '_build_book.py'], cwd=ROOT, capture_output=True)
    return True, (tag or 'auto')


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silencioso

    def _send(self, code, ctype, body):
        if isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, 'application/json; charset=utf-8', json.dumps(obj, ensure_ascii=False))

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs, unquote
        u = urlparse(self.path)
        path, q = u.path, parse_qs(u.query)
        try:
            if path in ('/', '/editor.html'):
                with open(os.path.join(ROOT, 'editor.html'), encoding='utf-8') as f:
                    return self._send(200, 'text/html; charset=utf-8', f.read())
            if path == '/nav':
                with open(os.path.join(ROOT, '_nav_proto.html'), encoding='utf-8') as f:
                    return self._send(200, 'text/html; charset=utf-8', f.read())
            if path == '/_tree.json':
                with open(os.path.join(ROOT, '_tree.json'), encoding='utf-8') as f:
                    return self._send(200, 'application/json; charset=utf-8', f.read())
            if path == '/_book.json':
                bp = os.path.join(ROOT, 'shin-dendo-tebiki.json')
                if not os.path.isfile(bp):
                    return self._send(404, 'text/plain', 'sem book')
                with open(bp, encoding='utf-8') as f:
                    return self._send(200, 'application/json; charset=utf-8', f.read())
            if path == '/api/files':
                return self._json({'files': md_files()})
            if path == '/api/scans':
                return self._json({'scans': scan_files()})
            if path == '/api/file':
                name = (q.get('name') or [''])[0]
                if not SAFE_MD.match(name or ''):
                    return self._json({'error': 'nome invalido'}, 400)
                with open(os.path.join(ROOT, name), encoding='utf-8') as f:
                    return self._json({'name': name, 'content': f.read()})
            if path == '/api/proposals':
                import _notes_review as R
                q = R.load()
                return self._json({'items': q['items'], 'summary': R.summary(q)})
            if path == '/api/map':
                data = {}
                if os.path.exists(MAP_FILE):
                    with open(MAP_FILE, encoding='utf-8') as f:
                        data = json.load(f)
                return self._json(data)
            if path.startswith('/scan/'):
                fn = unquote(path[len('/scan/'):])
                if not SAFE_IMG.match(fn):
                    return self._send(400, 'text/plain', 'nome invalido')
                fp = os.path.join(SCAN_DIR, fn)
                if not os.path.isfile(fp):
                    return self._send(404, 'text/plain', 'nao encontrado')
                with open(fp, 'rb') as f:
                    return self._send(200, 'image/jpeg', f.read())
            return self._send(404, 'text/plain', 'rota desconhecida')
        except Exception as e:
            return self._json({'error': str(e)}, 500)

    def do_POST(self):
        ln = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(ln).decode('utf-8') if ln else '{}'
        try:
            body = json.loads(raw)
        except Exception:
            return self._json({'error': 'json invalido'}, 400)
        u = self.path
        _WLOCK.acquire()
        try:
            if u == '/api/save':
                name = body.get('name', '')
                content = body.get('content', '')
                if not SAFE_MD.match(name):
                    return self._json({'error': 'nome invalido'}, 400)
                os.makedirs(BACKUP_DIR, exist_ok=True)
                src = os.path.join(ROOT, name)
                # TRAVA ANTI-CLOBBER (server-side, vale p/ qualquer cliente): recusa gravar se o
                # texto enviado APAGARIA notas [^id] que existem no disco (buffer desatualizado).
                # Remover nota e' tarefa do /nav (outros endpoints), nunca do editor de texto.
                if os.path.exists(src) and not body.get('force'):
                    disk = open(src, encoding='utf-8').read()
                    # conta so ANCORAS no corpo ([^id] sem ':' depois) — ignora as defs [^id]: do bloco ## Notas
                    anchors = lambda t: set(re.findall(r'\[\^([^\]]+)\](?!:)', t))
                    lost = anchors(disk) - anchors(content)
                    if lost:
                        return self._json({'ok': False, 'error': 'stale', 'lost': sorted(lost),
                            'msg': 'Gravacao recusada: este texto apagaria %d nota(s) que existem no disco (%s). '
                                   'O editor esta com uma versao desatualizada — recarregue a pagina (F5) e refaca a edicao.'
                                   % (len(lost), ', '.join(sorted(lost)[:6]))}, 409)
                if os.path.exists(src):
                    stamp = str(int(time.time()))
                    shutil.copy2(src, os.path.join(BACKUP_DIR, name + '.' + stamp))
                with open(src, 'w', encoding='utf-8', newline='') as f:
                    f.write(content)
                subprocess.run([sys.executable, '_build_book.py'], cwd=ROOT, capture_output=True)  # /nav atualiza sozinho
                return self._json({'ok': True})
            if u == '/api/map':
                with open(MAP_FILE, 'w', encoding='utf-8') as f:
                    json.dump(body, f, ensure_ascii=False, indent=1)
                return self._json({'ok': True})
            if u == '/api/grifo':
                name = body.get('name', ''); ref_id = body.get('refId', ''); cw = body.get('catchword', '')
                if not SAFE_MD.match(name or ''):
                    return self._json({'error': 'nome invalido'}, 400)
                if not re.match(r'^[A-Za-z0-9_\-]+$', ref_id or ''):
                    return self._json({'error': 'id invalido'}, 400)
                ok, msg = set_grifo(name, ref_id, cw)
                return self._json({'ok': ok, 'msg': msg}, 200 if ok else 400)
            if u == '/api/notetext':
                name = body.get('name', ''); ref_id = body.get('refId', ''); text = body.get('text', '')
                if not SAFE_MD.match(name or ''):
                    return self._json({'error': 'nome invalido'}, 400)
                if not re.match(r'^[A-Za-z0-9_\-]+$', ref_id or ''):
                    return self._json({'error': 'id invalido'}, 400)
                ok, msg = set_notetext(name, ref_id, text)
                return self._json({'ok': ok, 'msg': msg}, 200 if ok else 400)
            if u == '/api/addnote':
                name = body.get('name', ''); node_id = body.get('nodeId', ''); cw = body.get('catchword', ''); text = body.get('text', '')
                if not SAFE_MD.match(name or ''):
                    return self._json({'error': 'nome invalido'}, 400)
                if not re.match(r'^[A-Za-z0-9.]+$', node_id or ''):
                    return self._json({'error': 'nodeId invalido'}, 400)
                ok, msg = add_note(name, node_id, cw, text)
                return self._json({'ok': ok, 'msg': msg}, 200 if ok else 400)
            if u == '/api/anexotag':
                name = body.get('name', ''); cw = body.get('catchword', ''); tag = body.get('tag', '')
                if not SAFE_MD.match(name or ''):
                    return self._json({'error': 'nome invalido'}, 400)
                if tag and not re.match(r'^[a-z]+$', tag):
                    return self._json({'error': 'tag invalida'}, 400)
                ok, msg = set_anexotag(name, cw, tag)
                return self._json({'ok': ok, 'msg': msg}, 200 if ok else 400)
            if u == '/api/proposal':
                # fila de notas propostas: approve | drop (marcador espurio) | status (rejeitar/reabrir/editar)
                import _notes_review as R
                pid = body.get('id', ''); action = body.get('action', '')
                if not re.match(r'^p\d{4,}$', pid or ''):
                    return self._json({'error': 'id invalido'}, 400)
                try:
                    if action == 'approve':
                        p = R.approve(pid, body.get('texto', ''), body.get('trecho', ''))
                    elif action == 'drop':
                        p = R.drop_marker(pid)
                    elif action == 'status':
                        p = R.set_status(pid, body.get('status'), texto=body.get('texto'),
                                         trecho=body.get('trecho'), obs=body.get('obs'))
                    else:
                        return self._json({'error': 'acao invalida'}, 400)
                except (ValueError, KeyError) as e:
                    return self._json({'ok': False, 'msg': str(e).strip("'")}, 400)
                return self._json({'ok': True, 'item': p})
            return self._json({'error': 'rota desconhecida'}, 404)
        except Exception as e:
            return self._json({'error': str(e)}, 500)
        finally:
            _WLOCK.release()


class Reusable(socketserver.ThreadingTCPServer):   # threaded (nao bloqueia leituras); writes serializados pelo _WLOCK
    allow_reuse_address = True
    daemon_threads = True


def main():
    os.chdir(ROOT)
    with Reusable(('127.0.0.1', PORT), Handler) as httpd:
        url = 'http://localhost:%d' % PORT
        print('Editor Shin Dendo rodando em', url)
        print('  arquivos .md :', len(md_files()))
        print('  scans        :', len(scan_files()), 'em', SCAN_DIR)
        print('Ctrl+C para parar.')
        threading.Thread(target=lambda: (time.sleep(0.8), webbrowser.open(url)), daemon=True).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nparado.')


if __name__ == '__main__':
    main()
