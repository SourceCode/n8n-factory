import unittest
from unittest.mock import MagicMock, patch
from n8n_factory.ai.prompt_optimizer import PromptOptimizer

class TestPromptOptimizer(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.optimizer = PromptOptimizer(client=self.mock_client)

    def test_optimize_success(self):
        # Setup mock response
        self.mock_client.chat.return_value = {
            "message": {
                "content": "Optimized prompt content"
            }
        }

        # Call optimize
        original_prompt = "bad prompt"
        result = self.optimizer.optimize(original_prompt)

        # Assertions
        self.assertEqual(result, "Optimized prompt content")
        self.mock_client.chat.assert_called_once()
        
        # Check call args
        args, kwargs = self.mock_client.chat.call_args
        messages = args[0]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn(original_prompt, messages[1]["content"])

    def test_optimize_api_failure(self):
        # Setup mock to raise exception
        self.mock_client.chat.side_effect = Exception("API Error")

        # Call optimize
        original_prompt = "bad prompt"
        # Should catch exception and return original prompt? 
        # Wait, the implementation raises the exception after logging.
        # Let's check the implementation:
        # except Exception as e:
        #     logger.error(f"Failed to optimize prompt: {e}")
        #     raise e
        
        with self.assertRaises(Exception):
            self.optimizer.optimize(original_prompt)

    def test_optimize_unexpected_format(self):
        # Setup mock with bad format
        self.mock_client.chat.return_value = {}

        # Call optimize
        original_prompt = "bad prompt"
        result = self.optimizer.optimize(original_prompt)

        # Should return original prompt
        self.assertEqual(result, original_prompt)

if __name__ == '__main__':
    unittest.main()
