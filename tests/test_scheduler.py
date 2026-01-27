import unittest
from unittest.mock import MagicMock, patch
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
        self.mock_op.inspect_redis.assert_called_with(["LPUSH", "n8n_factory:job_queue", '{"workflow": "workflow_1", "mode": "id", "inputs": {}, "timestamp": null}'])

    def test_dequeue(self):
        self.mock_op.inspect_redis.return_value = '{"workflow": "workflow_1"}'
        job = self.queue.dequeue()
        self.assertEqual(job["workflow"], "workflow_1")

    def test_size(self):
        self.mock_op.inspect_redis.return_value = "5"
        self.assertEqual(self.queue.size(), 5)

class TestScheduler(unittest.TestCase):
    @patch('n8n_factory.scheduler.SystemOperator')
    @patch('n8n_factory.scheduler.QueueManager')
    def test_tick_runs_job(self, MockQueue, MockOp):
        # Setup
        mock_op = MockOp.return_value
        mock_queue = MockQueue.return_value
        
        # Scenario: 1 active, conc=5 -> 4 slots. Queue has 1 job.
        mock_op.get_active_executions.return_value = [{"id": "1"}]
        mock_queue.size.return_value = 1
        mock_queue.dequeue.return_value = {"workflow": "wf1", "mode": "id"}
        
        scheduler = Scheduler(concurrency=5)
        scheduler.queue = mock_queue
        scheduler.operator = mock_op
        
        # Act
        scheduler._tick()
        
        # Assert
        mock_op.execute_workflow.assert_called_with(
            workflow_id="wf1",
            env={"N8N_PORT": "5679"},
            broker_port=None
        )
        mock_queue.dequeue.assert_called()

    @patch('n8n_factory.scheduler.SystemOperator')
    @patch('n8n_factory.scheduler.QueueManager')
    def test_tick_full_capacity(self, MockQueue, MockOp):
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