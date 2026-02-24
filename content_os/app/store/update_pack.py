from typing import Dict, Any, List

class StoreUpdatePackGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fields = config.get("store_improve", {}).get("pack_fields", ["top_questions", "recommended_answers", "warnings", "comparison_table"])

    def generate_pack(self, sku: str, insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a store update package based on extracted insights.
        """
        pack = {
            "sku": sku,
            "type": "store_update_pack",
            "version": "1.0",
            "content": {}
        }

        if "top_questions" in self.fields:
            pack["content"]["qna"] = [
                {"q": q["question"], "a": "TBD: Generate answer based on product specs"}
                for q in insights.get("top_questions", [])
            ]

        if "warnings" in self.fields:
            pack["content"]["warnings"] = insights.get("warnings", [])

        if "comparison_table" in self.fields:
            # Mock comparison table logic
            pack["content"]["comparison_table"] = {
                "headers": ["Feature", "Our Product", "Competitor A"],
                "rows": [
                    ["Price", "Competitive", "High"],
                    ["Quality", "Premium", "Standard"]
                ]
            }

        return pack
