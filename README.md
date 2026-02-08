# Viral Clip Processor

An AI-powered automated video clipper that extracts viral moments from YouTube videos.
Refactored from a Jupyter Notebook into a clean, modular Python application using **Hexagonal Architecture**.

## Features

- **Multi-Engine Transcription**: Support for `whisperx` (fast, aligned) and `openai-whisper` (robust).
- **AI Analysis**: Uses Gemini (via Google GenAI) to identify viral hooks and structure clips.
- **Smart Cropping**: Intelligent vertical cropping using YOLO face detection and "Smart Seat" clustering.
- **GPU Acceleration**: Auto-detects NVIDIA GPUs for NVENC encoding and CUDA inference.
- **Configurable**: Fully controlled via `config.yaml`.

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `whisperx` and `torch` may require specific installation commands based on your CUDA version.*

3. Setup Environment Variables:
   Create a `.env` file:
   ```env
   GEMINI_API_KEY=your_key_here
   TELEGRAM_TOKEN=opt_token
   TELEGRAM_CHAT_ID=opt_chat_id
   ```

## Usage

### CLI
Run the processor on a YouTube URL:

```bash
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --output my_clips
```

### Configuration
Edit `config/default.yaml` to change settings:

```yaml
transcriber: whisperx          # or openai_whisper
whisper_model: large-v3-turbo
use_gpu: true
ai_analyzer: gemini
notification:
  telegram:
    enabled: true
```

## Architecture

This project follows **Hexagonal Architecture (Ports & Adapters)**:

- **Domain**: Pure business logic (`src/domain`).
- **Ports**: Interfaces identifying external dependencies (`src/ports`).
- **Adapters**: Concrete implementations (`src/adapters`) for:
  - Transcription (WhisperX, OpenAI)
  - Video Editing (FFmpeg)
  - AI (Gemini)
  - Notification (Telegram)
- **Application**: Orchestration logic (`src/application`).

## Project Structure

```
├── src/
│   ├── domain/       # Entities
│   ├── ports/        # Interfaces
│   ├── adapters/     # Implementations (Whisper, FFmpeg, Gemini...)
│   ├── application/  # Pipeline logic
│   └── factory.py    # Dependency Injection
├── config/           # Config & Prompts
├── main.py           # Entry point
└── tests/            # Unit & Integration tests
```
