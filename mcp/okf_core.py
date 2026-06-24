"""Pure OKF-KB core logic.

No MCP dependency here — this module is plain stdlib + PyYAML so it can be
unit-tested and reused outside the MCP server. The two-layer model:

    sources/articles/*.md   -> raw articles (the "catalog" / source of truth)
    bundles/<name>/*.md     -> curated OKF concepts (the knowledge layer)

Configuration (read from environment, with sensible defaults):

    OKF_KB_ROOT    root of the working knowledge base
    OKF_BUNDLE     name of the active bundle dir under bundles/
"""
from __future__ import annotations

import os
import posixpath
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# --- configuration ---------------------------------------------------------

KB_ROOT = Path(
    os.environ.get("OKF_KB_ROOT", Path(__file__).resolve().parent / "kb")
).resolve()
BUNDLE_NAME = os.environ.get("OKF_BUNDLE", "default")
SOURCES_DIR = KB_ROOT / "sources" / "articles"
BUNDLE_DIR = KB_ROOT / "bundles" / BUNDLE_NAME

# Filenames that are NOT concept documents (see OKF SPEC §3.1).
RESERVED = {"index.md", "log.md"}


# --- document (de)serialization --------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?(.*)\Z", re.DOTALL)


def split_doc(text: str) -> tuple[dict[str, Any], str]:
    """Split a markdown doc into (frontmatter dict, body).

    Returns ({}, text) if there is no frontmatter block.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    if not isinstance(fm, dict):
        raise ValueError("frontmatter is not a YAML mapping")
    return fm, m.group(2)


def join_doc(frontmatter: dict[str, Any], body: str) -> str:
    """Serialize a (frontmatter, body) pair back to a single markdown doc."""
    fm_yaml = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm_yaml}\n---\n\n{body.strip()}\n"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slugify(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text.strip("_") or "article"


def _walk_concepts(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if p.name not in RESERVED)


def _rel_id(path: Path, root: Path) -> str:
    return str(path.relative_to(root).with_suffix("")).replace(os.sep, "/")


# --- concept-id normalization + frontmatter invariants ---------------------

# frontmatter keys the tool enforces at write time. SPEC §4.1 makes only
# `type` strictly required, but the original reference agent enforces these
# four (title/description feed index.md and search; timestamp auto-fills).
REQUIRED_FRONTMATTER_KEYS = ("type", "title", "description")

# canonical key order for stable, reviewable diffs (mirrors the original
# agent's _PREFERRED_KEY_ORDER).
_PREFERRED_KEY_ORDER = ("type", "resource", "title", "description", "tags", "timestamp")


def _normalize_concept_id(concept_id: str) -> str:
    """Normalize a concept id to a clean slash path.

    Strips leading/trailing slashes, backslashes → '/', drops empty/`.`/`..`
    segments so the id can never escape the bundle root or produce a weird
    path like '/concepts/x'."""
    cid = (concept_id or "").strip().replace("\\", "/")
    parts = [p for p in cid.split("/") if p and p not in (".", "..")]
    return "/".join(parts)


def _reorder_frontmatter(fm: dict[str, Any]) -> dict[str, Any]:
    """Return fm with canonical key ordering; unknown keys appended after."""
    ordered: dict[str, Any] = {}
    for key in _PREFERRED_KEY_ORDER:
        if key in fm:
            ordered[key] = fm[key]
    for key, value in fm.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def _top_level_headings(body: str) -> list[str]:
    """Top-level '# heading' texts in order, skipping fenced code blocks."""
    out: list[str] = []
    in_fence = False
    fence = None
    for line in (body or "").splitlines():
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            tok = s[:3]
            if not in_fence:
                in_fence, fence = True, tok
            elif tok == fence:
                in_fence, fence = False, None
            continue
        if in_fence:
            continue
        if s.startswith("# ") and not s.startswith("## "):
            out.append(s[2:].strip())
    return out


# --- source layer: raw articles --------------------------------------------

def list_articles() -> list[dict[str, Any]]:
    """List every raw article in sources/articles/.

    Each entry: {id, title, resource, timestamp}. id is the slug (filename
    stem) used by read_article().
    """
    if not SOURCES_DIR.exists():
        return []
    out = []
    for p in sorted(SOURCES_DIR.glob("*.md")):
        fm, _ = split_doc(p.read_text(encoding="utf-8"))
        out.append(
            {
                "id": p.stem,
                "title": fm.get("title", p.stem),
                "resource": fm.get("resource"),
                "timestamp": fm.get("timestamp"),
            }
        )
    return out


def read_article(article_id: str) -> dict[str, Any]:
    """Read a raw source article. Raises FileNotFoundError if unknown."""
    p = SOURCES_DIR / f"{article_id}.md"
    if not p.exists():
        raise FileNotFoundError(f"Unknown article: {article_id}")
    fm, body = split_doc(p.read_text(encoding="utf-8"))
    return {"id": article_id, "frontmatter": fm, "body": body}


def _fetch_html(url: str) -> str:
    from urllib.request import Request, urlopen

    req = Request(url, headers={"User-Agent": "okf-kb/0.1 (+local knowledge base)"})
    with urlopen(req, timeout=30) as r:  # noqa: S310 - user-supplied URL
        return r.read().decode("utf-8", errors="replace")


def acquire_url(url: str, slug: str | None = None) -> dict[str, Any]:
    """Fetch a web article, convert it to markdown, and save it under
    sources/articles/. This is the ACQUIRE step: it pins the article to a
    local file so later enrichment is reproducible regardless of future
    edits or link rot on the origin site.
    """
    from markdownify import markdownify as html_to_md

    html = _fetch_html(url)
    md = html_to_md(html)
    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_m.group(1).strip() if title_m else (slug or url)
    if not slug:
        slug = _slugify(title)

    fm = {
        "type": "Article",
        "title": title,
        "resource": url,
        "timestamp": _now_iso(),
    }
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    p = SOURCES_DIR / f"{slug}.md"
    p.write_text(join_doc(fm, md), encoding="utf-8")
    return {
        "id": slug,
        "path": str(p.relative_to(KB_ROOT)),
        "title": title,
        "bytes": p.stat().st_size,
    }


# --- bundle layer: curated OKF concepts ------------------------------------

def list_concepts() -> list[dict[str, Any]]:
    """List every curated concept in the active bundle.

    Each entry: {id, type, title, description, resource}. id is the slash-joined
    path (e.g. 'concepts/ga4_events') used by read_existing_doc() /
    write_concept_doc()."""
    if not BUNDLE_DIR.exists():
        return []
    out = []
    for p in _walk_concepts(BUNDLE_DIR):
        fm, _ = split_doc(p.read_text(encoding="utf-8"))
        out.append(
            {
                "id": _rel_id(p, BUNDLE_DIR),
                "type": fm.get("type"),
                "title": fm.get("title", p.stem),
                "description": fm.get("description"),
                "resource": fm.get("resource"),
            }
        )
    return out


def read_existing_doc(concept_id: str) -> dict[str, Any] | None:
    """Read an existing curated concept doc, or None if it does not exist.

    None signals 'this concept is new' — the caller should author from
    scratch rather than augment.
    """
    concept_id = _normalize_concept_id(concept_id)
    p = BUNDLE_DIR / f"{concept_id}.md"
    if not p.exists():
        return None
    fm, body = split_doc(p.read_text(encoding="utf-8"))
    return {"id": concept_id, "frontmatter": fm, "body": body}


def write_concept_doc(
    concept_id: str, frontmatter: dict[str, Any], body: str
) -> dict[str, Any]:
    """Write (full-replacement) a curated concept doc.

    Enforces the OKF invariants in code, not just in the prompt:
      - frontmatter is a dict,
      - it carries non-empty `type`, `title`, `description` (timestamp
        auto-refreshes to now if omitted),
      - keys are written in canonical order,
      - AUGMENTATION GUARD: when overwriting an existing doc, refuse to drop
        any existing top-level '#' heading (the model must augment, not
        rewrite). Mirrors the original agent's Schema/Citations guard.

    On a validation/augmentation failure returns an {error, concept_id, ...}
    dict instead of raising, so the model can read the reason and re-call.
    On success returns {id, path, created, bytes}.
    """
    concept_id = _normalize_concept_id(concept_id)
    if not isinstance(frontmatter, dict):
        return {"error": "frontmatter must be a dict", "concept_id": concept_id}

    missing = [k for k in REQUIRED_FRONTMATTER_KEYS if not frontmatter.get(k)]
    if missing:
        return {
            "error": (
                f"frontmatter missing required key(s): {', '.join(missing)}. "
                f"Required: {', '.join(REQUIRED_FRONTMATTER_KEYS)} (timestamp "
                f"auto-fills). Re-call write_concept_doc with them set."
            ),
            "concept_id": concept_id,
            "missing": missing,
        }

    fm = dict(frontmatter)
    if not fm.get("timestamp"):
        fm["timestamp"] = _now_iso()
    fm = _reorder_frontmatter(fm)

    p = BUNDLE_DIR / f"{concept_id}.md"

    # Augmentation guard: refuse to overwrite in a way that drops existing
    # top-level headings. The model must preserve every existing '#' heading
    # (same wording/order) and only extend or add.
    if p.exists():
        try:
            _, old_body = split_doc(p.read_text(encoding="utf-8"))
        except Exception:
            old_body = ""
        old_headings = _top_level_headings(old_body)
        new_headings = set(_top_level_headings(body or ""))
        dropped = [h for h in old_headings if h not in new_headings]
        if dropped:
            shown = ", ".join(f"`# {h}`" for h in dropped[:8])
            trunc = " (and more)" if len(dropped) > 8 else ""
            return {
                "error": (
                    f"Refusing to write: this overwrites an existing doc and "
                    f"would drop {len(dropped)} existing top-level heading(s): "
                    f"{shown}{trunc}. Augment, do not rewrite — preserve every "
                    f"existing '#' heading (same wording, same order) and only "
                    f"extend under them or add new headings after. Re-call "
                    f"read_existing_doc to see the current doc, then re-call "
                    f"write_concept_doc with all headings preserved."
                ),
                "concept_id": concept_id,
                "dropped_headings": dropped,
            }

    p.parent.mkdir(parents=True, exist_ok=True)
    existed = p.exists()
    p.write_text(join_doc(fm, body), encoding="utf-8")
    return {
        "id": concept_id,
        "path": str(p.relative_to(KB_ROOT)),
        "created": not existed,
        "bytes": p.stat().st_size,
    }


# --- index.md + log.md maintenance -----------------------------------------
#
# Both files are OKF spec features (SPEC §6 index.md, §7 log.md) but the
# original reference agent does NOT expose them as agent tools: index.md is
# regenerated by the runner after enrichment (bundle/index.py:regenerate_indexes)
# and log.md is not automated at all. This MCP server has no runner layer, so
# we surface them as deterministic tools the model calls explicitly.
#
# generate_index mirrors regenerate_indexes (grouped by type, relative links,
# descriptions from frontmatter) but is pure-stdlib — it does not call an LLM
# to synthesize directory descriptions the way the original does.


def _index_dirs(bundle_root: Path) -> list[Path]:
    """Every directory at or under bundle_root that contains a concept doc
    (ancestors included, so each level gets its own progressive-disclosure
    listing)."""
    dirs: set[Path] = set()
    for md in bundle_root.rglob("*.md"):
        if md.name in RESERVED:
            continue
        cur = md.parent
        while True:
            dirs.add(cur)
            if cur == bundle_root:
                break
            cur = cur.parent
    return sorted(dirs, key=lambda p: (-len(p.relative_to(bundle_root).parts), str(p)))


def _build_index_text(entries: list[tuple[str, str, str, str]]) -> str:
    """entries: (type, title, relative_link, description). Group by type,
    sort, render as SPEC §6 listing. Pure deterministic — no LLM."""
    grouped: dict[str, list[tuple[str, str, str]]] = {}
    for typ, title, link, desc in entries:
        grouped.setdefault(typ or "Other", []).append((title, link, desc))
    sections = []
    for typ in sorted(grouped):
        lines = [f"# {typ}", ""]
        for title, link, desc in sorted(grouped[typ], key=lambda e: e[0].lower()):
            suffix = f" - {desc}" if desc else ""
            lines.append(f"* [{title}]({link}){suffix}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections) + "\n"


def generate_index() -> dict[str, Any]:
    """Regenerate index.md in every directory of the active bundle.

    Walks the bundle, and for each directory writes an index.md listing its
    concept docs (grouped by `type`, with title + description from frontmatter)
    and its subdirectories. Idempotent — safe to call after every
    write_concept_doc. Mirrors the original agent's regenerate_indexes but is
    pure-stdlib (no LLM directory-description synthesis).

    Returns {written: [relative paths of index.md files]}."""
    if not BUNDLE_DIR.exists():
        return {"written": []}

    written: list[str] = []
    for directory in _index_dirs(BUNDLE_DIR):
        entries: list[tuple[str, str, str, str]] = []
        for child in sorted(directory.iterdir()):
            if child.name == "index.md":
                continue
            if child.is_file() and child.suffix == ".md":
                if child.name in RESERVED:  # log.md etc. are not concepts
                    continue
                fm, _ = split_doc(child.read_text(encoding="utf-8"))
                entries.append(
                    (
                        str(fm.get("type") or ""),
                        str(fm.get("title") or child.stem),
                        child.name,
                        str(fm.get("description") or ""),
                    )
                )
            elif child.is_dir():
                entries.append(("Subdirectories", child.name, f"{child.name}/index.md", ""))
        if not entries:
            continue
        idx = directory / "index.md"
        idx.write_text(_build_index_text(entries), encoding="utf-8")
        written.append(str(idx.relative_to(KB_ROOT)))
    return {"written": written}


def append_log(action: str, summary: str) -> dict[str, Any]:
    """Append a dated entry to the bundle's log.md (OKF SPEC §7).

    Enforces the §7 format: ISO 8601 `YYYY-MM-DD` date headings, newest date
    first, a flat list under each date. Today's date (UTC) is used; if a
    section for today already exists the entry is added to it, otherwise a new
    section is inserted at the top. The leading bold word is the `action`
    (e.g. Creation, Update, Deprecation).

    Returns {path, date, entry}."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    action = (action or "Update").strip() or "Update"
    summary = (summary or "").strip()
    if not summary:
        raise ValueError("summary must not be empty")
    entry_line = f"* **{action}**: {summary}"

    log_path = BUNDLE_DIR / "log.md"
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    title = "# Bundle Update Log\n\n"
    sections: list[tuple[str, list[str]]] = []  # (date, body_lines)
    if log_path.exists():
        text = log_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        # Header = everything before the first '## ' date heading.
        first_section = next(
            (i for i, ln in enumerate(lines) if ln.startswith("## ")), len(lines)
        )
        title_block = "\n".join(lines[:first_section]).rstrip()
        if title_block:
            title = title_block + "\n\n"
        i = first_section
        while i < len(lines):
            ln = lines[i]
            if ln.startswith("## "):
                date = ln[3:].strip()
                body: list[str] = []
                i += 1
                while i < len(lines) and not lines[i].startswith("## "):
                    body.append(lines[i])
                    i += 1
                sections.append((date, [b for b in body if b.strip()]))
            else:
                i += 1

    # Insert/prepend today's entry, newest-first overall.
    for idx, (date, body) in enumerate(sections):
        if date == today:
            body.insert(0, entry_line)
            sections[idx] = (date, body)
            break
    else:
        sections.insert(0, (today, [entry_line]))

    out = [title.rstrip() + "\n"]
    for date, body in sections:
        out.append(f"\n## {date}\n")
        out.append("\n".join(body).rstrip() + "\n")
    log_path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")

    return {
        "path": str(log_path.relative_to(KB_ROOT)),
        "date": today,
        "entry": entry_line,
    }


