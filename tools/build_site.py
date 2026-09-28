# -*- coding: utf-8 -*-
"""Gera o SITE PÚBLICO estático (somente leitura) em site/.

O leitor é o mesmo _nav_proto.html do /nav local — aqui ele recebe
window.SD_STATIC=true, que esconde as ferramentas de edição/revisão e os
marcadores de nota pendente, e lê o livro de book.json (sem servidor Python).

Uso (na raiz):  python tools/build_site.py            -> site/
                python -m http.server -d site 8080    -> testar em localhost:8080
Publicação: .github/workflows/pages.yml roda isto e publica no GitHub Pages.

Acesso: igual ao Mioshie-Shu e ao Kōwa-hen (mesmo domínio www.cmu.org.br) — auth.js no <head> manda para
login.html quem não entrou; mesma senha (só o hash SHA-256 fica no código) e mesma chave de sessão
(mioshie_shu_auth; quem entrou pela Zenshu, mioshie_auth, também passa): um login vale para os três sites
na mesma aba. Para trocar a senha, troque AUTH_HASH aqui e nos outros dois sites. A trava é só no navegador:
impede a navegação casual, mas quem souber o endereço de book.json ainda consegue baixá-lo.
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

# ---- acesso (mesma senha e mesma sessão do Mioshie-Shu e do Kōwa-hen) ----
AUTH_HASH = '925933144f0b01b062954b29d2dc665c63d5e15083d31d30e35536859bc1f787'
FAVICON = '<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📖</text></svg>">'

# Carregado de forma síncrona no começo do <head>: HTTPS, senha e o botão "Sair".
AUTH_JS = '''// Login compartilhado com o Mioshie-Shu e o Kōwa-hen (mesmo domínio): mesma senha, mesma chave de sessão;
// quem entrou pela Zenshu (chave mioshie_auth) também é aceito. Gerado por tools/build_site.py.
(function () {
  var HASH = '%s';
  if (location.protocol === 'http:' && !/^(localhost|127\\.|\\[::1\\])/.test(location.hostname)) {
    location.replace('https:' + location.href.slice(5)); // crypto.subtle (login) só funciona em contexto seguro
    return;
  }
  if (/login\\.html$/.test(location.pathname)) return;
  var ok = false;
  try {
    ok = sessionStorage.getItem('mioshie_shu_auth') === HASH || sessionStorage.getItem('mioshie_auth') === 'true';
  } catch (e) { /* sem storage */ }
  if (!ok) {
    // volta para o mesmo ensinamento depois de entrar (#c1.i1.2)
    var pag = location.pathname.split('/').pop() || 'index.html';
    location.replace('login.html?redirect=' + encodeURIComponent(pag + location.search + location.hash));
    return;
  }
  document.addEventListener('DOMContentLoaded', function () {
    var b = document.getElementById('sairBtn');
    if (b) b.onclick = function () {
      try { sessionStorage.removeItem('mioshie_shu_auth'); sessionStorage.removeItem('mioshie_auth'); } catch (e) { /* sem storage */ }
      location.replace('login.html');
    };
  });
})();
''' % AUTH_HASH

LOGIN_HTML = '''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<script src="auth.js"></script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Entrar · Novo Manual de Difusão</title>
%s
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Literata:opsz,wght@7..72,600&display=swap" rel="stylesheet">
<style>
  /* cores do leitor (papel/bronze; escuro se o leitor estiver no escuro) */
  :root { --bg:#faf7f0; --bg-2:#f3eee3; --card:#fffdf8; --line:#e5ddcc; --mut:#8a7f70; --fg:#2a2520; --acc:#9c6b28; --acc-soft:#f2e6cc; --on-acc:#fff;
    --serif:'Literata','Noto Serif JP',Georgia,serif; --sans:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif; }
  html.dark { --bg:#16171a; --bg-2:#1b1c20; --card:#1f2125; --line:#2d3036; --mut:#948b7e; --fg:#e8e3da; --acc:#d7aa5f; --acc-soft:#3a2f1d; --on-acc:#16171a; }
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; color: var(--fg); font: 15px/1.5 var(--sans);
    background: linear-gradient(145deg, var(--bg) 0%%, var(--bg-2) 100%%); }
  .cartao-login { background: var(--card); border: 1px solid var(--line); border-radius: 20px; padding: 44px 36px; width: min(400px, calc(100%% - 32px));
    text-align: center; box-shadow: 0 12px 40px rgba(0, 0, 0, .08); animation: sobe .45s ease-out; }
  @keyframes sobe { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
  .cartao-login h1 { margin: 0 0 4px; font: 600 1.6rem/1.25 var(--serif); }
  .cartao-login .sub { color: var(--mut); font-size: .88rem; margin: 0 0 4px; }
  .cartao-login .kanji { font-family: 'Noto Serif JP', var(--serif); color: var(--acc); margin: 0 0 26px; }
  .cartao-login .aviso { color: var(--mut); font-size: .86rem; margin: 0 0 14px; }
  .cartao-login input { width: 100%%; padding: 13px 14px; border: 1.5px solid var(--line); border-radius: 10px; background: var(--bg); color: var(--fg);
    font: inherit; font-size: 1rem; text-align: center; outline: none; }
  .cartao-login input:focus { border-color: var(--acc); box-shadow: 0 0 0 3px var(--acc-soft); }
  .cartao-login input.erro { border-color: #d32f2f; }
  .cartao-login button { width: 100%%; margin-top: 14px; padding: 13px; border: 0; border-radius: 10px; background: var(--acc);
    color: var(--on-acc); font: 600 1rem var(--sans); cursor: pointer; }
  .cartao-login button:hover { filter: brightness(.92); }
  .erro-msg { color: #d32f2f; font-size: .86rem; margin-top: 12px; }
</style>
<script>
  try { var t = localStorage.getItem('nav-theme');
    if (t === 'dark' || (!t && matchMedia('(prefers-color-scheme: dark)').matches)) document.documentElement.classList.add('dark');
  } catch (e) { /* sem storage */ }
</script>
</head>
<body>
<main class="cartao-login">
  <h1>Novo Manual de Difusão</h1>
  <p class="sub">Apostila para ministros · estudo</p>
  <p class="kanji">新・伝道の手引き</p>
  <p class="aviso">Por favor, insira a senha de acesso. É a mesma do Mioshie-Shu.</p>
  <form id="form" autocomplete="off">
    <input type="password" id="senha" placeholder="Senha" aria-label="Senha" autofocus>
    <button type="submit">Entrar</button>
    <p class="erro-msg" id="erro" hidden>Senha incorreta. Tente novamente.</p>
  </form>
</main>
<script>
  // Mesma senha do Mioshie-Shu, do Kōwa-hen e da Zenshu; só o hash SHA-256 fica no código.
  const HASH = '%s';
  const CHAVE = 'mioshie_shu_auth'; // compartilhada com o Mioshie-Shu e o Kōwa-hen (mesmo domínio)

  function destino() {
    const r = new URLSearchParams(location.search).get('redirect') || 'index.html';
    // só páginas deste site (evita redirecionar para outro domínio)
    return /^[\\w.-]+\\.html([?#].*)?$/.test(r) ? r : 'index.html';
  }
  try {
    if (sessionStorage.getItem(CHAVE) === HASH || sessionStorage.getItem('mioshie_auth') === 'true') location.replace(destino());
  } catch (e) { /* sem storage */ }

  async function sha256(texto) {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(texto));
    return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
  }

  const senha = document.getElementById('senha'), erro = document.getElementById('erro');
  document.getElementById('form').addEventListener('submit', async e => {
    e.preventDefault();
    if (await sha256(senha.value) === HASH) {
      try { sessionStorage.setItem(CHAVE, HASH); } catch (err) { /* sem storage */ }
      location.replace(destino());
    } else {
      erro.hidden = false;
      senha.classList.add('erro');
      senha.value = '';
      senha.focus();
    }
  });
  senha.addEventListener('input', () => { erro.hidden = true; senha.classList.remove('erro'); });
</script>
</body>
</html>
''' % (FAVICON, AUTH_HASH)

SAIR_BTN = '<button id="sairBtn" class="tbtn" title="Sair (pede a senha de novo)">Sair</button>'


def main():
    html = open(os.path.join(ROOT, '_nav_proto.html'), encoding='utf-8').read()
    html = html.replace('<title>Apostila — protótipo de navegação</title>',
                        '<title>Novo Manual de Difusão — 新・伝道の手引き</title>', 1)
    assert '</head>' in html
    html = html.replace('</head>', HEAD_EXTRA + '</head>', 1)
    # trava de acesso: a primeira coisa do <head> (antes de fontes e estilos)
    assert html.count('<meta charset="utf-8">') >= 1
    html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8"><script src="auth.js"></script>', 1)
    theme_btn = '<button id="themeBtn" class="tbtn" title="Alternar tema claro/escuro">☾ Escuro</button>'
    assert html.count(theme_btn) == 1
    html = html.replace(theme_btn, theme_btn + '\n  ' + SAIR_BTN, 1)
    book = json.load(open(os.path.join(ROOT, 'shin-dendo-tebiki.json'), encoding='utf-8'))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)
    with open(os.path.join(OUT, 'book.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(book, f, ensure_ascii=False, separators=(',', ':'))
    for name, txt in (('auth.js', AUTH_JS), ('login.html', LOGIN_HTML)):
        with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(txt)
    open(os.path.join(OUT, '.nojekyll'), 'w').close()

    size = sum(os.path.getsize(os.path.join(dp, x)) for dp, _, fs in os.walk(OUT) for x in fs)
    print('site gerado em %s (%.1f MB)' % (os.path.relpath(OUT), size / 1e6))


if __name__ == '__main__':
    main()
