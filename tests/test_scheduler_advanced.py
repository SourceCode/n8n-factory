import unittest
from unittest.mock import MagicMock, patch, ANY
import time
import json
from typing import Any
from n8n_factory.queue_manager import QueueManager
from n8n_factory.scheduler import Scheduler

class TestQueueManagerAdvanced(unittest.TestCase):
    def setUp(self):
        self.mock_op = MagicMock()
        self.queue = QueueManager(operator=self.mock_op)

    def test_enqueue_delayed(self):
        self.queue.enqueue("wf1", delay=5000)
        # Check ZADD called
        self.mock_op.inspect_redis.assert_called()
        args = self.mock_op.inspect_redis.call_args[0][0]
        self.assertEqual(args[0], "ZADD")
        self.assertEqual(args[1], "n8n_factory:job_queue:delayed")
        # Timestamp should be in future
        self.assertTrue(float(args[2]) > time.time() * 1000)

    def test_dequeue_priority(self):
        # Scenario: ZRANGEBYSCORE returns a job
        job_json = json.dumps({"workflow": "delayed_wf"})
        self.mock_op.inspect_redis.side_effect = [
            job_json, # ZRANGEBYSCORE result
            "1"       # ZREM result
        ]
        
        job = self.queue.dequeue()
        self.assertEqual(job["workflow"], "delayed_wf")
        # Verify calls
        calls = self.mock_op.inspect_redis.call_args_list
        self.assertEqual(calls[0][0][0][0], "ZRANGEBYSCORE")
        self.assertEqual(calls[1][0][0][0], "ZREM")

    def test_dequeue_fallback(self):
        # Scenario: ZRANGEBYSCORE returns empty, RPOP returns job
        self.mock_op.inspect_redis.side_effect = [
            "",       # ZRANGEBYSCORE result (empty)
            json.dumps({"workflow": "regular_wf"}) # RPOP result
        ]
        
        job = self.queue.dequeue()
        self.assertEqual(job["workflow"], "regular_wf")
        
    def test_cursor_operations(self):
        self.queue.set_cursor("run1", "step", 5)
        self.mock_op.inspect_redis.assert_called_with(["HSET", "n8n_factory:cursors:run1", "step", "5"])
        
        self.queue.get_cursor("run1", "step")
        self.mock_op.inspect_redis.assert_called_with(["HGET", "n8n_factory:cursors:run1", "step"])
        
        self.queue.reset_cursors("run1")
        self.mock_op.inspect_redis.assert_called_with(["DEL", "n8n_factory:cursors:run1"])

class TestSchedulerAdvanced(unittest.TestCase):
    @patch('n8n_factory.scheduler.SystemOperator')
    @patch('n8n_factory.scheduler.QueueManager')
    def test_retry_logic(self, MockQueue, MockOp):
        mock_op = MockOp.return_value
        mock_queue = MockQueue.return_value
        
        scheduler = Scheduler()
        scheduler.operator = mock_op
        scheduler.queue = mock_queue
        
        # Scenario: Execute fails
        mock_op.execute_workflow.side_effect = RuntimeError("Execution failed")
        
        job = {"workflow": "wf_fail", "retries": 0}
        scheduler._execute_job(job)
        
        # Assert requeue called with delay
        mock_queue.requeue.assert_called_with(job, delay=2000)
        self.assertEqual(job["retries"], 1)

    @patch('n8n_factory.scheduler.SystemOperator')
    @patch('n8n_factory.scheduler.QueueManager')
    def test_max_retries(self, MockQueue, MockOp):
        mock_op = MockOp.return_value
        mock_queue = MockQueue.return_value
        
        scheduler = Scheduler()
        scheduler.operator = mock_op
        scheduler.queue = mock_queue
        
        mock_op.execute_workflow.side_effect = RuntimeError("Fail")
        
        job = {"workflow": "wf_fail", "retries": 5}
        scheduler._execute_job(job)
        
        # Assert NOT requeued (max retries)
        mock_queue.requeue.assert_not_called()

if __name__ == '__main__':
    unittest.main()