# --- reorganization: move a concept + rewrite links -----------------------
#
# Moving a doc breaks links in two directions:
#   - INBOUND  links in other docs that pointed at the old path,
#   - OUTBOUND relative links inside the moved doc itself (their `../` depth
#     is now wrong because the doc sits in a different directory).
#
# move_concept rewrites both deterministically, then refreshes index.md and
# appends a log entry. This is the one operation where link integrity MUST be
# guaranteed by a tool, not by the model — relative-path arithmetic is exactly
# the kind of thing an LLM gets wrong silently.

_EXTERNAL = ("http://", "https://", "mailto:", "ftp://", "data:")
_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*?)\)")


def _parse_link_field(field: str) -> tuple[str, str]:
    """Split the inside of a markdown link's (...) into (url, title_tail).

    title_tail is the raw ` "title"` suffix (kept verbatim) or ''."""
    field = field.strip()
    if '"' in field:
        i = field.index('"')
        return field[:i].strip(), field[i:].rstrip()
    return field, ""


def _resolve_target(url: str, resolve_dir: str) -> tuple[str | None, str, str]:
    """Resolve a link url to a normalized bundle-relative path.

    Returns (target_file_rel, anchor, kind):
      - target_file_rel: posix path relative to bundle root, .md ensured; or
        None for external/anchor-only links.
      - anchor: '#section' or ''.
      - kind: 'abs' (bundle-absolute /x), 'rel' (relative), 'external', 'anchor'.

    `resolve_dir` is the directory (bundle-relative, posix) the link is
    resolved against — for the moved doc this is its OLD directory so its
    relative links still resolve correctly."""
    path_part = url
    anchor = ""
    if "#" in path_part:
        path_part, anchor = path_part.split("#", 1)
        anchor = "#" + anchor
    path_part = path_part.split("?", 1)[0]
    if not path_part:
        return None, anchor, "anchor"
    if path_part.startswith(_EXTERNAL):
        return None, anchor, "external"
    if path_part.startswith("/"):
        norm = posixpath.normpath(path_part[1:])
        kind = "abs"
    else:
        norm = posixpath.normpath(posixpath.join(resolve_dir, path_part))
        kind = "rel"
    if not norm.endswith(".md"):
        norm = norm + ".md"
    return norm, anchor, kind


