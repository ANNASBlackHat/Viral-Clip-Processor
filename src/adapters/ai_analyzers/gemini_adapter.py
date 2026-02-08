import json
import os
from typing import List
from google import genai
from google.genai import types
from src.ports.interfaces import AIAnalyzerPort
from src.domain.entities import ClipSuggestion

class GeminiAdapter(AIAnalyzerPort):
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp", prompt_file: str = "config/prompts/viral_formula.txt"):
        self.api_key = api_key
        self.model_name = model_name
        self.prompt_template = self._load_prompt(prompt_file)
        self.client = genai.Client(api_key=self.api_key)

    def _load_prompt(self, path: str) -> str:
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: Prompt file {path} not found. Using empty prompt.")
            return ""

    def analyze_for_viral_clips(self, formatted_transcript: str, additional_prompt: str = "") -> List[ClipSuggestion]:
        
        full_prompt = f"{self.prompt_template}\n\n{additional_prompt}\n\n### TRANSCRIPT:\n{formatted_transcript}"
        
        print(f"[Gemini] Sending prompt to {self.model_name}...")
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=full_prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=generate_content_config
            )
            
            return self._parse_json_response(response.text)
            
        except Exception as e:
            print(f"[Gemini] Error: {e}")
            return []

    def _parse_json_response(self, text: str) -> List[ClipSuggestion]:
        try:
            # Clean up markdown code blocks if present (though response_mime_type should handle this)
            text = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            
            if isinstance(data, dict):
                data = [data] # Handle single object response
            
            suggestions = []
            for item in data:
                suggestions.append(ClipSuggestion(
                    title=item.get("title", "Untitled"),
                    viral_score=int(item.get("viral_score", 5)),
                    segment_ids=item.get("segments_ids", []) or item.get("final_clip_sequence", []),
                    reasoning=item.get("reasoning", ""),
                    execution_plan=item.get("execution_plan", {})
                ))
            return suggestions
            
        except json.JSONDecodeError:
            print(f"[Gemini] Failed to parse JSON: {text[:100]}...")
            return []
