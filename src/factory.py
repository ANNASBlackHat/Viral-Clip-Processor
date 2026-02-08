from typing import Dict
import os
from src.ports.interfaces import (
    TranscriberPort, AIAnalyzerPort, VideoEditorPort, 
    DownloaderPort, NotifierPort, FaceDetectorPort
)
from src.adapters.transcribers.whisperx_adapter import WhisperXAdapter
from src.adapters.transcribers.openai_whisper_adapter import OpenAIWhisperAdapter
from src.adapters.ai_analyzers.gemini_adapter import GeminiAdapter
from src.adapters.video_editors.ffmpeg_adapter import FFmpegAdapter
from src.adapters.face_detectors.yolo_adapter import YoloAdapter
from src.adapters.downloaders.ytdlp_adapter import YtDlpDownloader
from src.adapters.notifiers.telegram_adapter import TelegramNotifier

class ServiceFactory:
    def __init__(self, config: Dict):
        self.config = config

    def get_transcriber(self) -> TranscriberPort:
        engine = self.config.get("transcriber", "whisperx")
        if engine == "whisperx":
            return WhisperXAdapter(
                model_name=self.config.get("whisper_model", "large-v3-turbo")
            )
        elif engine == "openai_whisper":
            return OpenAIWhisperAdapter(
                model_size=self.config.get("whisper_model", "medium")
            )
        else:
            raise ValueError(f"Unknown transcriber: {engine}")

    def get_ai_analyzer(self) -> AIAnalyzerPort:
        # Currently only Gemini supported
        api_key = os.getenv("GEMINI_API_KEY") # Or from config
        if not api_key:
             print("Warning: GEMINI_API_KEY not found in env.")
        
        return GeminiAdapter(
            api_key=api_key
        )

    def get_video_editor(self) -> VideoEditorPort:
        return FFmpegAdapter(use_gpu=self.config.get("use_gpu", True))

    def get_face_detector(self) -> FaceDetectorPort:
        return YoloAdapter()

    def get_downloader(self) -> DownloaderPort:
        return YtDlpDownloader()

    def get_notifier(self) -> NotifierPort:
        if self.config.get("notification", {}).get("telegram", {}).get("enabled", False):
            # Fetch from env or config
            return TelegramNotifier(
                bot_token=os.getenv("TELEGRAM_TOKEN"),
                chat_id=os.getenv("TELEGRAM_CHAT_ID")
            )
        return None 
