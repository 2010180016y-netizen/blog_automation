from typing import List, Dict, Optional
from .state_machine import ContentState, StateMachine

class PublishQueue:
    def __init__(self, config: Dict):
        self.config = config
        self.items: Dict[str, Dict] = {} # content_id -> item

    def add_item(self, content_id: str, data: Dict):
        self.items[content_id] = {
            "id": content_id,
            "data": data,
            "state": ContentState.DRAFT,
            "history": [ContentState.DRAFT],
            "human_approval_required": False
        }

    def update_state(self, content_id: str, next_state: ContentState):
        item = self.items.get(content_id)
        if not item:
            raise ValueError("Item not found")
            
        StateMachine.validate_transition(item["state"], next_state)
        
        # Governance check
        if next_state == ContentState.READY:
            platform = item["data"].get("platform")
            if platform in self.config.get("publishing", {}).get("governance", {}).get("require_human_approval_for", []):
                item["human_approval_required"] = True
        
        item["state"] = next_state
        item["history"].append(next_state)

    def get_ready_items(self, platform: str) -> List[Dict]:
        return [
            item for item in self.items.values()
            if item["state"] == ContentState.READY 
            and item["data"].get("platform") == platform
            and not item["human_approval_required"]
        ]

    def approve(self, content_id: str):
        if content_id in self.items:
            self.items[content_id]["human_approval_required"] = False
