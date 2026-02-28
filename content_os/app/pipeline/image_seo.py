from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup


def _tokenize_filename(image_path: str) -> List[str]:
    stem = Path(image_path).stem
    tokens = re.split(r"[_\-\s]+", stem)
    cleaned = [t for t in tokens if t and not t.isdigit() and t.lower() not in {"img", "image", "photo", "frame"}]
    return cleaned[:5]


def detect_keyword_stuffing_alt(alt_text: str, keywords: List[str], max_keyword_repeats: int = 1, max_ratio: float = 0.35) -> bool:
    lower = alt_text.lower()
    words = [w for w in re.split(r"\s+", lower) if w]
    if not words:
        return False

    keyword_hits = 0
    for keyword in keywords:
        key = keyword.strip().lower()
        if not key:
            continue
        count = lower.count(key)
        keyword_hits += count
        if count > max_keyword_repeats:
            return True

    return (keyword_hits / len(words)) > max_ratio if keywords else False


def generate_descriptive_alt_text(
    image_path: str,
    sku: str,
    context: str = "",
    primary_keyword: str = "",
    max_words: int = 16,
) -> str:
    tokens = _tokenize_filename(image_path)
    context_phrase = context.strip() or "product detail"
    token_phrase = " ".join(tokens).strip()

    base = f"{sku} {context_phrase}".strip()
    if token_phrase:
        base = f"{base}, {token_phrase}"
    if primary_keyword:
        base = f"{base} featuring {primary_keyword.strip()}"

    words = [w for w in re.split(r"\s+", base) if w]
    trimmed = " ".join(words[:max_words])

    keywords = [primary_keyword] if primary_keyword else []
    if detect_keyword_stuffing_alt(trimmed, keywords):
        trimmed = f"{sku} {context_phrase}".strip()

    return trimmed


def optimize_image_asset(
    input_path: str,
    output_dir: str,
    max_width: int = 1600,
    quality: int = 82,
    prefer_webp: bool = True,
) -> Dict[str, object]:
    path = Path(input_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    target_suffix = ".webp" if prefer_webp else path.suffix.lower()
    output_path = out_dir / f"{path.stem}{target_suffix}"

    report = {
        "source": str(path),
        "output": str(output_path),
        "resized": False,
        "webp_converted": False,
        "lazy_loading": {"loading": "lazy", "decoding": "async"},
        "warnings": [],
    }

    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as img:
            width, height = img.size
            if width > max_width:
                next_height = int((max_width / width) * height)
                img = img.resize((max_width, next_height))
                report["resized"] = True

            if prefer_webp:
                img.save(output_path, format="WEBP", quality=quality, optimize=True)
                report["webp_converted"] = True
            else:
                img.save(output_path, quality=quality, optimize=True)

    except Exception as exc:
        fallback_output = out_dir / path.name
        shutil.copy2(path, fallback_output)
        report["output"] = str(fallback_output)
        report["warnings"].append(f"image optimizer fallback used: {exc}")

    return report


def apply_lazy_loading_to_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all("img"):
        if not img.get("loading"):
            img["loading"] = "lazy"
        if not img.get("decoding"):
            img["decoding"] = "async"
    return str(soup)
