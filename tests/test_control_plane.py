import unittest
from unittest.mock import MagicMock, patch, ANY
import json
from n8n_factory.control_plane import AdaptiveBatchSizer, PhaseGate

class TestAdaptiveBatchSizer(unittest.TestCase):
    def setUp(self):
        self.mock_op = MagicMock()
        self.sizer = AdaptiveBatchSizer(self.mock_op, default_size=10)

    def test_initialization_ensures_config(self):
        # Verify SET commands for config and current size
        self.mock_op.inspect_redis.assert_any_call(["SET", self.sizer.KEY_CONFIG, ANY, "NX"])
        self.mock_op.inspect_redis.assert_any_call(["SET", self.sizer.KEY_CURRENT, "10", "NX"])

    def test_get_batch_size(self):
        self.mock_op.inspect_redis.return_value = "25"
        self.assertEqual(self.sizer.get_batch_size(), 25)

        self.mock_op.inspect_redis.return_value = "invalid"
        self.assertEqual(self.sizer.get_batch_size(), 10) # Default

    @patch('time.time')
    def test_update_stats_increases_size(self, mock_time):
        mock_time.return_value = 100.0 # 100 % 5 = 0 < 0.5
        
        # Setup config
        config = {
            "min_size": 1, "max_size": 100, "target_latency_ms": 5000,
            "failure_threshold_rate": 0.1, "adjustment_factor": 2.0, "window_size": 2
        }
        self.mock_op.inspect_redis.side_effect = [
            None, # LPUSH
            None, # LTRIM
            # _recalculate calls
            # LRANGE returns 2 fast successes
            json.dumps({"d": 500, "s": 1}) + "\n" + json.dumps({"d": 600, "s": 1}),
            json.dumps(config), # get_config
            "10", # get_batch_size (current)
            None  # SET new size
        ]

        # Note: Order of calls inside implementation matters for side_effect.
        # Impl: LPUSH, LTRIM, Check time, LRANGE, get_config (inside _recal), get_batch_size, SET
        # Wait, get_config is called in update_stats BEFORE LPUSH too to get window size.
        # Let's check implementation again.
        # update_stats: get_config(), LPUSH, LTRIM, check time, _recalculate
        # _recalculate: LRANGE, get_batch_size, SET
        # Wait, inside _recalculate I pass config, so it doesn't fetch it again?
        # Impl: def _recalculate(self, key_stats: str, config: Dict[str, Any]):
        # So correct order: 
        # 1. get_config (in update_stats)
        # 2. LPUSH
        # 3. LTRIM
        # 4. LRANGE
        # 5. get_batch_size
        # 6. SET
        
        self.mock_op.inspect_redis.side_effect = [
            json.dumps(config), # 1. get_config
            None, # 2. LPUSH
            None, # 3. LTRIM
            json.dumps({"d": 500, "s": 1}) + "\n" + json.dumps({"d": 600, "s": 1}), # 4. LRANGE
            "10", # 5. get_batch_size
            None  # 6. SET
        ]

        self.sizer.update_stats(500, True)
        
        # Verify SET called with increased size (10 * 2 + 1 = 21)
        self.mock_op.inspect_redis.assert_called_with(["SET", self.sizer.KEY_CURRENT, "21"])

    @patch('time.time')
    def test_update_stats_decreases_on_failure(self, mock_time):
        mock_time.return_value = 100.0 # 100 % 5 = 0 < 0.5
        
        # Setup config
        config = {
            "min_size": 1, "max_size": 100, "target_latency_ms": 5000,
            "failure_threshold_rate": 0.1, "adjustment_factor": 2.0, "window_size": 2
        }
        
        # Order:
        # 1. get_config
        # 2. LPUSH
        # 3. LTRIM
        # 4. LRANGE
        # 5. get_batch_size
        # 6. SET
        
        self.mock_op.inspect_redis.side_effect = [
            json.dumps(config), # 1
            None, # 2
            None, # 3
            json.dumps({"d": 100, "s": 0}) + "\n" + json.dumps({"d": 100, "s": 0}), # 4
            "50", # 5 (current size)
            None # 6
        ]

        self.sizer.update_stats(100, False)
        
        # Verify decrease: 50 / 2 = 25
        self.mock_op.inspect_redis.assert_called_with(["SET", self.sizer.KEY_CURRENT, "25"])


class TestPhaseGate(unittest.TestCase):
    def setUp(self):
        self.mock_op = MagicMock()
        self.gate = PhaseGate(self.mock_op)

    def test_set_rule(self):
        self.gate.set_rule("3", "2", "complete")
        expected_json = json.dumps({"dependency": "2", "condition": "complete"})
        self.mock_op.inspect_redis.assert_called_with(["HSET", self.gate.KEY_RULES, "3", expected_json])

    def test_can_run_no_rule(self):
        self.mock_op.inspect_redis.return_value = None # HGET returns nothing
        self.assertTrue(self.gate.can_run("run1", "phase1"))

    def test_can_run_locked(self):
        # HGET rule
        rule = json.dumps({"dependency": "1", "condition": "complete"})
        
        # HMGET cursors (current=5, total=10)
        cursors = "5\n10" 
        
        self.mock_op.inspect_redis.side_effect = [rule, cursors]
        
        self.assertFalse(self.gate.can_run("run1", "2"))

    def test_can_run_unlocked(self):
        # HGET rule
        rule = json.dumps({"dependency": "1", "condition": "complete"})
        
        # HMGET cursors (current=10, total=10)
        cursors = "10\n10" 
        
        self.mock_op.inspect_redis.side_effect = [rule, cursors]
        
        self.assertTrue(self.gate.can_run("run1", "2"))

if __name__ == '__main__':
    unittest.main()
