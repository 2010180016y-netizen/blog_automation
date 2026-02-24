from typing import List, Dict
from .templates import FIX_GUIDES, CHECKLIST_TEMPLATE, ITEM_TEMPLATE

class FixPlanGenerator:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.max_items = self.config.get("qa_fixplan", {}).get("rules", {}).get("max_items", 12)

    def generate(self, qa_report: Dict) -> Dict:
        """
        Converts a QA report (fails/warns) into a structured fix plan.
        """
        all_issues = []
        
        # Process Fails
        for fail in qa_report.get("fail", []):
            all_issues.append({**fail, "type": "FAIL", "priority": "🚨 REJECT"})
            
        # Process Warns
        for warn in qa_report.get("warn", []):
            all_issues.append({**warn, "type": "WARN", "priority": "⚠️ WARN"})

        # Limit items
        all_issues = all_issues[:self.max_items]
        
        checklist_items = []
        json_items = []

        for issue in all_issues:
            code = issue.get("code")
            guide = FIX_GUIDES.get(code, {
                "title": "기타 수정 사항",
                "action": issue.get("detail", "내용을 확인하고 수정하세요."),
                "priority": "MEDIUM"
            })
            
            location = issue.get("location", "본문 확인 필요")
            
            # Markdown Item
            item_md = ITEM_TEMPLATE.format(
                priority=issue["priority"],
                title=guide["title"],
                action=guide["action"],
                location=location
            )
            checklist_items.append(item_md)
            
            # JSON Item
            json_items.append({
                "code": code,
                "title": guide["title"],
                "action": guide["action"],
                "location": location,
                "severity": issue["type"]
            })

        markdown_output = CHECKLIST_TEMPLATE.format(
            status=qa_report.get("status", "UNKNOWN"),
            total_items=len(checklist_items),
            items="\n".join(checklist_items)
        )

        return {
            "markdown": markdown_output,
            "json": json_items,
            "total_count": len(json_items)
        }
