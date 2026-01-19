from abc import ABC, abstractmethod
from typing import List, TypedDict, Optional, Dict, Any

class StandardArticle(TypedDict):
    """
    StandardizedJSON output format for all data sources.
    This ensures Llama 3 always receives consistent data.
    """
    source_id: str          # e.g., 'gnews', 'serpapi_trends', 'twitter'
    source_name: str        # Human readable name, e.g., 'Google News'
    title: str              # Article title or trend summary
    url: str                # Link to source
    published_date: str     # ISO 8601 format preferred (YYYY-MM-DD)
    abstract: str           # Summary, snippet, or description
    full_text: Optional[str]# Full content if available
    metadata: Dict[str, Any]# Extra data (e.g., trend scores, author, likes)

class BaseSource(ABC):
    """
    Abstract Base Class that all data acquisition adapters must implement.
    """
    
    @abstractmethod
    def fetch(self, query: str) -> List[StandardArticle]:
        """
        Fetch data for a given query and return a list of StandardArticle objects.
        """
        pass
