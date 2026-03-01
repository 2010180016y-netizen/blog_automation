from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
from typing import Dict, Optional


class LinkBuilder:
    def __init__(self, config: Dict):
        self.config = config
        self.params_config = config.get(
            "tracking",
            {},
        ).get(
            "link_params",
            {
                "channel_param": "ch",
                "content_id_param": "cid",
                "sku_param": "sku",
                "intent_param": "intent",
                "variant_param": "variant",
            },
        )

    def build_tracking_link(
        self,
        base_url: str,
        channel: str,
        content_id: str,
        sku: str,
        intent: str,
        variant: Optional[str] = None,
    ) -> str:
        """
        Enforces required tracking params: ch/cid/sku/intent.
        For A/B publishing, optional `variant` parameter is appended.
        """
        if not base_url:
            raise ValueError("base_url is required")

        required = {
            "channel": channel,
            "content_id": content_id,
            "sku": sku,
            "intent": intent,
        }
        for k, v in required.items():
            if v is None or str(v).strip() == "":
                raise ValueError(f"{k} is required")

        u = urlparse(base_url)
        if not u.scheme or not u.netloc:
            raise ValueError("base_url must be absolute URL")

        query = parse_qs(u.query)
        query[self.params_config["channel_param"]] = [channel]
        query[self.params_config["content_id_param"]] = [content_id]
        query[self.params_config["sku_param"]] = [sku]
        query[self.params_config["intent_param"]] = [intent]
        if variant:
            query[self.params_config["variant_param"]] = [variant]

        new_query = urlencode(query, doseq=True)
        return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))
