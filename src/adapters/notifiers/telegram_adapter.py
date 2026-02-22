import requests
from src.ports.interfaces import NotifierPort

class TelegramNotifier(NotifierPort):
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str) -> bool:
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        try:
            resp = requests.post(url, data=payload, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"[Telegram] Error sending message: {e}")
            return False

    def send_file(self, file_path: str) -> bool:
        url = f"{self.base_url}/sendDocument"
        import os
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, 'rb') as f:
                resp = requests.post(
                    url,
                    data={'chat_id': self.chat_id},
                    files={'document': f},
                    timeout=60
                )
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"[Telegram] Error sending file directly {file_name}: {e}. Trying GoFile fallback...")
            return self._handle_gofile_fallback(file_path, file_name)

    def _upload_to_gofile(self, file_path: str) -> str:
        """Uploads a file to GoFile and returns the download link."""
        url = "https://upload.gofile.io/uploadfile"
        with open(file_path, 'rb') as f:
            response = requests.post(url, files={'file': f}, timeout=120)
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "ok":
            return data["data"]["downloadPage"]
        raise Exception(f"GoFile error: {data.get('status')}")

    def _handle_gofile_fallback(self, file_path: str, file_name: str) -> bool:
        try:
            link = self._upload_to_gofile(file_path)
            msg = f"📂 *File:* `{file_name}`\n⚠️ Size limit exceeded.\n🔗 [Download from GoFile]({link})"
            return self.send_message(msg)
        except Exception as e:
            print(f"[Telegram] Critical: Failed to upload {file_name} to both services. Error: {e}")
            return False
