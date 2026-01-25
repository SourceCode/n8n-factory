import logging
import re
from rich.logging import RichHandler
from rich.console import Console

console = Console()

class SecretFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        
        # Pattern 1: Key=Value pair
        # Replace "key=value" with "key=***MASKED***"
        # Group 1: Key, Group 2: Value
        msg = re.sub(
            r'(api_key|apikey|token|secret|password|passwd|pwd)\s*[:=]\s*([^\s,]+)', 
            r'\1=***MASKED***', 
            msg, 
            flags=re.IGNORECASE
        )
        
        # Pattern 2: OpenAI style keys (sk-...)
        # Replace the whole key with "sk-***MASKED***"
        # We capture "sk-" and the rest separately or just replace the whole thing.
        msg = re.sub(
            r'sk-[a-zA-Z0-9]{20,}', 
            r'sk-***MASKED***', 
            msg
        )
        
        record.msg = msg
        record.args = () 
        return True

def setup_logger(level="INFO"):
    handler = RichHandler(console=console, rich_tracebacks=True, show_path=False)
    handler.addFilter(SecretFilter())
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler]
    )
    return logging.getLogger("n8n_factory")

logger = setup_logger()
