from abc import ABC, abstractmethod
from typing import List
from src.domain.entities import ClipSuggestion

class ResponseParser(ABC):
    """Abstract base class for AI response parsers."""
    
    @abstractmethod
    def parse(self, data: dict) -> ClipSuggestion:
        """Parse a single clip object from AI response."""
        pass
    
    def parse_response(self, data) -> List[ClipSuggestion]:
        """Parse the full AI response (list or single object)."""
        if isinstance(data, list):
            return [self.parse(item) for item in data]
        return [self.parse(data)]
