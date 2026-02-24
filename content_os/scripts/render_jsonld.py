import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schema.product_jsonld import ProductJsonLdGenerator
from app.schema.validate import SchemaValidator

def render_jsonld(sku: str):
    # Mock Product DB lookup
    product_db = {
        "SKU001": {
            "sku": "SKU001",
            "name": "프리미엄 기계식 키보드",
            "image_url": "https://cdn.example.com/kb001.jpg",
            "description": "최고의 타건감을 자랑하는 기계식 키보드입니다.",
            "price": 159000,
            "currency": "KRW",
            "brand": "TechMaster",
            "url": "https://store.example.com/products/kb001"
        }
    }

    data = product_db.get(sku)
    if not data:
        print(f"Error: Product {sku} not found in DB.")
        return

    generator = ProductJsonLdGenerator()
    validator = SchemaValidator()

    jsonld = generator.generate(data)
    report = validator.validate_product(jsonld)

    print("--- JSON-LD Output ---")
    print(generator.to_string(jsonld))
    print("\n--- Validation Report ---")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/render_jsonld.py <sku>")
    else:
        render_jsonld(sys.argv[1])
