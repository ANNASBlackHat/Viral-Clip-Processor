from src.adapters.ai_analyzers.parsers.base import ResponseParser
from src.domain.entities import ClipSuggestion

class ViralFormulaParser(ResponseParser):
    """
    Parser for viral_formula.txt prompt output.
    
    Expected format:
    {
      "title": "...",
      "viral_score": 8,
      "hook_segment_id": 5,
      "segments_ids": [5, 6, 7, 8],
      "reasoning": "...",
      "execution_plan": {...}
    }
    """
    
    def parse(self, data: dict) -> ClipSuggestion:
        return ClipSuggestion(
            title=data.get("title", "Untitled"),
            viral_score=int(data.get("viral_score", 5)),
            segment_ids=data.get("segments_ids", []),
            reasoning=data.get("reasoning", ""),
            execution_plan=data.get("execution_plan", {})
        )
