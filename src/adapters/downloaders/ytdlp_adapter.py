import yt_dlp
import os
import re
from src.ports.interfaces import DownloaderPort

class YtDlpDownloader(DownloaderPort):
    def download(self, url: str, output_dir: str) -> str:
        print(f"[YtDlp] Downloading {url} to {output_dir}...")
        
        # Options for the download
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'restrictfilenames': True,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # handle the fact that prepare_filename might define ext but merge changes it?
            # actually if merge_output_format is mp4, it should end in mp4
            
            # Sanity check if file exists, sometimes yt-dlp customizes name
            # If merged, it might differ.
            # simpler approach: get the filename from the actual file created?
            # yt-dlp is tricky with filenames.
            
            # Let's try to find the file if prepare_filename is slightly off (e.g. .webm vs .mp4)
            # But with merge_output_format='mp4', it usually forces mp4.
            
            base, _ = os.path.splitext(filename)
            final_path = base + ".mp4"
            
            if os.path.exists(final_path):
                return final_path
            elif os.path.exists(filename):
                return filename
            else:
                # Fallback search in directory?
                raise Exception(f"Downloaded file not found at {filename} or {final_path}")
