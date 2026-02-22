import subprocess
import os
import shutil
from typing import List
from src.ports.interfaces import VideoEditorPort
from src.domain.entities import Clip

class FFmpegAdapter(VideoEditorPort):
    def __init__(self, use_gpu: bool = True):
        self.use_gpu = use_gpu and self._check_gpu()
        self.settings = self._get_encoding_settings()

    def _check_gpu(self) -> bool:
        if shutil.which("nvidia-smi") is None:
            return False
        try:
            subprocess.check_call(["nvidia-smi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False

    def _get_encoding_settings(self):
        if self.use_gpu:
            print("[FFmpeg] Encoder: GPU (NVENC)")
            return {
                'input_flags': ["-hwaccel", "cuda"],
                'video_codec': "h264_nvenc",
                'quality_flags': ["-cq", "23"],
                'preset': ["-preset", "p5"]
            }
        else:
            print("[FFmpeg] Encoder: CPU (libx264)")
            return {
                'input_flags': [],
                'video_codec': "libx264",
                'quality_flags': ["-crf", "23"],
                'preset': ["-preset", "fast"]
            }

    def extract_clips(self, video_path: str, clips: List[Clip], output_dir: str) -> List[str]:
        output_files = []
        os.makedirs(output_dir, exist_ok=True)
        
        for idx, clip in enumerate(clips):
            safe_title = "".join([c if c.isalnum() else "_" for c in clip.title])
            output_filename = os.path.join(output_dir, f"{safe_title}.mp4")
            
            filter_complex = ""
            inputs = ""
            
            for i, seg in enumerate(clip.segments):
                filter_complex += f"[0:v]trim=start={seg.start}:end={seg.end},setpts=PTS-STARTPTS[v{i}];"
                filter_complex += f"[0:a]atrim=start={seg.start}:end={seg.end},asetpts=PTS-STARTPTS[a{i}];"
                inputs += f"[v{i}][a{i}]"
            
            filter_complex += f"{inputs}concat=n={len(clip.segments)}:v=1:a=1[outv][outa]"
            
            cmd = ["ffmpeg", "-y"]
            cmd.extend(self.settings['input_flags'])
            cmd.extend(["-i", video_path])
            cmd.extend(["-filter_complex", filter_complex])
            cmd.extend(["-map", "[outv]", "-map", "[outa]"])
            cmd.extend(["-c:v", self.settings['video_codec']])
            cmd.extend(self.settings['quality_flags'])
            cmd.extend(self.settings['preset'])
            cmd.extend(["-c:a", "aac"])
            cmd.extend(["-pix_fmt", "yuv420p"])
            cmd.append(output_filename)
            
            print(f"[FFmpeg] Processing clip: {clip.title}")
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                output_files.append(output_filename)
            except subprocess.CalledProcessError as e:
                print(f"[FFmpeg] Error: {e.stderr.decode()}")
                
        return output_files

    def crop_to_vertical(self, video_path: str, output_path: str, speaker_positions: List[int] = None) -> str:
        if not speaker_positions:
            print("[FFmpeg] No speaker_positions provided. Performing simple center crop.")
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", "crop=ih*(9/16):ih",
                "-c:a", "copy",
                output_path
            ]
            subprocess.run(cmd, check=True)
            return output_path

        from moviepy.editor import VideoFileClip
        print(f"[SmartCrop] Processing {video_path}...")
        
        clip = VideoFileClip(video_path)
        w, h = clip.size
        # Target 9:16
        new_w = int(h * (9/16))
        new_h = h
        if new_w % 2 != 0: new_w -= 1
        
        # Determine the x crop parameters given the time t
        def get_crop_params(t):
            frame_index = int(t * clip.fps)
            frame_index = min(frame_index, len(speaker_positions) - 1)
            
            current_center_x = speaker_positions[frame_index]
            
            x1 = int(current_center_x - (new_w / 2))
            
            if x1 < 0: x1 = 0
            if x1 + new_w > w: x1 = w - new_w
            
            return x1, 0, x1 + new_w, new_h

        final_clip = clip.fl(lambda gf, t: gf(t)[0:new_h, get_crop_params(t)[0]:get_crop_params(t)[2]], keep_duration=True)
        
        print("[SmartCrop] Rendering final vertical video...")
        final_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=clip.fps,
            preset="fast",
            ffmpeg_params=['-pix_fmt', 'yuv420p']
        )
        clip.close()
        final_clip.close()
        
        return output_path

    def burn_subtitles(self, video_path: str, subtitle_path: str, output_path: str) -> str:
        safe_subtitle_path = subtitle_path.replace(':', '\\\\:')
        cmd = ["ffmpeg", "-y"]
        cmd.extend(self.settings['input_flags'])
        cmd.extend(["-i", video_path])
        cmd.extend(["-vf", f"subtitles={safe_subtitle_path}"])
        cmd.extend(["-c:v", self.settings['video_codec']])
        cmd.extend(self.settings['quality_flags'])
        cmd.extend(self.settings['preset'])
        cmd.extend(["-c:a", "copy"])
        cmd.extend(["-pix_fmt", "yuv420p"])
        cmd.append(output_path)

        print(f"[FFmpeg] Burning subtitles into {video_path}...")
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"[FFmpeg] Error burning subtitles: {e.stderr.decode()}")
            raise
