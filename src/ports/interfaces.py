from abc import ABC, abstractmethod
from typing import List, Optional, Any
from src.domain.entities import TranscriptionResult, ClipSuggestion, Speaker, Segment, TimeRange

class TranscriberPort(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, language: str = None) -> TranscriptionResult:
        """Transcribe audio and return word-level timestamps."""
        pass

class AIAnalyzerPort(ABC):
    @abstractmethod
    def analyze_for_viral_clips(
        self, 
        formatted_transcript: str,
        additional_prompt: str = ""
    ) -> List[ClipSuggestion]:
        """Identify viral-worthy moments from transcript."""
        pass

class VideoEditorPort(ABC):
    @abstractmethod
    def extract_clips(
        self, 
        video_path: str, 
        clips: List[ClipSuggestion],
        output_dir: str
    ) -> List[str]:
        """Cut video into clips, return output file paths."""
        pass
    
    @abstractmethod
    def crop_to_vertical(
        self,
        video_path: str,
        output_path: str,
        speaker_positions: List[int] = None
    ) -> str:
        """Convert landscape to 9:16 vertical."""
        pass

    @abstractmethod
    def burn_subtitles(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str
    ) -> str:
        """Burn subtitles (.ass or .srt) into video."""
        pass

class FaceDetectorPort(ABC):
    @abstractmethod
    def detect_per_frame(self, video_path: str) -> List[Optional[Speaker]]:
        """Return speaker detection for each frame."""
        pass

class DownloaderPort(ABC):
    @abstractmethod
    def download(self, url: str, output_dir: str) -> str:
        """Download video/audio from URL, return local path."""
        pass

class NotifierPort(ABC):
    @abstractmethod
    def send_file(self, file_path: str) -> bool:
        pass
    
    @abstractmethod
    def send_message(self, text: str) -> bool:
        pass

class SubtitleGeneratorPort(ABC):
    @abstractmethod
    def generate(self, segments: List[Segment], clip_ranges: List[TimeRange], output_path: str) -> str:
        """Generate subtitle file (e.g., .ass or .srt)."""
        pass