def _rewrite_doc_links(
    doc_path: Path,
    *,
    from_file_rel: str,
    to_file_rel: str,
    moved_old_dir: str | None,
    bundle_root: Path,
) -> int:
    """Rewrite links in one doc. Returns the number of links changed.

    - Any link resolving to from_file_rel → repointed at to_file_rel, as a
      path relative to THIS doc's directory (inbound fix).
    - If this is the moved doc (moved_old_dir is not None), every RELATIVE
      link is rebased from its old directory to its new one (outbound fix)."""
    text = doc_path.read_text(encoding="utf-8")
    doc_dir_rel = posixpath.dirname(
        str(doc_path.relative_to(bundle_root)).replace(os.sep, "/")
    )
    resolve_dir = moved_old_dir if moved_old_dir is not None else doc_dir_rel
    changes = 0

    def repl(m: re.Match) -> str:
        nonlocal changes
        label, field = m.group(1), m.group(2)
        url, title_tail = _parse_link_field(field)
        target, anchor, kind = _resolve_target(url, resolve_dir)
        new_url: str | None = None
        if target == from_file_rel:
            new_url = posixpath.relpath(to_file_rel, doc_dir_rel)
        elif moved_old_dir is not None and kind == "rel" and target is not None:
            new_url = posixpath.relpath(target, doc_dir_rel)
        if new_url is None:
            return m.group(0)
        changes += 1
        return f"[{label}]({new_url}{anchor}{(' ' + title_tail) if title_tail else ''})"

    new_text = _LINK_RE.sub(repl, text)
    if new_text != text:
        doc_path.write_text(new_text, encoding="utf-8")
    return changes


