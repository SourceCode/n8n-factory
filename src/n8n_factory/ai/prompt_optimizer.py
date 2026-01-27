from typing import Optional
from .ollama_client import OllamaClient
from ..logger import logger

class PromptOptimizer:
    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient()
        self.system_prompt = (
            "You are an expert Prompt Engineer for Large Language Models. "
            "Your goal is to rewrite the user's prompt to be more focused, detailed, "
            "and optimized for high-quality AI responses. "
            "Follow these rules:\n"
            "1. Clarify the objective.\n"
            "2. Add necessary context or constraints.\n"
            "3. Use a structured format if beneficial.\n"
            "4. Eliminate ambiguity.\n"
            "5. Do NOT change the core intent of the user.\n"
            "6. Return ONLY the optimized prompt text. Do not include explanations or preambles."
        )

    def optimize(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Optimizes the given prompt using an LLM.
        """
        logger.debug(f"Optimizing prompt: {prompt[:50]}...")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Optimize this prompt:\n\n{prompt}"}
        ]
        
        try:
            response = self.client.chat(messages, model=model, stream=False)
            if "message" in response and "content" in response["message"]:
                optimized = response["message"]["content"].strip()
                return optimized
            else:
                logger.error(f"Unexpected response format from Ollama: {response}")
                return prompt # Fallback
        except Exception as e:
            logger.error(f"Failed to optimize prompt: {e}")
            raise e
