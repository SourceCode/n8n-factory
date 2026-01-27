import unittest
from unittest.mock import MagicMock, patch, ANY
import json
import n8n_factory.scheduler
print(f"DEBUG: Loaded scheduler from {n8n_factory.scheduler.__file__}")

from n8n_factory.queue_manager import QueueManager
from n8n_factory.scheduler import Scheduler

class TestQueueManager(unittest.TestCase):
    def setUp(self):
        self.mock_op = MagicMock()
        self.queue = QueueManager(operator=self.mock_op)

    def test_enqueue(self):
        self.mock_op.inspect_redis.return_value = "1"
        self.queue.enqueue("workflow_1")
        # Check that LPUSH is called. inspecting the exact JSON string is brittle due to timestamp
        # So we verify the call structure and key payload attributes
        self.mock_op.inspect_redis.assert_called()
        args = self.mock_op.inspect_redis.call_args[0][0]
        self.assertEqual(args[0], "LPUSH")
        self.assertEqual(args[1], "n8n_factory:job_queue")
        
        payload = json.loads(args[2])
        self.assertEqual(payload["workflow"], "workflow_1")
        self.assertEqual(payload["mode"], "id")
        self.assertEqual(payload["retries"], 0)
        self.assertIn("meta", payload)
        self.assertIn("timestamp", payload)

    def test_dequeue(self):
        # Sequence: 
        # 1. ZRANGEBYSCORE (check delayed) -> return empty
        # 2. RPOP (check regular) -> return job
        self.mock_op.inspect_redis.side_effect = [
            "", 
            '{"workflow": "workflow_1"}'
        ]
        job = self.queue.dequeue()
        self.assertEqual(job["workflow"], "workflow_1")

    def test_size(self):
        self.mock_op.inspect_redis.return_value = "5"
        self.assertEqual(self.queue.size(), 5)

class TestScheduler(unittest.TestCase):
    @patch('n8n_factory.scheduler.SystemOperator')
    @patch('n8n_factory.scheduler.QueueManager')
    @patch('n8n_factory.scheduler.AdaptiveBatchSizer') # Mock Sizer
    @patch('n8n_factory.scheduler.PhaseGate') # Mock Gate
    def test_tick_runs_job(self, MockGate, MockSizer, MockQueue, MockOp):
        # Setup
        mock_op = MockOp.return_value
        mock_queue = MockQueue.return_value
        mock_sizer = MockSizer.return_value
        mock_gate = MockGate.return_value
        
        # Scenario: 1 active, conc=5 -> 4 slots. Queue has 1 job.
        mock_op.get_active_executions.return_value = [{"id": "1"}]
        mock_queue.size.return_value = 1
        mock_queue.delayed_size.return_value = 0
        mock_queue.dequeue.return_value = {"workflow": "wf1", "mode": "id"}
        mock_sizer.get_batch_size.return_value = 10
        mock_gate.can_run.return_value = True
        
        scheduler = Scheduler(concurrency=5)
        # Manually attach mocks if not injected by init (init creates new instances)
        # But we patched the classes, so init uses mocks.
        # We need to grab the instances created inside init?
        # The patches mock the CLASS, so Scheduler() calls MockQueue() -> returns a mock instance.
        # The mock_queue above is the RETURN VALUE of the class mock, which is what we want.
        
        # However, we need to ensure the Scheduler instance uses *our* configured mocks
        # Since we patched the classes, Scheduler init will instantiate new mocks.
        # simpler: assign our configured mocks to the scheduler instance.
        scheduler.queue = mock_queue
        scheduler.operator = mock_op
        scheduler.sizer = mock_sizer
        scheduler.gate = mock_gate
        
        # Act
        scheduler._tick()
        
        # Assert
        # Check env contains BATCH_SIZE
        mock_op.execute_workflow.assert_called()
        call_kwargs = mock_op.execute_workflow.call_args[1]
        self.assertEqual(call_kwargs['workflow_id'], "wf1")
        self.assertIn("BATCH_SIZE", call_kwargs['env'])
        self.assertEqual(call_kwargs['env']['BATCH_SIZE'], "10")
        
        mock_queue.dequeue.assert_called()

    @patch('n8n_factory.scheduler.SystemOperator')
    @patch('n8n_factory.scheduler.QueueManager')
    @patch('n8n_factory.scheduler.AdaptiveBatchSizer')
    @patch('n8n_factory.scheduler.PhaseGate')
    def test_tick_full_capacity(self, MockGate, MockSizer, MockQueue, MockOp):
        # Setup: 5 active, conc=5 -> 0 slots.
        mock_op = MockOp.return_value
        mock_queue = MockQueue.return_value
        
        mock_op.get_active_executions.return_value = [{"id": i} for i in range(5)]
        
        scheduler = Scheduler(concurrency=5)
        scheduler.queue = mock_queue
        scheduler.operator = mock_op
        
        # Act
        scheduler._tick()
        
        # Assert
        mock_queue.dequeue.assert_not_called()

if __name__ == '__main__':
    unittest.main()