import unittest
from unittest.mock import MagicMock, patch
from n8n_factory.commands.ops import ops_monitor_command, _list_active_executions, _watch_execution

class TestOpsMonitor(unittest.TestCase):
    
    @patch('n8n_factory.commands.ops.operator')
    @patch('n8n_factory.commands.ops.console')
    def test_list_active_executions(self, mock_console, mock_operator):
        # Setup mock return
        mock_operator.get_active_executions.return_value = [
            {"id": "1", "name": "Test Workflow", "status": "running", "startedAt": "2023-01-01", "mode": "manual"}
        ]
        
        # Call function
        _list_active_executions(json_output=False)
        
        # Verify
        mock_operator.get_active_executions.assert_called_once()
        mock_console.print.assert_called()

    @patch('n8n_factory.commands.ops.operator')
    @patch('n8n_factory.commands.ops.console')
    def test_list_active_executions_empty(self, mock_console, mock_operator):
        mock_operator.get_active_executions.return_value = []
        _list_active_executions(json_output=False)
        mock_console.print.assert_called_with("[yellow]No active executions found.[/yellow]")

    @patch('n8n_factory.commands.ops.operator')
    @patch('n8n_factory.commands.ops.console')
    def test_watch_execution_success(self, mock_console, mock_operator):
        # Mock execution details
        mock_operator.get_execution_details.side_effect = [
            {"id": "1", "status": "running", "name": "WF1", "data": "{}"},
            {"id": "1", "status": "success", "name": "WF1", "data": "{}"}
        ]
        
        # Need to mock Live context manager
        mock_live = MagicMock()
        mock_console.status.return_value.__enter__.return_value = mock_live
        
        # Since _watch_execution has a loop and uses Live, it's tricky to test the loop fully without blocking.
        # But we can test that it calls get_execution_details.
        # We will patch time.sleep to raise an exception to break the loop or use side_effect on operator to eventually return completed status.
        
        with patch('time.sleep'):
             _watch_execution("1", json_output=False)
        
        # Assertions
        self.assertEqual(mock_operator.get_execution_details.call_count, 2)

if __name__ == '__main__':
    unittest.main()
