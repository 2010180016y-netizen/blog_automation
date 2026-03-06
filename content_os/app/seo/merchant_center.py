from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from xml.etree import ElementTree as ET


def load_products_from_db(db_path: str = "blogs.db") -> List[Dict[str, Any]]:
    products: List[Dict[str, Any]] = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT sku, name, price, shipping, product_link, options,
                   as_info, prohibited_expressions, mandatory_disclaimer,
                   evidence_data, created_at
            FROM products
            WHERE name IS NOT NULL AND product_link IS NOT NULL
            """
        )
        for row in cursor:
            products.append(dict(row))
    return products


def generate_product_merchant_jsonld(product: Dict[str, Any], site_url: str, currency: str = "KRW") -> Dict[str, Any]:
    sku = str(product.get("sku") or "")
    url = product.get("product_link") or f"{site_url.rstrip('/')}/products/{sku}"
    price = product.get("price")
    shipping_cost = _extract_shipping_cost(product.get("shipping"))

    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "sku": sku,
        "name": product.get("name"),
        "description": product.get("as_info") or product.get("mandatory_disclaimer") or "",
        "url": url,
        "offers": {
            "@type": "Offer",
            "url": url,
            "priceCurrency": currency,
            "price": str(price) if price is not None else None,
            "availability": "https://schema.org/InStock",
            "shippingDetails": {
                "@type": "OfferShippingDetails",
                "shippingRate": {
                    "@type": "MonetaryAmount",
                    "value": str(shipping_cost),
                    "currency": currency,
                },
            },
        },
    }


def _extract_shipping_cost(shipping_value: Optional[str]) -> int:
    if not shipping_value:
        return 0
    digits = "".join(c for c in str(shipping_value) if c.isdigit())
    return int(digits) if digits else 0


def validate_merchant_item(product: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required = ["sku", "name", "price", "product_link"]
    for field in required:
        if not product.get(field):
            errors.append(f"Missing required field: {field}")

    if product.get("price") is not None:
        try:
            if float(product["price"]) <= 0:
                errors.append("price must be greater than 0")
        except Exception:
            errors.append("price must be numeric")

    return errors


def generate_merchant_center_feed(
    products: List[Dict[str, Any]],
    output_path: str,
    site_url: str,
    title: str = "Content OS Merchant Feed",
    description: str = "Product feed for Merchant Center",
    currency: str = "KRW",
) -> Dict[str, Any]:
    g_ns = "http://base.google.com/ns/1.0"
    ET.register_namespace("g", g_ns)

    rss = ET.Element("rss", version="2.0", attrib={"xmlns:g": g_ns})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = title
    ET.SubElement(channel, "link").text = site_url.rstrip("/")
    ET.SubElement(channel, "description").text = description

    valid_count = 0
    errors: List[Dict[str, Any]] = []

    for p in products:
        item_errors = validate_merchant_item(p)
        if item_errors:
            errors.append({"sku": p.get("sku"), "errors": item_errors})
            continue

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, f"{{{g_ns}}}id").text = str(p.get("sku"))
        ET.SubElement(item, f"{{{g_ns}}}title").text = str(p.get("name"))
        ET.SubElement(item, f"{{{g_ns}}}link").text = str(p.get("product_link"))
        ET.SubElement(item, f"{{{g_ns}}}price").text = f"{p.get('price')} {currency}"
        ET.SubElement(item, f"{{{g_ns}}}availability").text = "in_stock"
        ET.SubElement(item, f"{{{g_ns}}}condition").text = "new"
        ET.SubElement(item, f"{{{g_ns}}}shipping").text = str(p.get("shipping") or "0")
        valid_count += 1

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(rss).write(path, encoding="utf-8", xml_declaration=True)

    return {
        "path": str(path),
        "valid_count": valid_count,
        "error_count": len(errors),
        "errors": errors,
    }


def _fingerprint_product(product: Dict[str, Any]) -> str:
    basis = {
        "sku": product.get("sku"),
        "price": product.get("price"),
        "shipping": product.get("shipping"),
        "product_link": product.get("product_link"),
        "options": product.get("options"),
    }
    raw = json.dumps(basis, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def detect_product_changes(products: List[Dict[str, Any]], snapshot_path: str) -> Dict[str, List[str]]:
    current = {str(p.get("sku")): _fingerprint_product(p) for p in products if p.get("sku")}

    p = Path(snapshot_path)
    previous: Dict[str, str] = {}
    if p.exists():
        previous = json.loads(p.read_text(encoding="utf-8"))

    new = [sku for sku in current.keys() if sku not in previous]
    removed = [sku for sku in previous.keys() if sku not in current]
    changed = [sku for sku, fp in current.items() if sku in previous and previous[sku] != fp]

    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "new": sorted(new),
        "changed": sorted(changed),
        "removed": sorted(removed),
    }
