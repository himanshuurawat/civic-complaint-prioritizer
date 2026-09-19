import unittest

import pandas as pd

from adapters import adapt_bbmp
from pipeline import clean_and_score


class PipelineTests(unittest.TestCase):
    def test_bbmp_adapter_disables_text_duplicate_detection(self):
        raw = pd.DataFrame(
            [
                {"Complaint ID": "1", "Category": "Electrical", "Sub Category": "Wire", "Grievance Date": "2025-01-01", "Ward Name": "Ward A", "Grievance Status": "Open"},
                {"Complaint ID": "2", "Category": "Electrical", "Sub Category": "Wire", "Grievance Date": "2025-01-02", "Ward Name": "Ward A", "Grievance Status": "Open"},
            ]
        )
        result = clean_and_score(adapt_bbmp(raw))
        self.assertEqual(int(result["duplicate_count"].sum()), 0)
        self.assertTrue((result["predicted_category"] == "Electrical").all())

    def test_missing_required_column_is_rejected(self):
        with self.assertRaises(ValueError):
            clean_and_score(pd.DataFrame({"complaint_id": ["1"]}))


if __name__ == "__main__":
    unittest.main()