def _prune_empty_dirs(bundle_root: Path, start: Path) -> None:
    """Remove `start` and its now-empty ancestors, stopping at bundle_root."""
    try:
        start.relative_to(bundle_root)
    except ValueError:
        return
    cur = start
    while cur != bundle_root:
        if cur.exists() and not any(cur.iterdir()):
            cur.rmdir()
            cur = cur.parent
        else:
            break


def move_concept(from_id: str, to_id: str) -> dict[str, Any]:
    """Move a concept doc to a new path and rewrite all affected links.

    Handles both directions of link breakage:
      - INBOUND: links in other docs that pointed at the old path are repointed
        at the new path (as a correct relative path from each doc).
      - OUTBOUND: relative links inside the moved doc are rebased to its new
        directory (bundle-absolute links are left untouched).

    Then regenerates index.md across the bundle and appends a log entry. Use
    this for ANY reorganization — never hand-move files (that strands links).

    Args:
      from_id: current concept id, e.g. 'concepts/alpha'.
      to_id:   target concept id,   e.g. 'domains/web/alpha'.

    Returns {moved, from, to, path, links_rewritten}. Raises if the source is
    unknown or the target already exists."""
    from_id = _normalize_concept_id(from_id)
    to_id = _normalize_concept_id(to_id)
    if from_id == to_id:
        return {"moved": False, "from": from_id, "to": to_id, "links_rewritten": 0}

    from_path = BUNDLE_DIR / f"{from_id}.md"
    if not from_path.exists():
        raise FileNotFoundError(f"Unknown concept: {from_id}")
    to_path = BUNDLE_DIR / f"{to_id}.md"
    if to_path.exists():
        raise ValueError(f"Target already exists: {to_id}")

    from_file_rel = from_id + ".md"
    to_file_rel = to_id + ".md"
    old_dir = posixpath.dirname(from_file_rel)

    to_path.parent.mkdir(parents=True, exist_ok=True)
    from_path.rename(to_path)

    total = 0
    for p in _walk_concepts(BUNDLE_DIR):
        moved_old = old_dir if p == to_path else None
        total += _rewrite_doc_links(
            p,
            from_file_rel=from_file_rel,
            to_file_rel=to_file_rel,
            moved_old_dir=moved_old,
            bundle_root=BUNDLE_DIR,
        )

    _prune_empty_dirs(BUNDLE_DIR, BUNDLE_DIR / old_dir if old_dir else BUNDLE_DIR)
    generate_index()
    append_log(
        "Update",
        f"将概念 {from_id} 迁移至 {to_id}（重写 {total} 处链接）。",
    )
    return {
        "moved": True,
        "from": from_id,
        "to": to_id,
        "path": str(to_path.relative_to(KB_ROOT)),
        "links_rewritten": total,
    }


