import whisper
from src.ports.interfaces import TranscriberPort
from src.domain.entities import TranscriptionResult, Segment, Word

class OpenAIWhisperAdapter(TranscriberPort):
    def __init__(self, model_size: str = "medium", device: str = None):
        self.model_size = model_size
        self.device = device  # Whisper auto-detects, but can be forced

    def transcribe(self, audio_path: str, language: str = None) -> TranscriptionResult:
        print(f"[OpenAI Whisper] Loading model {self.model_size}...")
        model = whisper.load_model(self.model_size, device=self.device)

        print(f"[OpenAI Whisper] Transcribing {audio_path}...")
        result = model.transcribe(
            audio_path, 
            language=language, 
            word_timestamps=True
        )

        return self._map_to_domain(result)

    def _map_to_domain(self, raw_result: dict) -> TranscriptionResult:
        segments = []
        for i, seg in enumerate(raw_result.get("segments", [])):
            words = []
            # OpenAI Whisper structure for words is slightly different
            if "words" in seg:
                for w in seg["words"]:
                    words.append(Word(
                        text=w["word"],
                        start=w["start"],
                        end=w["end"],
                        confidence=w.get("probability", 1.0)
                    ))
            
            segments.append(Segment(
                id=seg.get("id", i),
                text=seg.get("text", "").strip(),
                start=seg["start"],
                end=seg["end"],
                words=words
            ))

        duration = segments[-1].end if segments else 0.0
        
        return TranscriptionResult(
            language=raw_result.get("language", "en"),
            segments=segments,
            duration=duration
        )
