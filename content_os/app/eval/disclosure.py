from __future__ import annotations

import re
from typing import Dict, List, Tuple


def _normalize_lang(language: str) -> str:
    return "ko" if language == "ko" else "en"


def apply_disclosure_templates(
    title: str,
    content: str,
    language: str,
    disclosure_required: bool,
    templates: Dict[str, Dict[str, str]],
) -> Tuple[str, str, List[str]]:
    """
    Auto-insert title/body disclosure labels for sponsored/affiliate content.
    Returns (title, content, applied_steps).
    """
    if not disclosure_required:
        return title, content, []

    lang = _normalize_lang(language)
    tpl = templates.get(lang, {})
    title_prefix = tpl.get("title_prefix", "")
    body_prefix = tpl.get("body_prefix", "")

    applied: List[str] = []
    next_title = title
    next_content = content

    if title_prefix and not next_title.startswith(title_prefix):
        next_title = f"{title_prefix} {next_title}".strip()
        applied.append("title_prefix")

    if body_prefix and body_prefix not in next_content[:180]:
        next_content = f"{body_prefix}\n\n{next_content}".strip()
        applied.append("body_prefix")

    return next_title, next_content, applied


def annotate_affiliate_links(content: str, language: str, template: str, affiliate_domains: List[str]) -> str:
    """
    Place a disclosure line right before affiliate links if not already present nearby.
    """
    _normalize_lang(language)
    marker = template.strip()

    if not marker:
        return content

    url_pattern = re.compile(r"https?://[^\s)]+")
    lines = content.splitlines()
    result: List[str] = []

    for line in lines:
        has_url = bool(url_pattern.search(line))
        if not has_url:
            result.append(line)
            continue

        lower_line = line.lower()
        is_affiliate = any(token in lower_line for token in ["ref=", "aff", "affiliate", "utm_source=partner"]) or any(
            domain.lower() in lower_line for domain in affiliate_domains
        )
        if not is_affiliate:
            result.append(line)
            continue

        prev = result[-1] if result else ""
        if marker.lower() not in prev.lower() and marker.lower() not in lower_line:
            result.append(marker)
        result.append(line)

    return "\n".join(result)
