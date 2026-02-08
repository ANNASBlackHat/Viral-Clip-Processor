from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional

@dataclass
class Word:
    text: str
    start: float  # seconds
    end: float
    confidence: float = 1.0

@dataclass
class Segment:
    id: int
    text: str
    start: float
    end: float
    words: List[Word]

@dataclass
class TranscriptionResult:
    language: str
    segments: List[Segment]
    duration: float

@dataclass
class ClipSuggestion:
    title: str
    viral_score: int
    segment_ids: List[int]
    reasoning: str
    execution_plan: Dict[str, Any]
    start_time: float = 0.0
    end_time: float = 0.0

@dataclass
class Speaker:
    id: int
    center_x: int  # pixel position
    bounding_box: Tuple[int, int, int, int]  # x1, y1, x2, y2
    frame_index: int

@dataclass
class TimeRange:
    start: float
    end: float

@dataclass
class Clip:
    title: str
    description: str
    segments: List[TimeRange]
    source_video: str = ""
    viral_score: int = 0

