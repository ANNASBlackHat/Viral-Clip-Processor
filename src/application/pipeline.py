from typing import List, Dict
import os
import math
from src.ports.interfaces import (
    TranscriberPort, AIAnalyzerPort, VideoEditorPort, 
    DownloaderPort, NotifierPort, FaceDetectorPort
)
from src.domain.entities import ClipSuggestion, Clip, TimeRange, TranscriptionResult

class ClipProcessorPipeline:
    def __init__(
        self,
        downloader: DownloaderPort,
        transcriber: TranscriberPort,
        analyzer: AIAnalyzerPort,
        editor: VideoEditorPort,
        detector: FaceDetectorPort,
        notifier: NotifierPort
    ):
        self.downloader = downloader
        self.transcriber = transcriber
        self.analyzer = analyzer
        self.editor = editor
        self.detector = detector
        self.notifier = notifier

    def process(self, url: str, output_dir: str) -> List[str]:
        print(f"=== Starting Pipeline for {url} ===")
        
        # 1. Download
        video_path = self.downloader.download(url, output_dir)
        print(f"Video downloaded to: {video_path}")
        
        # 2. Transcribe (Extract audio internally or pass video path if transcriber supports it)
        # WhisperX/OpenAI supports video files usually, ffmpeg extracts audio on fluid
        # We pass video_path directly
        transcript = self.transcriber.transcribe(video_path, language="id")
        print(f"Transcription complete. Found {len(transcript.segments)} segments.")
        
        # 3. Format Transcript for AI
        formatted_text, segment_map = self._format_transcript(transcript)
        
        # 4. Analyze
        suggestions = self.analyzer.analyze_for_viral_clips(formatted_text)
        print(f"AI suggested {len(suggestions)} clips.")
        
        # 5. Map Suggestions to Clips (Resolve Timestamps)
        clips = self._resolve_clips(suggestions, segment_map)
        
        if not clips:
            print("No valid clips found.")
            return []
            
        # 6. Extract Clips
        clip_paths = self.editor.extract_clips(video_path, clips, output_dir)
        print(f"Extracted {len(clip_paths)} clips.")
        
        # 7. (Optional/Future) Vertical Crop & Subtitles
        # For now, we just notify
        
        # 8. Notify
        if self.notifier:
            self.notifier.send_message(f"Processed {len(clip_paths)} clips from {url}")
            for path in clip_paths:
                self.notifier.send_file(path)
                
        return clip_paths

    def _format_transcript(self, transcript: TranscriptionResult):
        formatted_lines = []
        segment_map = {}
        
        for seg in transcript.segments:
            # Simple format: [ID] (Start-End) Text
            start = math.floor(seg.start)
            end = math.ceil(seg.end)
            line = f"[{seg.id}] ({start}-{end}s) {seg.text}"
            formatted_lines.append(line)
            
            segment_map[seg.id] = seg
            
        return "\n".join(formatted_lines), segment_map

    def _resolve_clips(self, suggestions: List[ClipSuggestion], segment_map: Dict[int, any]) -> List[Clip]:
        resolved_clips = []
        
        for sugg in suggestions:
            time_ranges = []
            
            # Filter valid segments
            valid_ids = [sid for sid in sugg.segment_ids if sid in segment_map]
            if not valid_ids:
                continue
                
            # Merge consecutive segments logic (optional but good)
            # For now, just map 1:1, the editor handles concatenation
            # BUT editor expects TimeRange. 
            # We can merge here to optimize editor calls (less trim filters)
            
            # Simple merge logic:
            if not valid_ids: continue
            
            sorted_segments = sorted([segment_map[sid] for sid in valid_ids], key=lambda s: s.start)
            
            current_start = sorted_segments[0].start
            current_end = sorted_segments[0].end
            
            for i in range(1, len(sorted_segments)):
                seg = sorted_segments[i]
                # If gap is small (< 0.5s), merge
                if seg.start - current_end < 0.5:
                    current_end = seg.end
                else:
                    time_ranges.append(TimeRange(current_start, current_end))
                    current_start = seg.start
                    current_end = seg.end
            
            time_ranges.append(TimeRange(current_start, current_end))
            
            resolved_clips.append(Clip(
                title=sugg.title,
                description=sugg.reasoning,
                segments=time_ranges,
                viral_score=sugg.viral_score
            ))
            
        return resolved_clips
