from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/ntes-multi-day-poll.yml")


class MultiDayWorkflowTest(unittest.TestCase):
    def test_checkout_does_not_request_removed_ntes_branch(self):
        workflow = WORKFLOW.read_text()
        self.assertNotIn("ref: ntes", workflow)

    def test_multi_day_script_has_required_api_key_environment(self):
        workflow = WORKFLOW.read_text()
        self.assertIn(
            "RAILRADAR_API_KEY_MULTI_DAY:",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
