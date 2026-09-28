# Apostila Shin Dendō — Handoff / Como continuar
*(resumo da sessão de 2026-06-03 — leia isto pra retomar de qualquer conversa)*

## 🎯 Objetivo
Transformar a apostila **Shin Dendō** (新・伝道の手引き — manual doutrinário para ministros) num **livro de ESTUDO interativo**, navegável pela hierarquia complexa (até 9 níveis: capítulo › item › parte › número › círculo › romano › letra › subletra › katakana). Cada folha é um *ensinamento* estruturado (fonte, preâmbulo, texto, data, explicação, notas, referências…).

## ⚡ Como retomar numa conversa nova
Diga algo como: **"continuar a apostila Shin Dendō — [Fase B notas / ajuste no leitor /nav / integrar no CdF]"**.
As memórias do projeto trazem o detalhe (`MEMORY.md` → `apostila-reader-caminho-felicidade.md` e `shindendo-md-normalization.md`). Este arquivo é o resumo operacional.

---

## ✅ O que está PRONTO

1. **Conversor MD→JSON** (`_build_book.py`): converte os 8 `.md` → `shin-dendo-tebiki.json` (414 nós, raiz `sections`, nós `id/level/nivel/marcador/title/pagina/children` + `ensinamento` na folha / `explicacao`+`subtitulo` no pai). Corpo = fluxo de blocos tipado pelos marcadores `***[…]***`.
2. **Triagem dos 8 arquivos** (`_conserva.py`): check de conservação linha-a-linha → **0 perdas** (toda linha de corpo cai em algum campo). Corrigiu: intro-de-pai descartada, cabeçalho com corpo grudado (`split_heading`), fonte no mesmo parágrafo, subtítulo emoldurado `――…――`.
3. **Tipagem** (`_triagem.py`, conservador): `ens.referencias` (listas de "Artigos de referência"), `ens.resumo` (marcador `[Resumo]`), `tipo:salmo` (verso), `tipo:jp-pendente` (fragmentos JP não-traduzidos). **0 quote-nodes mistaggeados.**
4. **★ Leitor de ESTUDO `/nav`** (`_nav_proto.html` servido por `servidor.py`) — **é AQUI que se revisa**:
   - árvore colapsável dos 9 níveis, **marcador colorido por nível** + nº de página do livro;
   - **trilha** (breadcrumb) sempre visível; **busca**;
   - painel do ensinamento: fonte 📜 · Preâmbulo/Explicação retráteis · texto · data · resumo · referências · anexo · **salmo em verso** · flag JP;
   - **paginação por número, círculos rolando** (○①②③ juntos na página do número);
   - **chip 📖 de citação inline** (hover) — `(…pág… <Zencho…>)` vira 📖; glosa `(国常立尊)`/`(tane)` fica no texto;
   - multi-parágrafo preservado; notas `[^n]` viram chip 📝 (hover).
   - **o livro é uma TEIA de remissões** ("pág. N deste livro"): prévia do destino ao passar o mouse; ao seguir uma remissão, botão **↩ Voltar para…** (pilha: volta ao ponto exato, com rolagem). Remissão só vira link quando a página está mapeada sem ambiguidade (`pageNode`); senão fica cinza "sem mapa de páginas" — **páginas mapeadas pelos scans (28/09/2026): 762/764 nós** (só as capas c1/c2 sem página) → **232/232 remissões ligadas**. Entradas novas no `_editor_map.json` levam `"fonte":"scan"`. **Mapa ANTIGO corrigido pelo OCR japonês (28/09/2026)**: o mapa antigo (feito pelo PT, regra "próximo marcador") estava quase sempre +1 (até +5) — 194 de 412 nós errados (ex.: c1.i1.4 = 12, real 11 → "Ensinamento 4 da página 11" abria o §3; c1.i1.10–12 = 22, reais 18/19/20). Fonte nova: `Nao Organizados/新・伝道の手引き_OCR.md`, onde `\[Pág. N\]` marca o FIM da pág. N impressa → título logo depois = pág. N+1 (títulos `##` e também `\#\#` escapados). Alinhamento por Item da sequência de marcadores (4, ①, i, A, a…) nossa × OCR; validado contra as entradas `fonte:scan` (315/323 iguais, 8 com ±1 na virada de página) e em 5 pontos no scan (págs. 11, 18/19, 171, 277, 319/320). Entradas conferidas levam `"fonte":"ocr"`; `fonte:scan` não foi tocado. Resultado: páginas em ordem crescente no livro todo, 232/232 remissões ligadas. Scripts de uma vez (não versionados): extrair títulos+página do OCR → alinhar → aplicar com travas (salto >6 recusado, ordem crescente, conflito de título igual). **Estrutura (28/09/2026):** `c1.i3.2.3.i` estava duplicado — o "I." de C1_Item03 (pág. 107, scan) é a 9ª LETRA (…H, I, J, K sob "i."), mas `classify()` lia I/V/X maiúsculo sem Parte como romano; agora romano de uma letra só em minúscula (`_build_book.py` e `tools/_build_tree.py`) e o título foi para `#####`. c2.i3.I.19 "A Sabedoria de Kannon" ESTÁ certo: o scan (pág. 320) mostra "19 観音の智" numerado — o OCR perdeu esse título no corpo e o sumário do OCR tem recuos errados (não confiar no recuo do sumário). Scans: img = pág//2 + 21 (há lacunas: 381–382, 400–401, 406–408, 430–431 não existem).
   - **"Citado por"** no fim de cada ensinamento (quem remete a ele, com tipo: texto/explicação/nota N/anexo) + selo "↩ citado N×" no cabeçalho; índice `citeIndex()` lê fonte/preâmbulo/texto/posfácio/resumo/explicação/referências/anexo/notas.
   - **🕸 Teia** (botão no topo): diagrama de arcos do livro em ordem de leitura — arco acima = remete adiante, abaixo = remete para trás; ponto maior = mais citado; tracinho aceso = já lido (localStorage `nav-seen`); clicar num ponto mostra "remete a"/"citado por" navegáveis + "Abrir no livro" (com ↩ de volta). Vale no /nav e no site estático.
   - **LER ROLANDO (28/09/2026)**: página = um Item inteiro (ou a maior seção ≤ `PAGE_LIM`=100k; 16 páginas no livro, antes 160). Só capítulos e seções enormes (c2.i3, c2.i4, c2.i4.II) viram sumário (2 níveis). Árvore mostra todos os níveis; clicar numa seção ROLA até ela (não troca de página). Ao rolar, `spyTree()` marca a seção na árvore (`.row.here`), abre o caminho e fecha o que ela mesma abriu (`autoPath`), e atualiza a **faixa fixa de posição** (`.posbar`: Item › I › 2 › ② › i › B, clicável). "Nesta página" (coluna direita) saiu — a árvore faz esse papel. "Já lido" agora conta por seção que passou pela tela.
   - **Legibilidade**: seção com texto = ENSINAMENTO (`.sec.teach`: título serifado grande, bloco com linha no fim); seção sem texto = GRUPO (`.sec.grp`: rótulo sans com linha + `.grp-body` com faixa lateral até onde o grupo vai; recuo máx. 2). "Texto omitido. Vide…" → caixa `.ens-omit`; `**subparte**` do .md → `strong.ens-part` (selo ※ solto entra nela); "Citado por" sempre recolhido.
   - **Escala de selos** (`mkSelo`; CSS "ESCALA DE SELOS", vem DEPOIS de "NÍVEIS" — ordem importa): nível mais alto = selo maior e mais cheio. número = quadrado grande cheio (32px) · círculo = círculo médio contornado com o algarismo (27px) · romano = caixa contornada · letra = quadradinho de fundo claro · minúscula/katakana = circulozinho cinza · subparte `**1: …**` = numeral (`.pt-n`). Mesma escala em títulos, árvore e faixa. Títulos de GRUPO e de ENSINAMENTO seguem a mesma escala de tamanho por nível (grupo ≥ o que contém); o grupo se distingue pela linha embaixo + contagem. Recuo +1 por nível até 4.
   - **Visão geral ↔ Ler tudo** (interruptor no cabeçalho da página, lembra em localStorage `nav-view`): visão geral mostra cada ensinamento só com título + 1ª frase (`prevLine`); clicar abre inteiro no lugar (`.sec.teach.open`). **Grupos dobram**: clicar no rótulo do grupo (com contagem "N ensinamentos") recolhe o conteúdo (`.sec.grp.fold`). Navegar até uma seção (árvore/remissão/faixa) desdobra o caminho (`revealSec`). Contexto (preâmbulo/posfácio) sempre aberto e inteiro (`ctxBlock`), em estilo secundário.
   - **DESKTOP (≥1200px)**: (1) **Painéis lado a lado** — remissão (a.xref, inclusive "Citado por") abre o destino num painel à direita (`openPane`/`renderPanes`, pilha `PANES`); link dentro de um painel abre o próximo; os que não cabem viram LOMBADAS verticais (clique = volta até ele); `↗ Ler aqui` leva ao leitor principal; `×`/Esc fecha. O leitor principal não sai do lugar (`keepAnchor/restoreAnchor` compensam o reflow). (2) **Notas na margem** (`layoutMargin`, `.mnotes`): com o leitor ≥1090px, cada nota fica à direita na altura do seu chip; hover nota ↔ chip/trecho; lista "Notas" do rodapé some; ResizeObserver refaz ao abrir/dobrar. Abaixo de 1200px tudo volta ao comportamento anterior (balão + ↩ Voltar).
   - **Índice recolhível (desktop, 28/09/2026)**: botão « ao lado da busca recolhe o índice numa faixa de 46px (» fixa de novo; escolha lembrada em localStorage `nav-side`). Com a faixa, passar o mouse (220ms) ou clicar abre o índice AO LADO dela, por cima do texto, sem mexer na leitura; fecha ao sair com o mouse (exceto digitando a busca), ao clicar fora, com Esc ou ao navegar. Lupa da faixa = abre + foca a busca. Ao abrir um painel de remissão, o índice fixo recolhe sozinho se estiver tirando espaço (largura − 340 − 490 < 1090) e volta quando os painéis fecham — se o leitor não mexeu nele no meio-tempo (`autoRail`). Ganho: em 1366px, com a faixa, as notas vão para a margem (antes só a partir de ~1430px); com painel aberto, o texto mantém os 720px. Celular (≤820px) inalterado (gaveta ☰).
   - **Correções (28/09/2026)**: (1) notas da margem PISCAVAM — `_layoutMargin` re-observava o `.page-body` a cada refazer e o `observe()` sempre dispara uma leitura inicial → refazia em laço (~11×/s). Agora observa uma vez por página e só refaz se o tamanho mudar (`_mnObs`/`_mnSize`). (2) algarismo SUBIDO na bolinha da nota (texto e margem): `text-box: trim-both cap alphabetic` (em `@supports`) apara a caixa à altura do algarismo; bolinha do texto com `padding:4px 5px` (16px), número da margem num `<span>` interno (o ajuste não pega direto na caixa flex) e 11px em vez de 10,5px → desvio 0 medido nas 34 notas de c1.i1. (3) legibilidade do aparato: token `--src` (claro #6b6153, 5,7:1; escuro #aba294) só para o que se LÊ — FONTE 13,5px, data 14,5px, fonte do anexo 13px; `--mut` (rótulos da interface) ficou como estava. Notas da margem 14px/1.6 (largura 280 mantida).
   - **"Texto omitido" ligado ao original** (`omitTarget`): acha o ensinamento original = com texto, a ±2 páginas da remissão, com fonte de números iguais (score ≥0.6, folga ≥0.15 sobre o 2º). 51 dos 72 omitidos ligam; os outros ficam só com o link (sem fonte comparável ou apontam p/ anexo). Botão "▸ mostrar o texto aqui" abre o original dentro da caixa; na visão geral a prévia mostra "↪ 1ª frase do original". Correção de .md (28/09): C2_Item04 D.a/D.b — o "Texto omitido… (pág. 331)" estava na linha do b; pelo scan (pág. 516) é do a.
   - **Escrito de origem (acervo Mioshie Zenshu) — REMOVIDO a pedido do usuário (28/09/2026).** Ligava a fonte ao escrito completo no acervo pelo texto japonês (OCR do livro → sondas de kanji). A identificação era boa, mas o painel confundia (tradução diferente da do livro; datas de palestra × publicação; fontes secundárias como 参考文献/再録 competindo com o original). Código/dados recuperáveis no histórico git (commits "Fonte → escrito completo…" e seguintes; script tools/build_fontes.py). Se voltar: escolher o escrito pela DATA do livro primeiro (236/242 batiam), e só depois por tamanho.
   - **Conversor — fonte gulosa corrigida (28/09/2026)**: 1ª linha `(fonte) Texto… (data)` era tomada INTEIRA como fonte (regex `^\((.*)\)$` gulosa) → texto sumia/virava fonte cinza. Agora `lead_groups()` casa parênteses balanceados: 1º grupo citação = fonte; grupo JP antes dele volta ao título; resto = texto; `[Zencho…] Trecho` logo após entra na fonte. 82 nós corrigidos. `_conserva.py` ganhou `split_ok()` (linha dividida em título/fonte/texto conta se cada pedaço existe) → 0 perdas.
5. **★ PUBLICADO no CdF como página não listada (11/06/2026)**: `shin-dendo.html` no repo `caminho_da_felicidade` = porte **só-leitura** do `/nav` (sem os recursos de edição), lê `data/books/shin-dendo-tebiki.json` do próprio repo (NÃO passa pelo Supabase). Sem menu/login/sitemap + `noindex` — acessível só por quem tem o link. Selo "notas em preparação" no topo (tirar no fim da Fase B). Publicar conteúdo novo = `python _sync_apostila.py --publish` (regenera + copia + commita o JSON; falta só `git push`). Mudou o leitor publicado? Editar `shin-dendo.html` direto (standalone, sem ?v= a bumpar). A integração antiga via disciples-reader (branch `feat/apostila-shin-dendo`) virou reserva morta.
6. **🗑 Marcador cru `*N` espúrio**: remove-se pela fila de revisão de notas (📝 Notas pendentes → "🗑 Marcador espúrio", `drop_marker` em `_notes_review.py`). (O `/api/rmstar` feito localmente em jun/2026 foi aposentado na integração com a sessão da nuvem — fazia o mesmo.)

## 📂 Arquivos-chave (em `D:\Mioshie_Sites\ShinDendoMD`)
| arquivo | o que faz |
|---|---|
| `_build_book.py` | conversor MD→JSON (reaproveita `classify()` do `_build_tree.py`) |
| `_sync_apostila.py` | **regenera + copia** o JSON pros destinos (data/books, .local-edits) |
| `_conserva.py` | check de conservação (0 perdas) |
| `_triagem.py` | classifica tipagem dos ensinamentos |
| `_nav_proto.html` + `servidor.py` | **leitor de estudo** (`localhost:8000/nav`, sem login) |
| `_notes_match.py` | Fase B: casamento de notas por **âncora** (o caminho certo) |
| `_notes_extract.py`, `_notes_pilot.py` | Fase B: diagnósticos de cobertura de notas |
| `shin-dendo-tebiki.json` | o livro gerado (414 nós) |
| `ShinDendo_C{1,2}_Item{1..4}.md` | fonte normalizada (8 arquivos) |
| `Nao Organizados/` | fontes p/ notas: `_ForSite.md` (PT), `新・伝道の手引き_OCR.md` (JP), `_Traduzido.md` |
| `CZUR_Scan/` | imagens dos scans (japonês original — p/ notas órfãs) |

## ▶️ Como rodar / revisar
```
cd D:\Mioshie_Sites\ShinDendoMD
python servidor.py          # → abre localhost:8000/nav (leitor COM edição e notas); localhost:8000/ = editor do texto
```
- Editou um `.md` ou o conversor? **`python _sync_apostila.py`** (regenera + copia; `--check` roda a conservação) → recarrega o `/nav`.
- Conservação dos 8: `python _conserva.py`. Tipagem: `python _triagem.py`.

---

## 🆕 Fila de notas (a IA propõe, você aprova)
- `python tools/notes_inventory.py` → varre os `.md` e grava `_notes_proposals.json`: **uma vaga por marcador cru** (`\*N`/`*N` **e** dígito colado `boca2.`). Hoje: **656 vagas** (todas `sem-fonte`). Rodar de novo é seguro (preserva o trabalho feito).
- No `/nav`, botão **📝 Notas pendentes** → painel da fila: filtra por arquivo/status, acende o `*N` e o trecho proposto no texto, e oferece **Aprovar** (grava `==trecho==[^id]` + def no `## Notas`, com trava de prosa + backup), **Rejeitar**, **Marcador espúrio** (remove só o `*N`), **Rascunho**. Atalhos: `A` `R` `D` `M` (usar seleção como trecho) `J`/`K`.
- Marcadores pendentes aparecem no leitor como chip laranja tracejado (`*N`).
- Próximo passo: os extratores das fontes (`Nao Organizados/*.md`, já liberados no `.gitignore`) preenchem `texto`/`trecho`/`origem`/`confianca` das vagas → status `pendente`.

## 🆕 Leitor / site público
- **Mesmo leitor** (`_nav_proto.html`) serve o `/nav` local e o **site público**: `python tools/build_site.py` gera `site/` (somente leitura: sem ✏️/📝, marcadores pendentes ocultos, lê `book.json`). Testar: `python -m http.server -d site 8080`.
- **GitHub Pages**: `.github/workflows/pages.yml` publica a cada push na `main`. Ativar uma vez em *Settings → Pages → Source: GitHub Actions*. (O site vai com `noindex` — tirar do `tools/build_site.py` se quiser que apareça no Google.)
- Novidades do leitor (valem nos dois): **busca no texto completo** (sem acento; frase exata primeiro; destaca no ensinamento), **link direto** por ensinamento (`#c1.i1.2`, voltar/avançar funcionam, botão 🔗), **"Livro pág. N" / "pág. N deste livro" clicáveis**, página inicial com o sumário, **layout de celular** (índice em gaveta ☰, nota 📝 abre com toque), imagens embutidas renderizadas.

## 🆕 Layout "livro de estudo" + páginas de leitura
- Visual: papel claro por padrão (escuro no botão ☾; 1ª visita segue o sistema), texto serifado (Literata) em coluna centralizada, destaque bronze, sem emojis na leitura; sumário com cara de livro na página inicial.
- **Os 9 níveis**: a lateral só vai até a **página de leitura** (nó cujo conteúdo inteiro cabe em ~30 mil caracteres — `PAGE_LIM` no `_nav_proto.html`); os níveis abaixo (①, i, A, a…) viram **seções da página**, com fio lateral de profundidade e o índice **"Nesta página"** (à direita; recolhível no topo em telas menores) que acompanha a rolagem. 764 nós → ~165 páginas. Links `#id` de seção profunda abrem a página e rolam até ela.
- Contêineres (capítulo/item/parte/número grande) mostram a introdução + **sumário** das páginas abaixo.
- **Anatomia fixa do ensinamento**: Fonte · Contexto (preâmbulo, recolhido) · **texto** · data · resumo/referências · 解説 Explicação · Anexos · **Notas** (lista de rodapé, além do balão).

## 🆕 Estrutura corrigida (C2 Item 3/4)
- Do meio do `C2_Item04` (e parte do `C2_Item03`) os títulos estavam **recuados com 2 espaços** → o conversor não os via e ~1000 linhas viravam **uma página só** (`c2.i4.2`, 211 mil caracteres). Recuo removido + títulos vazios (`###`) apagados + 3 marcadores de título corrigidos (`## 1. Criação` → `# I Criação`, `#### .E.` → `##### E.`, `*F.` → `*f.`). **Nenhuma palavra mudou** (verificado com `_notes_guard`). Livro: **414 → 764 nós**, conservação 0 perdas.
- `[image1]` (trecho JP escaneado, base64) saía como texto no fim de "Procura de Flores" → agora vai para `book.imagens` e aparece em "O Despertar (Satori)", onde é citado.
- Pendências vistas: `# Parei aqui~!` no `C2_Item04` (linha ~1130) — marca de onde a normalização manual parou; **páginas** dos ~350 títulos novos ainda vazias (rodar `python tools/_build_pagemap.py --write` quando `Nao Organizados/` estiver no repo); `c1.i3.2.3.i` duplicado (`#### I.` entre `i.` e `ii.` no C1_Item03 — conferir no livro).

## ⏳ O que FALTA — **Fase B: NOTAS** (projeto focado, cuidadoso)
Hoje a maioria dos ensinamentos mostra marcadores crus `*1 *2`; só o piloto C1_Item01 §2 tem as 3 notas reais (`[^id]` → chip 📝). Falta extrair/traduzir/injetar o resto.

**Tradução:** usar `D:\Mioshie_Sites\guia_johrei\prompts\translation_prompt.md` (v5.6). ✅ **VALIDADO**: traduzi o 註 JP do §2 e bateu **idêntico** ao humano. Regra-ouro: fontes/obras em Romaji (垂→Sui, 宗→Shu, 教→Kyo, 頁→pág, 行→l., 下段→col. inf., 本書→Livro, 参照→Ver).

**Fontes das notas (3, PARCIAIS e complementares):**
- (a) PT `_ForSite.md` — blocos `*\[Notas\] âncora N texto*` (já traduzidos; ~24% dos numerados).
- (b) JP OCR `新・伝道の手引き_OCR.md` — blocos `\[Notas\] 註 âncora*N texto` (mais cobertura; headings PLANOS e em japonês `## 二項`, `## ①`).
- (c) **Scans CZUR** — pros órfãos que não estão em nenhuma fonte digital (ex.: §1, §7). **Eu leio o JPEG full-res direto** (melhor que print do chat); usuário valida.

**⚠️ 3 BLOCKERS — por isso é colocação-por-ÂNCORA + validação humana, NÃO auto-por-`*N`:**
1. **Atribuir nota→ensinamento por hierarquia FALHA** (testado: nota do §3 caiu no §1; anexos têm `### 1/2` próprios + OCR-JP é plano). → casar pela **âncora** (a frase-gancho aparece no texto do ensinamento). `_notes_match.py` faz isso (§2 = 100%).
2. **Parser de bloco é multi-formato**: "(Livro pág N)." vs "página X deste livro" vs `**[Notas]** *Nota N*:`. O parser atual só pega o 1º formato (§3/§10 escaparam). Precisa generalizar.
3. **Marcadores `*N` no texto digital estão DESLOCADOS/espúrios**: ex. §1 — o MD tem `*1` em "consultam **a Deus**" (preâmbulo), mas o 註 original diz que a nota 1 é sobre "**○○○○○ nome do Deus**" (texto). Logo, **colocar a nota pela âncora, não pelo `*N`**; casos ambíguos (preâmbulo tem nota ou não?) exigem o usuário com o livro.

**Plano da rodada dedicada (Fase B):**
1. Generalizar o parser de blocos `[Notas]` (multi-formato) → trios `(âncora, N, texto)`.
2. Casar nota↔ensinamento por âncora (PT direto; JP traduz pelo `translation_prompt`).
3. **Colocar** a nota na posição da âncora no texto (não no `*N` deslocado) → converter pra `[^id]` + def no `## Notas` do `.md`.
4. Regenerar (`_sync_apostila.py`) → **usuário valida item a item no `/nav`** (já vira chip 📝).
5. Órfãos de scan: eu leio o CZUR + usuário valida a tradução (registro doutrinário é a expertise dele).

## 🔑 Decisões & armadilhas a lembrar
- **Fonte da verdade = JSON**; editar por ferramenta, não à mão.
- **Leitor = `/nav` standalone** (não o disciples-reader do CdF) — escolha do usuário: foco em estudo/navegação, sem fricção de login/gate/cache. CdF é reserva.
- **Nada no Supabase ainda** (decisão: corrigir conteúdo + revisar local antes de publicar). Publicar = subir index 3-livros + deploy web do reader.js/css + merge do branch, **juntos** (senão o site ao vivo mostra a apostila vazia).
- **Tipagem conservadora**: falso-positivo é pior que perda; nota/tag no lugar errado em texto doutrinário é inaceitável → sempre validar.
- Conservação=0 significa **nada perdido**, NÃO que tudo está no campo/posição certa.
- Backups dos `.md`: `_backup_*` (faseA/A3/original/editor).

---
*Fim do handoff. Estado completo nas memórias do projeto.*

### Piloto Fase B — C1_Item02 (28/09/2026)
- Fila ganhou a forma **solto** (`\*` sem número, n=0; `BARE_MK` em `_notes_review.py`): +180 vagas no livro (835 no total).
- **56 propostas** gravadas como `pendente` (origem `_ForSite (PT da casa)`, texto SEM repetir a âncora, trecho = frase que a nota explica). Ensaio em memória antes: 56/56 aplicáveis, prosa intacta (só saem os dígitos de marcador colado).
- Confiança <90% (revisar com o livro): p0030 (marcador deslocado → "é óbvia"), p0038/p0039 (notas 3 e 4 quase iguais; ⑭ em vez do ⑪ do OCR), p0041 (nota 5 → "não a informou"), p0664 (pág. 41, não 411), p0669 (Cap. 2, não Cap. 1), p0046 (Item 3), p0013 (grifo parcial).
- 3 notas do livro SEM marcador no .md (não entram na fila; adicionar com ➕ no /nav): "Plano Divino (Keirin)" (intro do Item 2), título "1. A aproximação do Paraíso Terrestre…", "abertura da Porta de Rocha" (L156).
- Receita p/ os próximos itens: ler blocos `[Notas]` do _ForSite + 註 do OCR JP do item → mapear âncora→vaga → ensaio (place em memória + trava de prosa) → gravar pendentes → usuário aprova no painel.
- **Rodar localmente:** `python servidor.py` → abre `http://localhost:8000/nav` (leitor com edição e fila de notas). `http://localhost:8000/` é o editor do texto (scan × .md). A versão SEM edição é o site estático (`site/`, gerado por `tools/build_site.py`) — é a que vai para o GitHub Pages. No Windows, porta 8000 ocupada = aviso claro (não sobe 2º servidor).
