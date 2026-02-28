from typing import Dict

from .en_rules import EnBannedClaimsRule, EnDisclosureRule
from .ko_rules import KoBannedClaimsRule, KoDisclosureRule


class RuleCatalog:
    def __init__(self, config: Dict):
        self.config = config
        compliance = config["compliance"]

        ko_terms = compliance["required_disclosures"]["ko"]
        en_terms = compliance["required_disclosures"]["en"]
        affiliate_domains = compliance.get("affiliate_domains", [])
        link_window_chars = int(compliance.get("affiliate_disclosure_window_chars", 200))

        self.ko_rules = [
            KoBannedClaimsRule(compliance["banned_claims"]["ko"]),
            KoDisclosureRule(ko_terms, affiliate_domains, link_window_chars=link_window_chars),
        ]
        self.en_rules = [
            EnBannedClaimsRule(compliance["banned_claims"]["en"]),
            EnDisclosureRule(en_terms, affiliate_domains, link_window_chars=link_window_chars),
        ]

    def get_rules(self, lang: str):
        if lang == "ko":
            return self.ko_rules
        return self.en_rules
