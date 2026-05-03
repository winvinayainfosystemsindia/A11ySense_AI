import os
import logging
import json
from typing import Dict, Any, List
from pathlib import Path

# LLM SDKs (imported safely)
try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.provider = os.getenv("LLM_PROVIDER", "mock").lower()
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        self.skills_dir = Path(__file__).parent.parent / "skills"
        
        # API Keys
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")

    def load_prompt(self, filename: str) -> str:
        prompt_path = self.prompts_dir / filename
        if not prompt_path.exists():
            logger.warning(f"Prompt file {filename} not found, using default.")
            return f"You are a {self.role} agent named {self.name}."
        return prompt_path.read_text(encoding="utf-8")

    def load_skills_docs(self) -> str:
        """Loads all skill documentation to provide to the agent."""
        docs = []
        for md_file in self.skills_dir.glob("*.md"):
            docs.append(f"--- SKILL: {md_file.stem} ---\n{md_file.read_text(encoding='utf-8')}")
        return "\n\n".join(docs)

    async def call_llm(self, prompt: str, system_message: str = "", use_vision: bool = False, image_data: str = None) -> str:
        """Generic LLM call dispatcher with vision support."""
        if self.provider == "claude" and self.anthropic_key and anthropic:
            return await self._call_claude(prompt, system_message, use_vision, image_data)
        elif self.provider == "groq" and self.groq_key and Groq:
            return await self._call_groq(prompt, system_message)
        elif self.provider == "gemini" and self.gemini_key and genai:
            return await self._call_gemini(prompt, system_message, use_vision, image_data)
        
        return "LLM Provider not configured correctly or Mock provider active."

    async def _call_claude(self, prompt: str, system_message: str, use_vision: bool, image_data: str) -> str:
        client = anthropic.Anthropic(api_key=self.anthropic_key)
        
        content = []
        if use_vision and image_data:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data,
                },
            })
        content.append({"type": "text", "text": prompt})
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620" if use_vision else "claude-3-haiku-20240307",
            max_tokens=2048,
            system=system_message,
            messages=[{"role": "user", "content": content}]
        )
        return message.content[0].text

    async def _call_groq(self, prompt: str, system_message: str) -> str:
        client = Groq(api_key=self.groq_key)
        # Enable JSON mode for more reliable formatting
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_message + "\nReturn response in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content

    async def _call_gemini(self, prompt: str, system_message: str, use_vision: bool, image_data: str) -> str:
        genai.configure(api_key=self.gemini_key)
        model_name = 'gemini-1.5-flash' if use_vision else 'gemini-1.5-pro'
        model = genai.GenerativeModel(model_name)
        
        parts = [system_message, prompt]
        if use_vision and image_data:
            parts.append({"mime_type": "image/png", "data": image_data})
            
        response = model.generate_content(parts)
        return response.text

    def parse_json(self, text: str) -> Dict[str, Any]:
        """
        Parses JSON from LLM response with balanced resilience.
        """
        try:
            # 1. Clean markdown code blocks
            text = text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            # 2. Find the JSON boundaries
            start = text.find('{')
            end = text.rfind('}') + 1
            if start == -1 or end == 0:
                logger.error(f"No JSON found in LLM response: {text[:100]}...")
                return {"error": "No JSON found"}

            json_str = text[start:end]

            # 3. Attempt standard parse (handles formatting newlines correctly)
            try:
                return json.loads(json_str, strict=False)
            except json.JSONDecodeError:
                # 4. Fallback: Aggressive cleaning only if standard parse fails
                # Remove actual control characters except allowed whitespace
                cleaned = "".join(ch for ch in json_str if ord(ch) >= 32 or ch in '\n\r\t')
                return json.loads(cleaned, strict=False)
                
        except Exception as e:
            logger.error(f"Ultimate JSON Parse Failure: {str(e)} | Raw snippet: {text[:200]}")
            return {"error": "Critical parsing failure", "raw": text}
