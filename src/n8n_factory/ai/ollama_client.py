import os
import json
import time
import requests
from typing import Dict, Any, List, Optional, Generator
from ..logger import logger

class OllamaClient:
    def __init__(self, model: str = "qwen3:8b", base_url: str = "http://localhost:11434", timeout: int = 120):
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        
        # Check env overrides
        if os.environ.get("OLLAMA_BASE_URL"):
            self.base_url = os.environ["OLLAMA_BASE_URL"]

    def list_models(self) -> List[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
            resp.raise_for_status()
            return resp.json().get("models", [])
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    def chat(self, 
             messages: List[Dict[str, str]], 
             system: Optional[str] = None, 
             stream: bool = False,
             json_mode: bool = False,
             temperature: float = 0.2) -> Dict[str, Any]:
        
        url = f"{self.base_url}/api/chat"
        
        # Prepend system message if provided
        final_messages = []
        if system:
            final_messages.append({"role": "system", "content": system})
        final_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": final_messages,
            "stream": stream,
            "temperature": temperature,
        }
        
        if json_mode:
            payload["format"] = "json"

        try:
            logger.debug(f"Sending request to Ollama ({self.model})...")
            start_time = time.time()
            
            if stream:
                # Streaming implementation omitted for simplicity in this turn, 
                # but infrastructure is here.
                pass 
            
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            
            data = resp.json()
            duration = time.time() - start_time
            
            # Extract content
            content = data.get("message", {}).get("content", "")
            
            return {
                "content": content,
                "raw": data,
                "duration": duration
            }

        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            raise TimeoutError(f"Ollama request timed out")
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            raise e