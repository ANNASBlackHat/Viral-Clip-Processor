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
            print(f"[Telegram] Error sending file {file_path}: {e}")
            return False