# --- web enrichment crawl --------------------------------------------------
#
# acquire_url pins ONE chosen article. The pair below adds the original
# agent's other capability: the LLM as its own crawler. start_web_crawl
# registers seeds and a crawl budget; fetch_url then enforces, inside the
# tool, a host allow-list, a page budget, a hop-depth cap, dedup, and a
# "must be reachable from a seed" check — so the model cannot overrun or
# wander off-site. Each fetch returns the page's markdown AND its outbound
# links so the model can decide which to follow.

from urllib.parse import urljoin, urlparse  # noqa: E402


class _WebState:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.seeds: list[str] = []
        self.allowed_hosts: set[str] = set()
        self.allowed_path_prefixes: list[str] = []
        self.denied_path_substrings: list[str] = []
        self.max_pages: int = 0
        self.max_depth: int = 0
        self.visited: set[str] = set()
        self.url_depth: dict[str, int] = {}
        self.fetched_count: int = 0

    @property
    def active(self) -> bool:
        return bool(self.seeds)


_web_state = _WebState()


def start_web_crawl(
    seeds: list[str],
    max_pages: int = 20,
    max_depth: int = 2,
    allowed_hosts: list[str] | None = None,
    denied_path_substrings: list[str] | None = None,
) -> dict[str, Any]:
    """Initialize a bounded web crawl and register its seed URLs.

    Resets any prior crawl state. Hosts of the seeds are auto-added to the
    allow-list; pass extra hosts via `allowed_hosts`. Only pages reachable
    from a seed (within max_depth hops) may be fetched.

    Args:
      seeds:  list of seed URLs to start from (depth 0).
      max_pages:          hard cap on total fetches this crawl (default 20).
      max_depth:          max hops from a seed (default 2).
      allowed_hosts:      extra hosts to permit beyond the seed hosts.
      denied_path_substrings: path substrings to block (e.g. '/tag/', '/page/').

    Returns {seeds, allowed_hosts, max_pages, max_depth}."""
    _web_state.reset()
    norm_seeds: list[str] = []
    for s in seeds or []:
        s = (s or "").strip()
        if not s:
            continue
        if not urlparse(s).scheme:
            s = "https://" + s
        norm_seeds.append(s)

    _web_state.seeds = norm_seeds
    _web_state.allowed_hosts = {urlparse(s).netloc for s in norm_seeds if urlparse(s).netloc}
    if allowed_hosts:
        _web_state.allowed_hosts |= {h for h in allowed_hosts if h}
    _web_state.denied_path_substrings = [d for d in (denied_path_substrings or []) if d]
    _web_state.max_pages = max(1, int(max_pages))
    _web_state.max_depth = max(0, int(max_depth))
    for s in norm_seeds:
        _web_state.url_depth.setdefault(s, 0)

    return {
        "seeds": _web_state.seeds,
        "allowed_hosts": sorted(_web_state.allowed_hosts),
        "max_pages": _web_state.max_pages,
        "max_depth": _web_state.max_depth,
    }


