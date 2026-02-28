from .image_seo import generate_descriptive_alt_text


def generate_alt_text(image_path: str, sku: str, context: str = "", primary_keyword: str = "") -> str:
    """Generate human-readable, description-first alt text with anti-stuffing guardrails."""
    return generate_descriptive_alt_text(
        image_path=image_path,
        sku=sku,
        context=context or "product usage scene",
        primary_keyword=primary_keyword,
    )
