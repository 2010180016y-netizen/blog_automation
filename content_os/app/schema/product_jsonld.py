import json
from typing import Dict, Any

class ProductJsonLdGenerator:
    def generate(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a Product JSON-LD object from raw product data.
        """
        sku = product_data.get("sku")
        name = product_data.get("name")
        image = product_data.get("image_url")
        description = product_data.get("description")
        price = product_data.get("price")
        currency = product_data.get("currency", "KRW")
        availability = product_data.get("availability", "https://schema.org/InStock")
        brand = product_data.get("brand", "Unknown")

        jsonld = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": name,
            "image": [image] if image else [],
            "description": description,
            "sku": sku,
            "brand": {
                "@type": "Brand",
                "name": brand
            },
            "offers": {
                "@type": "Offer",
                "url": product_data.get("url"),
                "priceCurrency": currency,
                "price": price,
                "availability": availability
            }
        }
        
        # Clean up None values
        return {k: v for k, v in jsonld.items() if v is not None}

    def to_string(self, jsonld: Dict[str, Any]) -> str:
        return json.dumps(jsonld, indent=2, ensure_ascii=False)
