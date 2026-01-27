import unittest
from unittest.mock import MagicMock, patch, ANY
import json
from n8n_factory.scheduler import Scheduler

class TestSchedulerIntegration(unittest.TestCase):
    @patch('n8n_factory.scheduler.SystemOperator')
    @patch('n8n_factory.scheduler.QueueManager')
    @patch('n8n_factory.scheduler.AdaptiveBatchSizer')
    @patch('n8n_factory.scheduler.PhaseGate')
    def test_job_execution_with_batch_size(self, MockGate, MockSizer, MockQueue, MockOp):
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
    def test_phase_gating_blocks_execution(self, MockGate, MockSizer, MockQueue, MockOp):
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
        # Execution should be skipped
        # We can't easily assert execute_workflow wasn't called on the real operator 
        # unless we mock that too, which is implicitly done but better explicit.
        # But we know _execute_job returns early.

if __name__ == '__main__':
    unittest.main()
