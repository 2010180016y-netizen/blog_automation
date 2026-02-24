from abc import ABC, abstractmethod
from typing import List, Dict

class BaseRule(ABC):
    @abstractmethod
    def evaluate(self, content: str, context: Dict) -> Dict:
        pass
