import yaml
import os

def load_config(path: str = "config/default.yaml") -> dict:
    if not os.path.exists(path):
        # Return defaults if file missing
        return {
            "transcriber": "whisperx",
            "whisper_model": "large-v3-turbo",
            "use_gpu": True,
            "notification": {
                "telegram": {"enabled": False}
            }
        }
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)
