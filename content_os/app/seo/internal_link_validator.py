from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup


@dataclass
class LinkEdge:
    source_slug: str
    target_slug: str
    anchor: str


def _normalize_slug(url_or_slug: str) -> str:
    value = (url_or_slug or "").strip()
    if not value:
        return ""

    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        value = parsed.path

    value = value.split("#", 1)[0].split("?", 1)[0]
    value = value.strip("/")
    return value


def _extract_links_from_html(content_html: str) -> List[Tuple[str, str]]:
    soup = BeautifulSoup(content_html or "", "html.parser")
    links: List[Tuple[str, str]] = []
    for a in soup.find_all("a"):
        href = (a.get("href") or "").strip()
        anchor = a.get_text(" ", strip=True)
        if href:
            links.append((href, anchor))
    return links


def build_internal_link_graph(posts: List[Dict]) -> Dict[str, List[LinkEdge]]:
    post_slugs = {_normalize_slug(p.get("slug", "")) for p in posts}
    graph: Dict[str, List[LinkEdge]] = {slug: [] for slug in post_slugs if slug}

    for post in posts:
        source_slug = _normalize_slug(post.get("slug", ""))
        if not source_slug:
            continue

        candidate_links: List[Tuple[str, str]] = []
        for item in post.get("internal_links", []) or []:
            candidate_links.append((item.get("url", ""), item.get("anchor", "")))

        candidate_links.extend(_extract_links_from_html(post.get("content", "")))

        for raw_target, anchor in candidate_links:
            target_slug = _normalize_slug(raw_target)
            if not target_slug or target_slug == source_slug:
                continue
            if target_slug not in post_slugs:
                continue
            graph[source_slug].append(LinkEdge(source_slug=source_slug, target_slug=target_slug, anchor=anchor))

    return graph


def detect_orphan_pages(posts: List[Dict], graph: Dict[str, List[LinkEdge]], root_slugs: List[str] | None = None) -> List[str]:
    slugs = {_normalize_slug(p.get("slug", "")) for p in posts if p.get("slug")}
    inbound_count = {slug: 0 for slug in slugs}

    for edges in graph.values():
        for edge in edges:
            if edge.target_slug in inbound_count:
                inbound_count[edge.target_slug] += 1

    roots = {_normalize_slug(s) for s in (root_slugs or []) if _normalize_slug(s)}
    return sorted([slug for slug, count in inbound_count.items() if count == 0 and slug not in roots])


def simulate_crawler(graph: Dict[str, List[LinkEdge]], start_slugs: List[str], max_depth: int = 3) -> Dict[str, object]:
    visited: Set[str] = set()
    queue = deque([(_normalize_slug(slug), 0) for slug in start_slugs if _normalize_slug(slug)])

    while queue:
        slug, depth = queue.popleft()
        if slug in visited or depth > max_depth:
            continue
        visited.add(slug)
        for edge in graph.get(slug, []):
            if edge.target_slug not in visited:
                queue.append((edge.target_slug, depth + 1))

    return {
        "visited": sorted(visited),
        "visited_count": len(visited),
    }


def validate_internal_links(
    posts: List[Dict],
    start_slugs: List[str],
    max_depth: int = 3,
    min_anchor_chars: int = 2,
) -> Dict[str, object]:
    graph = build_internal_link_graph(posts)
    crawl = simulate_crawler(graph, start_slugs=start_slugs, max_depth=max_depth)
    orphan_pages = detect_orphan_pages(posts, graph, root_slugs=start_slugs)

    anchor_issues: List[Dict[str, str]] = []
    for edges in graph.values():
        for edge in edges:
            if len((edge.anchor or "").strip()) < min_anchor_chars:
                anchor_issues.append(
                    {
                        "source": edge.source_slug,
                        "target": edge.target_slug,
                        "reason": "anchor text too short for crawl relevance",
                    }
                )

    all_slugs = sorted({_normalize_slug(p.get("slug", "")) for p in posts if p.get("slug")})
    unreachable = sorted([slug for slug in all_slugs if slug not in set(crawl["visited"])])

    status = "PASS"
    if orphan_pages or unreachable or anchor_issues:
        status = "WARN"
    if anchor_issues and len(anchor_issues) >= 3:
        status = "REJECT"

    return {
        "status": status,
        "graph_nodes": len(all_slugs),
        "crawl": crawl,
        "orphans": orphan_pages,
        "unreachable": unreachable,
        "anchor_issues": anchor_issues,
    }
