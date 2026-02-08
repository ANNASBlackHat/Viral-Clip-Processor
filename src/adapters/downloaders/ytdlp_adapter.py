import yt_dlp
import os
from src.ports.interfaces import DownloaderPort

class YtDlpDownloader(DownloaderPort):
    def __init__(self, cookies_file: str = None):
        """
        Initialize the downloader.
        
        Args:
            cookies_file: Optional path to a Netscape-format cookies file.
                          Export from browser using extensions like "Get cookies.txt"
        """
        self.cookies_file = cookies_file

    def download(self, url: str, output_dir: str) -> str:
        print(f"[YtDlp] Downloading {url} to {output_dir}...")
        
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'restrictfilenames': True,
            'quiet': True,
            'no_warnings': True,
        }
        
        # Add cookies if provided
        if self.cookies_file and os.path.exists(self.cookies_file):
            print(f"[YtDlp] Using cookies from: {self.cookies_file}")
            ydl_opts['cookiefile'] = self.cookies_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            base, _ = os.path.splitext(filename)
            final_path = base + ".mp4"
            
            if os.path.exists(final_path):
                return final_path
            elif os.path.exists(filename):
                return filename
            else:
                raise Exception(f"Downloaded file not found at {filename} or {final_path}")
