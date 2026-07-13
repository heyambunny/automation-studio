# services/ai_service.py
import requests
from typing import Optional

FAST_MODELS = ["qwen3:latest", "qwen3.5:latest", "gemma4:latest"]
REASONING_MODELS = ["deepseek-r1:8b", "deepseek-r1:14b"]

class AIService:
    """Generates AI summaries using Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3:latest"):
        self.base_url = base_url
        self.model = model
    
    def generate_summary(self, data_text: str, user_context: str = "") -> Optional[str]:
        """Generate AI summary from data with optional user context"""
        if not data_text or data_text.strip() == "":
            return None
        
        if user_context:
            prompt = (
                f"Context: {user_context}\n\n"
                f"Based on the context and data below, generate a professional email body summary "
                f"with key insights and numbers. Use bullet points (3-5 points). "
                f"Include actual numbers from the data.\n\n"
                f"Data:\n{data_text[:3000]}\n\nEmail Summary:"
            )
        else:
            prompt = (
                "You are a business analyst. Generate a concise executive summary from the data below. "
                "Use bullet points (3-5 points). Include key numbers, insights, and actionable items.\n\n"
                f"Data:\n{data_text[:3000]}\n\nExecutive Summary:"
            )
        
        return self._call_ollama(prompt, max_tokens=400, timeout=90)
    
    def generate_subject(self, data_text: str, user_context: str = "") -> Optional[str]:
        """Generate email subject from data with optional user context"""
        if not data_text or data_text.strip() == "":
            return None
        
        if user_context:
            prompt = (
                f"Context: {user_context}\n\n"
                f"Generate a short, professional email subject line (under 12 words) "
                f"based on the context and data. Do NOT start with 'Subject:'. "
                f"Do NOT use quotes.\n\n"
                f"Data:\n{data_text[:1000]}\n\nSubject:"
            )
        else:
            prompt = (
                "Generate a short, professional email subject line (under 12 words) "
                "summarizing this data. Do NOT start with 'Subject:'. Do NOT use quotes.\n\n"
                f"Data:\n{data_text[:1000]}\n\nSubject:"
            )
        
        result = self._call_ollama(prompt, max_tokens=25, timeout=20)
        if result:
            result = result.replace('"', '').replace("'", "").replace("\n", "").replace("Subject:", "").strip()
            if len(result) < 3:
                return None
            return result[:120]
        return None
    
    def generate_from_prompt_only(self, user_prompt: str) -> Optional[str]:
        """Generate email body from user prompt only (no data)"""
        if not user_prompt:
            return None
        
        prompt = (
            f"Generate a professional email body based on this instruction. "
            f"Use bullet points if appropriate. Keep it concise and professional.\n\n"
            f"Instruction: {user_prompt}\n\nEmail Body:"
        )
        
        return self._call_ollama(prompt, max_tokens=350, timeout=60)
    
    def _call_ollama(self, prompt: str, max_tokens: int = 300, timeout: int = 60) -> Optional[str]:
        """Call Ollama API with retry logic"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "max_tokens": max_tokens}
                },
                timeout=timeout
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            return None
        except requests.exceptions.ConnectionError:
            return None
        except requests.exceptions.Timeout:
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt[:1500],
                        "stream": False,
                        "options": {"temperature": 0.3, "max_tokens": 200}
                    },
                    timeout=40
                )
                if response.status_code == 200:
                    return response.json().get("response", "").strip()
            except:
                pass
            return None
        except Exception:
            return None
    
    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False