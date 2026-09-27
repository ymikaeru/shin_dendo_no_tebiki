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
5. **★ PUBLICADO no CdF como página não listada (11/06/2026)**: `shin-dendo.html` no repo `caminho_da_felicidade` = porte **só-leitura** do `/nav` (sem os recursos de edição), lê `data/books/shin-dendo-tebiki.json` do próprio repo (NÃO passa pelo Supabase). Sem menu/login/sitemap + `noindex` — acessível só por quem tem o link. Selo "notas em preparação" no topo (tirar no fim da Fase B). Publicar conteúdo novo = `python _sync_apostila.py --publish` (regenera + copia + commita o JSON; falta só `git push`). Mudou o leitor publicado? Editar `shin-dendo.html` direto (standalone, sem ?v= a bumpar). A integração antiga via disciples-reader (branch `feat/apostila-shin-dendo`) virou reserva morta.
6. **🗑 Remover marcador cru `*N`** (modo ✏️ do `/nav`): os `*N` deslocados/não consumidos ao criar a nota aparecem grifados em vermelho no modo edição — clique → confirma → remove do `.md` (`/api/rmstar`, localizado por CONTEXTO com ocorrência única; backup + regen como as outras operações).

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
python servidor.py          # → abre localhost:8000/nav (leitor de estudo, sem login)
```
- Editou um `.md` ou o conversor? **`python _sync_apostila.py`** (regenera + copia; `--check` roda a conservação) → recarrega o `/nav`.
- Conservação dos 8: `python _conserva.py`. Tipagem: `python _triagem.py`.

---

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
