import os

def generate_alt_text(image_path: str, sku: str, context: str = "") -> str:
    """Generates alt text for an image. LLM integration point."""
    filename = os.path.basename(image_path)
    # Rule-based fallback
    base_alt = f"Image of {sku} - {filename}"
    if "frame" in filename:
        return f"Video highlight of {sku} showing product in use"
    return base_alt
