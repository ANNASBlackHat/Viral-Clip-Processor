import unittest
from unittest.mock import MagicMock
from src.application.pipeline import ClipProcessorPipeline
from src.domain.entities import TranscriptionResult, Segment, ClipSuggestion, Clip

class TestClipProcessorPipeline(unittest.TestCase):
    def setUp(self):
        self.mock_downloader = MagicMock()
        self.mock_transcriber = MagicMock()
        self.mock_analyzer = MagicMock()
        self.mock_editor = MagicMock()
        self.mock_detector = MagicMock()
        self.mock_notifier = MagicMock()
        
        self.pipeline = ClipProcessorPipeline(
            downloader=self.mock_downloader,
            transcriber=self.mock_transcriber,
            analyzer=self.mock_analyzer,
            editor=self.mock_editor,
            detector=self.mock_detector,
            notifier=self.mock_notifier
        )

    def test_pipeline_flow(self):
        # Setup Mocks
        self.mock_downloader.download.return_value = "dummy_video.mp4"
        
        self.mock_transcriber.transcribe.return_value = TranscriptionResult(
            language="en",
            duration=100.0,
            segments=[
                Segment(id=1, text="Hello world", start=0.0, end=5.0, words=[]),
                Segment(id=2, text="This is a test", start=5.0, end=10.0, words=[])
            ]
        )
        
        self.mock_analyzer.analyze_for_viral_clips.return_value = [
            ClipSuggestion(
                title="Viral Moment",
                viral_score=10,
                segment_ids=[1, 2],
                reasoning="It's cool",
                execution_plan={}
            )
        ]
        
        self.mock_editor.extract_clips.return_value = ["output/clip_0.mp4"]
        
        # Run Pipeline
        url = "http://youtube.com/watch?v=123"
        output_dir = "test_output"
        result = self.pipeline.process(url, output_dir)
        
        # Assertions
        self.mock_downloader.download.assert_called_once_with(url, output_dir)
        self.mock_transcriber.transcribe.assert_called_once_with("dummy_video.mp4")
        self.mock_analyzer.analyze_for_viral_clips.assert_called_once()
        self.mock_editor.extract_clips.assert_called_once()
        self.mock_notifier.send_message.assert_called_once()
        
        # Check if clips were resolved correctly (IDs -> Timestamps)
        # Extract the args passed to extract_clips
        args, _ = self.mock_editor.extract_clips.call_args
        passed_clips = args[1] # second arg is clips list
        
        self.assertEqual(len(passed_clips), 1)
        self.assertEqual(passed_clips[0].title, "Viral Moment")
        self.assertEqual(len(passed_clips[0].segments), 1) 
        # Logic merged consecutive segments 0-5 and 5-10 into 0-10
        self.assertEqual(passed_clips[0].segments[0].start, 0.0)
        self.assertEqual(passed_clips[0].segments[0].end, 10.0)
        
        print("Pipeline Integration Test Passed!")

if __name__ == "__main__":
    unittest.main()
