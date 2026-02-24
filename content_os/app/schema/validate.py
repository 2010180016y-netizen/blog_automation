from typing import Dict, Any, List

class SchemaValidator:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.fail_on_missing = self.config.get("structured_data", {}).get("validation", {}).get("fail_on_missing", ["name", "image", "offers"])

    def validate_product(self, jsonld: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        
        # Check required fields from config
        for field in self.fail_on_missing:
            if field not in jsonld or not jsonld[field]:
                errors.append(f"Missing required field: {field}")

        # Deep check for offers
        if "offers" in jsonld:
            offers = jsonld["offers"]
            if not offers.get("price"):
                errors.append("Missing price in offers")
            if not offers.get("priceCurrency"):
                errors.append("Missing priceCurrency in offers")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "type": jsonld.get("@type")
        }
