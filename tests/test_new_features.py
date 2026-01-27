import unittest
from unittest.mock import MagicMock, patch
import os
import json
from n8n_factory.operator import SystemOperator
from n8n_factory.queue_manager import QueueManager
from n8n_factory.scheduler import Scheduler
from n8n_factory.commands.schedule import schedule_run_command

class TestOperatorFeatures(unittest.TestCase):
    @patch.dict(os.environ, {
        "N8N_CONTAINER_NAME": "custom-n8n",
        "DB_CONTAINER_NAME": "custom-db",
        "REDIS_CONTAINER_NAME": "custom-redis"
    })
    def test_operator_env_config(self):
        op = SystemOperator()
        self.assertEqual(op.n8n_container, "custom-n8n")
        self.assertEqual(op.db_container, "custom-db")
        self.assertEqual(op.redis_container, "custom-redis")

    def test_operator_defaults(self):
        # Ensure we don't have those env vars set in the real environment interfering
        with patch.dict(os.environ, {}, clear=True):
            op = SystemOperator()
            self.assertEqual(op.n8n_container, "n8n")
            self.assertEqual(op.db_container, "postgres")
            self.assertEqual(op.redis_container, "n8n-redis")

    @patch('subprocess.run')
    @patch.dict(os.environ, {"REDIS_PASSWORD": "secret_password"})
    def test_redis_auth(self, mock_run):
        op = SystemOperator(redis_container="my-redis")
        mock_run.return_value.stdout = "OK"
        
        op.inspect_redis("PING")
        
        args = mock_run.call_args[0][0]
        # Expect: docker exec my-redis redis-cli -a secret_password PING
        self.assertIn("-a", args)
        self.assertIn("secret_password", args)
        self.assertIn("PING", args)

    @patch('subprocess.run')
    def test_execute_workflow_broker_port_arg(self, mock_run):
        op = SystemOperator()
        mock_run.return_value.stdout = "Started"
        
        op.execute_workflow(workflow_id="123", broker_port=9999)
        
        args = mock_run.call_args[0][0]
        # Should contain -e N8N_RUNNERS_BROKER_PORT=9999
        self.assertIn("N8N_RUNNERS_BROKER_PORT=9999", " ".join(args))

    @patch('subprocess.run')
    @patch.dict(os.environ, {"N8N_RUNNERS_BROKER_PORT": "8888"})
    def test_execute_workflow_broker_port_env(self, mock_run):
        op = SystemOperator()
        mock_run.return_value.stdout = "Started"
        
        op.execute_workflow(workflow_id="123")
        
        args = mock_run.call_args[0][0]
        self.assertIn("N8N_RUNNERS_BROKER_PORT=8888", " ".join(args))

class TestQueueRequeue(unittest.TestCase):
    def test_requeue(self):
        mock_op = MagicMock()
        queue = QueueManager(operator=mock_op)
        job = {"workflow": "wf1", "mode": "id"}
        
        queue.requeue(job)
        
        # Should call LPUSH
        mock_op.inspect_redis.assert_called_with(["LPUSH", "n8n_factory:job_queue", json.dumps(job)])

class TestSchedulerReliability(unittest.TestCase):
    def setUp(self):
        self.mock_op = MagicMock()
        self.mock_queue = MagicMock()
        self.scheduler = Scheduler(concurrency=1)
        self.scheduler.operator = self.mock_op
        self.scheduler.queue = self.mock_queue

    def test_execute_job_success(self):
        job = {"workflow": "wf1", "mode": "id"}
        self.mock_op.execute_workflow.return_value = "Success: Execution started"
        
        self.scheduler._execute_job(job)
        
        self.mock_op.execute_workflow.assert_called()
        self.mock_queue.requeue.assert_not_called()

    def test_execute_job_exception_requeues(self):
        job = {"workflow": "wf1", "mode": "id"}
        self.mock_op.execute_workflow.side_effect = Exception("Connection error")
        
        self.scheduler._execute_job(job)
        
        self.mock_queue.requeue.assert_called_with(job)

    def test_execute_job_failure_msg_requeues(self):
        job = {"workflow": "wf1", "mode": "id"}
        self.mock_op.execute_workflow.return_value = "Execution failed: something went wrong"
        
        self.scheduler._execute_job(job)
        
        self.mock_queue.requeue.assert_called_with(job)

    def test_execute_job_passes_broker_port(self):
        self.scheduler.broker_port = 7777
        job = {"workflow": "wf1", "mode": "id"}
        self.mock_op.execute_workflow.return_value = "OK"
        
        self.scheduler._execute_job(job)
        
        self.mock_op.execute_workflow.assert_called_with(
            workflow_id="wf1", 
            env={"N8N_PORT": "5679"}, 
            broker_port=7777
        )

class TestCLICommands(unittest.TestCase):
    @patch('n8n_factory.commands.schedule.Scheduler')
    def test_schedule_run_command(self, MockScheduler):
        schedule_run_command(concurrency=10, poll=2, broker_port=6000)
        
        MockScheduler.assert_called_with(concurrency=10, poll_interval=2, broker_port=6000)
        MockScheduler.return_value.start.assert_called_once()

if __name__ == '__main__':
    unittest.main()
