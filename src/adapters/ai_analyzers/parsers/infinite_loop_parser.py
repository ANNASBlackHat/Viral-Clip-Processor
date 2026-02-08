from src.adapters.ai_analyzers.parsers.base import ResponseParser
from src.domain.entities import ClipSuggestion

class InfiniteLoopParser(ResponseParser):
    """
    Parser for infinite_loop.txt prompt output.
    
    Expected format:
    {
      "title": "...",
      "narrative_arc": {
        "hook_ids": [...],
        "context_ids": [...],
        "story_ids": [...],
        "conclusion_ids": [...]
      },
      "final_clip_sequence": [...],
      "reasoning": "..."
    }
    """
    
    def parse(self, data: dict) -> ClipSuggestion:
        # Prefer final_clip_sequence if present, otherwise combine arc IDs
        arc = data.get("narrative_arc", {})
        
        if "final_clip_sequence" in data:
            segment_ids = data["final_clip_sequence"]
        else:
            # Combine all arc IDs in narrative order
            segment_ids = (
                arc.get("hook_ids", []) +
                arc.get("context_ids", []) +
                arc.get("story_ids", []) +
                arc.get("conclusion_ids", [])
            )
        
        return ClipSuggestion(
            title=data.get("title", "Untitled"),
            viral_score=5,  # This format doesn't have viral_score
            segment_ids=segment_ids,
            reasoning=data.get("reasoning", ""),
            execution_plan={"narrative_arc": arc}  # Store arc for reference
        )
