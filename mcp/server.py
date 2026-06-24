#!/usr/bin/env python3
"""OKF-KB MCP server.

Exposes a small tool surface for curating an Open Knowledge Format (OKF)
knowledge base whose source material is web articles. Run it as a stdio MCP
server and point Claude Code (or any MCP client) at it.

See CLAUDE.md for the enrichment workflow and the hard rules the model must
honor when using these tools. The actual logic lives in okf_core.py; this
file only wraps each function as an MCP tool (docstrings become the model's
tool descriptions, so they are written for the model to read).
"""
from __future__ import annotations

import sys

from okf_core import (
    acquire_url as _acquire_url,
    append_log as _append_log,
    generate_index as _generate_index,
    list_articles as _list_articles,
    list_concepts as _list_concepts,
    move_concept as _move_concept,
    read_article as _read_article,
    read_existing_doc as _read_existing_doc,
    write_concept_doc as _write_concept_doc,
)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    print(
        "ERROR: the 'mcp' package is not installed. "
        "Run:  pip install -r requirements.txt",
        file=sys.stderr,
    )
    raise

mcp = FastMCP("okf-kb")


@mcp.tool()
def acquire_url(url: str, slug: str | None = None) -> dict:
    """Fetch a web article, convert it to markdown, and save it under
    sources/articles/. This is the ACQUIRE step: pin the article to a local
    file so later enrichment is reproducible. Always acquire BEFORE
    enriching — never treat a live URL as a source.

    Args:
      url:  the article URL to fetch.
      slug: optional filename stem for the saved article (auto-derived from
            the page <title> when omitted).

    Returns {id, path, title, bytes}. `id` is the article id to pass to
    read_article().
    """
    return _acquire_url(url, slug)


@mcp.tool()
def list_articles() -> list[dict]:
    """List every raw article in sources/articles/ (the corpus / 'catalog').

    Returns a list of {id, title, resource, timestamp}. Use this to see what
    source material is available before ingesting."""
    return _list_articles()


@mcp.tool()
def read_article(article_id: str) -> dict:
    """Read a raw source article. This is the equivalent of
    read_concept_raw in the original OKF agent: it returns the ground-truth
    material (the article prose) you should base a curated concept on.

    Returns {id, frontmatter, body}. Raises if the article id is unknown."""
    return _read_article(article_id)


@mcp.tool()
def list_concepts() -> list[dict]:
    """List every curated OKF concept already in the bundle. Use this to
    (a) check whether a concept already exists before writing it, and
    (b) discover valid link targets when weaving cross-links.

    Returns a list of {id, type, title, description, resource}. `id` is the
    slash-joined path used by read_existing_doc() / write_concept_doc()."""
    return _list_concepts()


@mcp.tool()
def read_existing_doc(concept_id: str) -> dict | None:
    """Read an existing curated concept doc, or return None if it does not
    exist. ALWAYS call this before write_concept_doc: a non-None result means
    you must AUGMENT (preserve every frontmatter key and every existing body
    heading), not rewrite.

    Returns {id, frontmatter, body} or None."""
    return _read_existing_doc(concept_id)


@mcp.tool()
def write_concept_doc(concept_id: str, frontmatter: dict, body: str) -> dict:
    """Write a curated OKF concept doc. This is a FULL REPLACEMENT, not a
    patch: the frontmatter argument must include EVERY key (type is required;
    timestamp may be omitted to auto-refresh). The body must be valid
    markdown ready for direct human/agent consumption — no preamble or
    reasoning narration.

    Args:
      concept_id:  slash-joined path, e.g. 'concepts/ga4_events'.
      frontmatter: dict; must include non-empty 'type'. When augmenting an
                   existing doc, copy every existing key verbatim and merge
                   tags as a union.
      body:        markdown body.

    Returns {id, path, created, bytes}."""
    return _write_concept_doc(concept_id, frontmatter, body)


@mcp.tool()
def generate_index() -> dict:
    """Regenerate index.md in every directory of the active bundle (OKF SPEC
    §6). Call this AFTER any write_concept_doc / append_log so the directory
    listing reflects current contents. Idempotent — safe to call repeatedly.

    Groups concept docs by their frontmatter `type`, lists each with its title
    and one-line description, and lists subdirectories. Pure deterministic (no
    LLM). Returns {written: [relative index.md paths]}."""
    return _generate_index()


@mcp.tool()
def append_log(action: str, summary: str) -> dict:
    """Append a dated entry to the bundle's log.md (OKF SPEC §7). Call this
    whenever a concept is created, materially updated, or deprecated, so the
    bundle keeps a chronological history.

    Enforces the §7 format: ISO 8601 YYYY-MM-DD date headings, newest date
    first, flat list under each date. Uses today's date (UTC).

    Args:
      action:  leading bold word, e.g. 'Creation', 'Update', 'Deprecation'.
      summary: one-line prose describing what changed.

    Returns {path, date, entry}."""
    return _append_log(action, summary)


@mcp.tool()
def move_concept(from_id: str, to_id: str) -> dict:
    """Move a concept to a new path AND rewrite every link it touches.

    Use this for ANY reorganization or re-categorization — never hand-move a
    file, because that strands links in both directions. This tool fixes both:
      - inbound links in OTHER docs that pointed at the old path, repointed at
        the new path (correct relative path from each doc);
      - the moved doc's OWN relative links, rebased to its new directory
        (bundle-absolute links are left untouched).
    Then it regenerates index.md and appends a log entry.

    Args:
      from_id: current concept id, e.g. 'concepts/alpha'.
      to_id:   target concept id,   e.g. 'domains/web/alpha'.

    Returns {moved, from, to, path, links_rewritten}."""
    return _move_concept(from_id, to_id)


if __name__ == "__main__":
    mcp.run()
