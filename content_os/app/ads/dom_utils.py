from bs4 import BeautifulSoup
from typing import List, Dict, Any

class DomUtils:
    @staticmethod
    def find_elements(html: str, selectors: List[str]) -> List[Any]:
        """
        Finds elements matching the given CSS selectors.
        """
        soup = BeautifulSoup(html, 'html.parser')
        elements = []
        for selector in selectors:
            elements.extend(soup.select(selector))
        return elements

    @staticmethod
    def get_element_info(element: Any) -> Dict[str, Any]:
        """
        Extracts basic info about a DOM element.
        """
        return {
            "tag": element.name,
            "id": element.get('id'),
            "classes": element.get('class', []),
            "text": element.get_text(strip=True)[:50]
        }