_HREF_RE = re.compile(r'<a\s[^>]*href=["\']([^"\']+)["\']', re.IGNORECASE)


def _extract_links(base_url: str, html: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for m in _HREF_RE.finditer(html):
        href = (m.group(1) or "").strip()
        if (
            not href
            or href.startswith("#")
            or href.lower().startswith(("mailto:", "javascript:", "tel:", "data:"))
        ):
            continue
        absu = urljoin(base_url, href)
        parsed = urlparse(absu)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            clean = parsed._replace(fragment="").geturl()
            if clean not in seen:
                seen.add(clean)
                out.append(clean)
    return out


def _fetch_and_parse(url: str) -> dict[str, Any]:
    from markdownify import markdownify as html_to_md

    html = _fetch_html(url)
    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return {
        "url": url,
        "title": title_m.group(1).strip() if title_m else url,
        "markdown": html_to_md(html),
        "links": _extract_links(url, html),
    }


def fetch_url(url: str) -> dict[str, Any]:
    """Fetch one page within the active crawl. Guards are enforced HERE, not
    by the model: scheme, host allow-list, denied-path blocklist, dedup,
    page budget, and hop-depth/reachability. Treat an `error` return as a
    signal to stop or pick a different URL — do not retry the same URL.

    Success: {url, title, markdown, links, fetched_count, max_pages_budget,
              depth, max_depth}.
    Rejected: {error, url, fetched_count, max_pages_budget}.
    """
    url = (url or "").strip()
    state = _web_state

    def _reject(reason: str) -> dict[str, Any]:
        return {
            "error": reason,
            "url": url,
            "fetched_count": state.fetched_count,
            "max_pages_budget": state.max_pages,
        }

    if not state.active:
        return _reject("no active crawl — call start_web_crawl first")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return _reject(f"unsupported scheme: {parsed.scheme or '(none)'}")
    if not parsed.netloc:
        return _reject("missing host in URL")
    if state.allowed_hosts and parsed.netloc not in state.allowed_hosts:
        return _reject(
            f"host not in allowed list: {parsed.netloc} "
            f"(allowed: {sorted(state.allowed_hosts)})"
        )
    path = parsed.path or "/"
    for bad in state.denied_path_substrings:
        if bad and bad in path:
            return _reject(f"path matches denied substring: {bad!r}")
    if url in state.visited:
        return _reject("already fetched in this crawl")
    if state.fetched_count >= state.max_pages:
        return _reject("max_pages reached")
    depth = state.url_depth.get(url)
    if depth is None:
        return _reject(
            "URL not reachable from a seed within the crawl graph "
            "(not returned as a link by any fetched page)"
        )
    if depth > state.max_depth:
        return _reject(f"depth {depth} exceeds max_depth {state.max_depth}")

    state.visited.add(url)
    state.fetched_count += 1
    try:
        page = _fetch_and_parse(url)
    except Exception as e:  # noqa: BLE001 - surface as a structured reject
        return _reject(f"fetch failed: {e}")

    child_depth = depth + 1
    for link in page["links"]:
        state.url_depth.setdefault(link, child_depth)

    return {
        "url": page["url"],
        "title": page["title"],
        "markdown": page["markdown"],
        "links": page["links"],
        "fetched_count": state.fetched_count,
        "max_pages_budget": state.max_pages,
        "depth": depth,
        "max_depth": state.max_depth,
    }
