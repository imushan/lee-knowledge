# OKF-KB — Knowledge Base Curation

This project curates an **Open Knowledge Format (OKF)** knowledge base whose
source material is **web articles**. The OKF-KB MCP server provides the tools;
this file is the instruction set the model follows when using them.

## The two-layer model

Everything lives on local files under the configured KB root (`OKF_KB_ROOT`):

```
sources/articles/*.md   raw articles  — the corpus / source of truth ("catalog")
bundles/<name>/*.md     curated OKF concepts — the knowledge layer (output)
```

- **Acquire first, enrich second.** Never treat a live URL as a source. Always
  `acquire_url` so the article is pinned to a local file; later enrichment
  reads that file and stays reproducible.
- The output is plain markdown with YAML frontmatter — diffable, reviewable,
  and consumable by humans and agents directly.

## Tools (provided by the MCP server)

| Tool | Layer | Role |
|------|-------|------|
| `acquire_url` | source | fetch a web article → `sources/articles/<slug>.md` |
| `list_articles` | source | list raw articles in the corpus |
| `read_article` | source | read a raw article (ground truth — like `read_concept_raw`) |
| `list_concepts` | bundle | list curated concepts (also: valid link targets) |
| `read_existing_doc` | bundle | read an existing concept doc (or None → new) |
| `write_concept_doc` | bundle | write/replace a curated concept doc |
| `generate_index` | bundle | regenerate `index.md` in every dir (SPEC §6) |
| `append_log` | bundle | append a dated entry to `log.md` (SPEC §7) |
| `move_concept` | bundle | move a concept + rewrite all affected links |

## Enrichment workflow (per concept)

1. **Acquire** the article(s): `acquire_url(url)` if not already local.
2. **Read the raw material**: `read_article(article_id)`.
3. **Check the bundle**: `list_concepts()` and `read_existing_doc(concept_id)`.
   - `None` → author a **new** doc.
   - non-`None` → **augment** the existing doc (rules below), do not rewrite.
4. **Write**: `write_concept_doc(concept_id, frontmatter, body)` exactly once
   per concept.
5. **Maintain the bundle's self-description**: after writing, call
   `generate_index()` to refresh every `index.md` (progressive disclosure),
   and call `append_log(action, summary)` to record what changed
   (`Creation` for a new doc, `Update` for a material change). These two are
   the bundle's `index.md` (SPEC §6) and `log.md` (SPEC §7) — without them
   the bundle has no directory listing and no history.

## Granularity decision

Articles are prose, not tables — decide mapping before writing:

- **Coarse**: one article → one concept doc (`concepts/<slug>.md`). Start here.
- **Fine**: decompose reusable bits into `references/` — metric definitions,
  glossaries, enum/status catalogs — and cross-link them from primary docs.

## Frontmatter (required + recommended)

Required:

- `type` — concept kind (e.g. `Concept`, `Reference`, `Article`). Non-empty.

Recommended: `title`, `description` (one sentence — used in `index.md`),
`resource` (canonical URI of the underlying asset), `tags` (list),
`timestamp` (omit to auto-refresh).

## Augmentation rules (NON-NEGOTIABLE)

When `read_existing_doc` returns a doc, the write is an **augmentation**, not a
rewrite. `write_concept_doc` is a full replacement, so you must reconstruct the
whole doc:

1. **Frontmatter — send every key.** Copy `type`, `title`, `resource` verbatim
   from the existing doc (the article URL is NOT the concept's `resource` — it
   goes in `# Citations`). Merge `tags` as the **union** of old + new. You may
   refine `description`. Omit `timestamp` to let the tool refresh it (the only
   key you may drop).
2. **Body — keep every existing `#` heading**, same order, same wording. You
   may extend prose under a heading, add bullets to existing lists, add `##`
   sub-sections, add new `#` headings **after** existing ones, and append to
   `# Citations`. You may **not** drop, rename, or reorder existing headings,
   nor replace the body wholesale.
3. If the article is a fundamentally different topic (tutorial, changelog,
   overview), do **not** force it into an existing concept — mint a
   `references/<slug>.md` and cross-link, or skip.

## Cross-linking

- Use **file-relative paths** only: `[users](users.md)`,
  `[metric](../references/metrics/dau.md)`. **Never** start a link with `/`
  (breaks GitHub/plain-file rendering), and don't use bare non-sibling names.
- Link **only** to ids returned by `list_concepts()`. Do not invent targets.
- One link per concept mention per section. Don't over-link. Don't link from
  headers, code blocks, or field-name listings. Don't link a doc to itself.

## Forced extractions

When an article contains any of these, capture them as first-class references
(these bypass the "is it reference-worthy?" question — they always are):

- **Metrics** → one `references/metrics/<slug>.md` per metric, owning the
  concrete SQL expression. Add a `# Metrics` bullet to each contributing
  concept doc linking to it (do not duplicate the SQL).
- **Join paths** → one `references/joins/<a>__<b>.md` per table pair
  (alphabetical, `__`-joined), owning the concrete `ON` clause. Add a `# Joins`
  bullet to each side.
- **Dimensions** → extend the owning concept's `# Schema` inline, or add a
  `# Dimensions` section. Shared enums → `references/<slug>.md`.

## Reorganization

As the KB grows you will deepen nesting or re-categorize. **Pure additions
(new concepts, new subdirectories) are safe** — they break no links; just run
`generate_index` afterward. **Moving an existing concept breaks links in both
directions**, so it must go through the tool, never a hand-edit:

- Use `move_concept(from_id, to_id)` for any rename or relocation. It rewrites
  inbound links (other docs → moved concept) and rebases the moved doc's own
  relative links to its new directory, then refreshes `index.md` and logs.
- Never move a file by hand, and never ask `write_concept_doc` to "rewrite at
  a new path" as a substitute — that strands every inbound link.

## Language

- **All generated documents are written in Chinese (简体中文).** This applies
  to concept docs, reference docs, frontmatter `title` / `description` /
  `tags`, `index.md` listings, and `log.md` entries — body prose, headings,
  and one-line descriptions alike.
- Keep code, identifiers, field names, SQL, file paths, and external URLs in
  their original form (do not translate them). Only the human-readable prose
  is Chinese.

## Integrity

- Cite **only** URLs you actually fetched or that already appear in the doc.
  Never invent URLs, fields, values, or join paths.
- Be concrete: real field names, real enum values, real example queries.
- No preamble, apologies, or reasoning narration in doc bodies — they must be
  valid markdown ready for direct consumption.
- End each enrichment turn with one sentence: how many articles you read, how
  many docs you created/updated, how many references you minted.
