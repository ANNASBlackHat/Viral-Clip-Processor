import argparse
import sys
import os
from dotenv import load_dotenv
from src.factory import ServiceFactory
from src.application.pipeline import ClipProcessorPipeline
from src.infrastructure.config import load_config

# Load environment variables (API keys)
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Viral Clip Processor CLI")
    parser.add_argument("url", help="YouTube URL to process")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--config", "-c", default="config/default.yaml", help="Path to config file")
    
    args = parser.parse_args()

    # Load Config
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # Initialize Services
    try:
        factory = ServiceFactory(config)
        pipeline = ClipProcessorPipeline(
            downloader=factory.get_downloader(),
            transcriber=factory.get_transcriber(),
            analyzer=factory.get_ai_analyzer(),
            editor=factory.get_video_editor(),
            detector=factory.get_face_detector(),
            notifier=factory.get_notifier(),
            subtitle_generator=factory.get_subtitle_generator()
        )
    except Exception as e:
        print(f"Error initializing services: {e}")
        sys.exit(1)

    # Run Pipeline
    try:
        pipeline.process(args.url, args.output)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nCritical Error during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
