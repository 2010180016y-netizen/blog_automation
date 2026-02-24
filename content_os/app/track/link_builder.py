from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
from typing import Dict

class LinkBuilder:
    def __init__(self, config: Dict):
        self.config = config
        self.params_config = config.get("tracking", {}).get("link_params", {
            "channel_param": "ch",
            "content_id_param": "cid",
            "sku_param": "sku",
            "intent_param": "intent"
        })

    def build_tracking_link(self, base_url: str, channel: str, content_id: str, sku: str, intent: str) -> str:
        """
        Appends tracking parameters to a base URL.
        """
        u = urlparse(base_url)
        query = parse_qs(u.query)
        
        query[self.params_config["channel_param"]] = [channel]
        query[self.params_config["content_id_param"]] = [content_id]
        query[self.params_config["sku_param"]] = [sku]
        query[self.params_config["intent_param"]] = [intent]
        
        new_query = urlencode(query, doseq=True)
        return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))
