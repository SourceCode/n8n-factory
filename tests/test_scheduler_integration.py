import unittest
from unittest.mock import MagicMock, patch, ANY
import json
import os
from n8n_factory.scheduler import Scheduler
from n8n_factory.control_plane import PhaseGate, AutoRefiller

class TestSchedulerIntegration(unittest.TestCase):
    @patch('n8n_factory.scheduler.SystemOperator')
    @patch('n8n_factory.scheduler.QueueManager')
    @patch('n8n_factory.scheduler.AdaptiveBatchSizer')
    @patch('n8n_factory.scheduler.PhaseGate')
    @patch('n8n_factory.scheduler.AutoRefiller')
    def test_job_execution_with_batch_size(self, MockRefiller, MockGate, MockSizer, MockQueue, MockOp):
        mock_op = MockOp.return_value
        mock_sizer = MockSizer.return_value
        mock_gate = MockGate.return_value
        mock_queue = MockQueue.return_value

        scheduler = Scheduler()
        # Override components with mocks
        scheduler.operator = mock_op
        scheduler.sizer = mock_sizer
        scheduler.gate = mock_gate
        scheduler.queue = mock_queue

        # Setup
        mock_sizer.get_batch_size.return_value = 42
        mock_gate.can_run.return_value = True
        mock_op.execute_workflow.return_value = "Success"

        job = {"workflow": "wf1", "mode": "id"}
        scheduler._execute_job(job)

        # Check environment injection
        mock_op.execute_workflow.assert_called()
        call_kwargs = mock_op.execute_workflow.call_args[1]
        env = call_kwargs['env']
        self.assertEqual(env['BATCH_SIZE'], "42")
        self.assertEqual(env['N8N_BATCH_SIZE'], "42")

        # Check stats update
        mock_sizer.update_stats.assert_called_with(ANY, success=True)

    @patch('n8n_factory.scheduler.SystemOperator')
    @patch('n8n_factory.scheduler.QueueManager')
    @patch('n8n_factory.scheduler.AdaptiveBatchSizer')
    @patch('n8n_factory.scheduler.PhaseGate')
    @patch('n8n_factory.scheduler.AutoRefiller')
    def test_phase_gating_blocks_execution(self, MockRefiller, MockGate, MockSizer, MockQueue, MockOp):
        mock_queue = MockQueue.return_value
        mock_gate = MockGate.return_value
        
        scheduler = Scheduler()
        scheduler.queue = mock_queue
        scheduler.gate = mock_gate
        
        # Scenario: Gate says NO
        mock_gate.can_run.return_value = False
        
        job = {"workflow": "wf1", "meta": {"phase": "2", "run_id": "r1"}}
        scheduler._execute_job(job)
        
        # Assertions
        mock_gate.can_run.assert_called_with("r1", "2")
        mock_queue.requeue.assert_called_with(job, delay=10000)

    @patch('n8n_factory.scheduler.SystemOperator')
    @patch('n8n_factory.scheduler.QueueManager')
    @patch('n8n_factory.scheduler.AdaptiveBatchSizer')
    @patch('n8n_factory.scheduler.PhaseGate')
    @patch('n8n_factory.scheduler.AutoRefiller')
    def test_auto_refill_triggers_command(self, MockRefiller, MockGate, MockSizer, MockQueue, MockOp):
        mock_queue = MockQueue.return_value
        mock_refiller = MockRefiller.return_value
        
        scheduler = Scheduler(refill_command="python refill.py", refill_threshold=10)
        scheduler.queue = mock_queue
        scheduler.refiller = mock_refiller
        
        # Scenario: Queue total (5) < Threshold (10)
        mock_queue.size.return_value = 3
        mock_queue.delayed_size.return_value = 2
        
        # Ensure dequeue returns a safe dict so _execute_job doesn't crash on retries comparison
        mock_queue.dequeue.return_value = {"workflow": "wf1", "mode": "id", "retries": 0}
        
        scheduler._tick()
        
        mock_refiller.check_and_refill.assert_called_with(5, 10, "python refill.py")

class TestControlPlaneExtras(unittest.TestCase):
    def test_phase_gate_fallback_file(self):
        mock_op = MagicMock()
        gate = PhaseGate(mock_op)
        
        # 1. Setup Rule
        gate.KEY_RULES = "mock_rules"
        mock_op.inspect_redis.side_effect = [
            json.dumps({"dependency": "p1", "condition": "complete"}), # get_rule
            None # HMGET returns nothing (Redis fail)
        ]
        
        # 2. Setup File Fallback
        # We need to mock os.path.exists and open
        with patch("os.path.exists") as mock_exists, \
             patch("builtins.open", unittest.mock.mock_open(read_data='{"run1": {"p1_current": 100, "p1_total": 100}}')) as mock_file:
            
            mock_exists.return_value = True
            
            # Act
            can_run = gate.can_run("run1", "p2")
            
            # Assert
            self.assertTrue(can_run)
            mock_file.assert_called_with(gate.FALLBACK_CURSOR_FILE, 'r')

if __name__ == '__main__':
    unittest.main()
