from typing import List, Dict
from .ko_rules import KoBannedClaimsRule, KoDisclosureRule
from .en_rules import EnBannedClaimsRule, EnDisclosureRule

class RuleCatalog:
    def __init__(self, config: Dict):
        self.config = config
        self.ko_rules = [
            KoBannedClaimsRule(config['compliance']['banned_claims']['ko']),
            KoDisclosureRule()
        ]
        self.en_rules = [
            EnBannedClaimsRule(config['compliance']['banned_claims']['en']),
            EnDisclosureRule()
        ]

    def get_rules(self, lang: str):
        if lang == "ko":
            return self.ko_rules
        return self.en_rules
