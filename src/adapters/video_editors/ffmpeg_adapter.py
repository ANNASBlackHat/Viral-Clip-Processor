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
            cmd.append(output_filename)
            
            print(f"[FFmpeg] Processing clip: {clip.title}")
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                output_files.append(output_filename)
            except subprocess.CalledProcessError as e:
                print(f"[FFmpeg] Error: {e.stderr.decode()}")
                
        return output_files

    def crop_to_vertical(self, video_path: str, output_path: str, speaker_positions: List[int] = None) -> str:
        # TODO: Implement the complex crop logic using speaker_positions
        # For now, just a simple center crop
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", "crop=ih*(9/16):ih", 
            "-c:a", "copy",
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path
