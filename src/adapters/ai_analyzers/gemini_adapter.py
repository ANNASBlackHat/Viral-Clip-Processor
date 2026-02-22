import json
import os
from typing import List
from google import genai
from google.genai import types
from src.ports.interfaces import AIAnalyzerPort
from src.domain.entities import ClipSuggestion
from src.adapters.ai_analyzers.parsers.base import ResponseParser

class GeminiAdapter(AIAnalyzerPort):
    def __init__(
        self, 
        api_key: str, 
        parser: ResponseParser,
        model_name: str = "gemini-flash-latest", 
        prompt_file: str = "config/prompts/viral_formula.txt"
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.parser = parser
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
        
        full_prompt = f"{self.prompt_template}\n"
        if additional_prompt:
            full_prompt += f"\n## Additional Instruction\n{additional_prompt}\n"
            
        full_prompt += f"\n## Context\n{formatted_transcript}"
        
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
            # Clean up markdown code blocks if present
            text = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            
            # Delegate parsing to the injected parser
            return self.parser.parse_response(data)
            
        except json.JSONDecodeError:
            print(f"[Gemini] Failed to parse JSON: {text[:100]}...")
            return []
