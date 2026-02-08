import torch
import whisperx
import gc
from typing import List, Optional
from src.ports.interfaces import TranscriberPort
from src.domain.entities import TranscriptionResult, Segment, Word

class WhisperXAdapter(TranscriberPort):
    def __init__(self, model_name: str = "large-v3-turbo", device: str = None, batch_size: int = 16):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        self.batch_size = batch_size

    def transcribe(self, audio_path: str, language: str = None) -> TranscriptionResult:
        print(f"[WhisperX] Loading audio from {audio_path}...")
        audio = whisperx.load_audio(audio_path)

        print(f"[WhisperX] Loading model {self.model_name} on {self.device}...")
        model = whisperx.load_model(self.model_name, self.device, compute_type=self.compute_type, language=language)

        print("[WhisperX] Transcribing...")
        result = model.transcribe(audio, batch_size=self.batch_size)
        
        # Cleanup model from memory
        del model
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()

        # Alignment
        print("[WhisperX] Aligning...")
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=self.device)
        aligned_result = whisperx.align(result["segments"], model_a, audio, self.device, return_char_alignments=False)

        # Cleanup alignment model
        del model_a
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()

        return self._map_to_domain(aligned_result, audio_path)

    def _map_to_domain(self, raw_result: dict, audio_path: str) -> TranscriptionResult:
        segments = []
        for i, seg in enumerate(raw_result["segments"]):
            words = []
            if "words" in seg:
                for w in seg["words"]:
                    if "start" in w and "end" in w:
                        words.append(Word(
                            text=w["word"],
                            start=w["start"],
                            end=w["end"],
                            confidence=w.get("score", 1.0)
                        ))
            
            segments.append(Segment(
                id=i,
                text=seg.get("text", "").strip(),
                start=seg["start"],
                end=seg["end"],
                words=words
            ))

        # Calculate total duration if possible, or estimate from last segment
        duration = segments[-1].end if segments else 0.0
        
        return TranscriptionResult(
            language=raw_result.get("language", "en"),
            segments=segments,
            duration=duration
        )
