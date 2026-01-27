import os
import json
import requests
from typing import Optional, Dict, Any, List, Union, Generator
from dotenv import load_dotenv
from ..logger import logger

# Load environment variables
load_dotenv()

class OllamaClient:
    """
    A client for interacting with a local or remote Ollama instance.
    
    Default Configuration:
    - Model: Qwen3:8b
    - Context Window: 32768
    - Temperature: 0.6
    - Top P: 0.95
    - Top K: 20
    - Min P: 0
    - Presence Penalty: 1.5
    - Enable Thinking: True
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: The base URL of the Ollama API. Defaults to OLLAMA_BASE_URL env or http://localhost:11434.
            api_key: The API key (if required). Defaults to OLLAMA_API_KEY env.
            model: The default model to use. Defaults to OLLAMA_MODEL env or Qwen3:8b.
        """
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip('/')
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY")
        self.model = model or os.getenv("OLLAMA_MODEL", "Qwen3:8b")
        
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        # Optimal settings for Qwen3:8b as per requirements
        self.default_options = {
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "min_p": 0.0,
            "num_ctx": 32768,
            "num_predict": -1,
            "presence_penalty": 1.5,
            # enable_thinking is handled in the request payload if supported by the backend
        }
        # Some custom backends or forks use enable_thinking in options
        self.enable_thinking = True

    def _get_options(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Merge default options with overrides."""
        opts = self.default_options.copy()
        if overrides:
            opts.update(overrides)
        
        # Ensure enable_thinking is present if it's treated as an option
        if self.enable_thinking and "enable_thinking" not in opts:
             opts["enable_thinking"] = True
             
        return opts

    def chat(self, 
             messages: List[Dict[str, str]], 
             model: Optional[str] = None, 
             options: Optional[Dict[str, Any]] = None, 
             stream: bool = False) -> Union[Dict[str, Any], requests.Response]:
        """
        Send a chat request to Ollama.
        
        Args:
            messages: List of message dictionaries (role, content).
            model: Model name to use.
            options: Model parameters (temperature, etc.).
            stream: Whether to stream the response.
            
        Returns:
            JSON response dict or Response object if streaming.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model or self.model,
            "messages": messages,
            "options": self._get_options(options),
            "stream": stream
        }

        try:
            logger.debug(f"Sending chat request to {url} with model {payload['model']}")
            response = requests.post(url, headers=self.headers, json=payload, stream=stream)
            response.raise_for_status()
            
            if stream:
                return response
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama Chat API error: {e}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def generate(self, 
                 prompt: str, 
                 model: Optional[str] = None, 
                 options: Optional[Dict[str, Any]] = None, 
                 stream: bool = False,
                 system: Optional[str] = None) -> Union[Dict[str, Any], requests.Response]:
        """
        Send a generate request to Ollama.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "options": self._get_options(options),
            "stream": stream
        }
        if system:
            payload["system"] = system

        try:
            logger.debug(f"Sending generate request to {url} with model {payload['model']}")
            response = requests.post(url, headers=self.headers, json=payload, stream=stream)
            response.raise_for_status()
            
            if stream:
                return response
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama Generate API error: {e}")
            raise

    def list_models(self) -> Dict[str, Any]:
        """List available models locally."""
        url = f"{self.base_url}/api/tags"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama List Models error: {e}")
            raise

    def pull_model(self, model: str, stream: bool = False) -> Union[Dict[str, Any], requests.Response]:
        """Pull a model."""
        url = f"{self.base_url}/api/pull"
        payload = {"name": model, "stream": stream}
        try:
            response = requests.post(url, headers=self.headers, json=payload, stream=stream)
            response.raise_for_status()
            if stream:
                return response
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama Pull Model error: {e}")
            raise
