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
        notifier: NotifierPort,
        subtitle_generator: any = None
    ):
        self.downloader = downloader
        self.transcriber = transcriber
        self.analyzer = analyzer
        self.editor = editor
        self.detector = detector
        self.notifier = notifier
        self.subtitle_generator = subtitle_generator

    def process(self, url: str, output_dir: str) -> List[str]:
        print(f"=== Starting Pipeline for {url} ===")
        
        # 1. Download
        video_path = self.downloader.download(url, output_dir)
        print(f"Video downloaded to: {video_path}")
        
        # 2. Extract Audio
        base_name, _ = os.path.splitext(os.path.basename(video_path))
        audio_path = os.path.join(output_dir, f"{base_name}.mp3")
        
        if not os.path.exists(audio_path):
            import subprocess
            print(f"Extracting audio from {video_path} to {audio_path}...")
            cmd = [
                "ffmpeg", "-y", "-i", video_path, 
                "-vn", "-acodec", "libmp3lame", "-q:a", "2", 
                audio_path
            ]
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error during audio extraction: {e.stderr}")
                raise

        # 3. Transcribe using extracted audio
        transcript = self.transcriber.transcribe(audio_path, language="id")
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
            
        # 6. Extract Clips (Horizontal first)
        clip_paths = self.editor.extract_clips(video_path, clips, output_dir)
        print(f"Extracted {len(clip_paths)} clips.")
        
        # 7. Vertical Crop with Smart Seat Tracking
        final_vertical_clips = []
        if clip_paths and self.detector and hasattr(self.detector, 'detect_per_frame'):
            print("Running face detection for smart cropping...")
            detections = self.detector.detect_per_frame(video_path)
            
            # Use KMeans logic to smooth and find seats (Requires fps)
            from src.adapters.face_detectors.strategies.smart_seat_crop import SmartSeatCropStrategy
            import cv2
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            cap.release()
            
            strategy = SmartSeatCropStrategy(min_shot_duration=2.0, smoothing_window=45)
            speaker_positions = strategy.calculate_camera_positions(detections, fps)
            
            for path in clip_paths:
                base, ext = os.path.splitext(path)
                vertical_path = f"{base}_vertical{ext}"
                try:
                    self.editor.crop_to_vertical(path, vertical_path, speaker_positions)
                    final_vertical_clips.append(vertical_path)
                except Exception as e:
                    print(f"Smart crop failed for {path}: {e}")
                    final_vertical_clips.append(path) # Fallback to original
        else:
            final_vertical_clips = clip_paths

        # 7.5 Generate and Burn Subtitles
        if self.subtitle_generator and final_vertical_clips:
            print("Generating and burning subtitles...")
            subtitled_clips = []
            for i, path in enumerate(final_vertical_clips):
                try:
                    clip_domain = clips[i]
                    ass_path = path.replace('.mp4', '.ass')
                    sub_out_path = path.replace('.mp4', '_sub.mp4')
                    created_ass = self.subtitle_generator.generate(transcript.segments, clip_domain.segments, ass_path)
                    if os.path.exists(ass_path) and created_ass:
                        self.editor.burn_subtitles(path, ass_path, sub_out_path)
                        subtitled_clips.append(sub_out_path)
                    else:
                        subtitled_clips.append(path)
                except Exception as e:
                    print(f"Failed to burn subtitle for {path}: {e}")
                    subtitled_clips.append(path)
            final_vertical_clips = subtitled_clips
        
        # 8. Notify
        if self.notifier:
            self.notifier.send_message(f"Processed {len(final_vertical_clips)} clips from {url}")
            for path in final_vertical_clips:
                self.notifier.send_file(path)
                
        return final_vertical_clips

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
        PADDING_DURATION = 2.0
        
        for sugg in suggestions:
            # Reconstruct the explicit final sequence exactly
            raw_segment_ids = sugg.segment_ids
            if not raw_segment_ids:
                continue

            valid_segments = []
            for seg_id in raw_segment_ids:
                if seg_id in segment_map:
                    seg = segment_map[seg_id]
                    valid_segments.append({
                        'id': seg_id,
                        'start': seg.start,
                        'end': seg.end
                    })
                    
            if not valid_segments:
                continue

            merged_blocks = []
            current_block = {
                'start': valid_segments[0]['start'],
                'end': valid_segments[0]['end'],
                'last_id': valid_segments[0]['id']
            }

            for i in range(1, len(valid_segments)):
                seg = valid_segments[i]
                prev_id = current_block['last_id']
                
                # Check consecutive segment ids
                if seg['id'] == prev_id + 1:
                    current_block['end'] = seg['end']
                    current_block['last_id'] = seg['id']
                else:
                    merged_blocks.append(current_block)
                    current_block = {
                        'start': seg['start'],
                        'end': seg['end'],
                        'last_id': seg['id']
                    }
                    
            merged_blocks.append(current_block)
            
            time_ranges = []
            for i in range(len(merged_blocks)):
                block = merged_blocks[i]
                
                if i < len(merged_blocks) - 1:
                    next_block = merged_blocks[i+1]
                    gap = next_block['start'] - block['end']
                    
                    if gap > PADDING_DURATION:
                        block['end'] += PADDING_DURATION
                
                time_ranges.append(TimeRange(block['start'], block['end']))

            resolved_clips.append(Clip(
                title=sugg.title,
                description=sugg.reasoning,
                segments=time_ranges,
                viral_score=sugg.viral_score
            ))
            
        return resolved_clips
