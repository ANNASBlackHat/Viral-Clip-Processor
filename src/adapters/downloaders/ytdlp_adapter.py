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
        import datetime
        import re
        
        print(f"[YtDlp] Extracting info for {url}...")
        
        # Options for extracting info (without downloading)
        info_opts = {
            'quiet': True,
            'skip_download': True,
            'forcetitle': True,
        }
        
        if self.cookies_file and os.path.exists(self.cookies_file):
            info_opts['cookiefile'] = self.cookies_file
            
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=False)
            except Exception as e:
                 raise Exception(f"Failed to extract info: {e}")
            video_title = info_dict.get('title', 'Unknown_Video')
            
            # Sanitize title for filename
            video_title = re.sub(r'[\\/*?:"<>;|=]', '_', video_title)
            video_title = re.sub(r'\s+', ' ', video_title).strip()
            video_title = re.sub(r'[^\w\s\-.]', '', video_title)
            video_title = video_title.replace(' ', '_')

        # Create dynamic directory name
        date_str = datetime.date.today().strftime('%Y-%m-%d')
        dynamic_output_dir = os.path.join(output_dir, f"{date_str}-{video_title}")
        os.makedirs(dynamic_output_dir, exist_ok=True)
        
        print(f"[YtDlp] Downloading to {dynamic_output_dir}...")
        
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(dynamic_output_dir, '%(title)s.%(ext)s'),
            'restrictfilenames': True,
            'trim_filenames': 200,
            'quiet': True,
            'no_warnings': True,
        }
        
        # Add cookies if provided
        if self.cookies_file and os.path.exists(self.cookies_file):
            ydl_opts['cookiefile'] = self.cookies_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print('start downloading...')
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
