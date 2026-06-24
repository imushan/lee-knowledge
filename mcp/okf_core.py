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
    p = BUNDLE_DIR / f"{concept_id}.md"
    if not p.exists():
        return None
    fm, body = split_doc(p.read_text(encoding="utf-8"))
    return {"id": concept_id, "frontmatter": fm, "body": body}


def write_concept_doc(
    concept_id: str, frontmatter: dict[str, Any], body: str
) -> dict[str, Any]:
    """Write (full-replacement) a curated concept doc.

    Validation enforces the OKF invariants the model must honor:
      - frontmatter is a dict,
      - it carries a non-empty `type`,
      - a missing/empty `timestamp` is auto-refreshed to now (UTC).

    Returns {id, path, created, bytes}.
    """
    if not isinstance(frontmatter, dict):
        raise ValueError("frontmatter must be a dict")
    if not frontmatter.get("type"):
        raise ValueError("frontmatter missing required 'type' key")
    if not frontmatter.get("timestamp"):
        frontmatter["timestamp"] = _now_iso()

    p = BUNDLE_DIR / f"{concept_id}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    existed = p.exists()
    p.write_text(join_doc(frontmatter, body), encoding="utf-8")
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
    from_id = from_id.strip("/")
    to_id = to_id.strip("/")
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
