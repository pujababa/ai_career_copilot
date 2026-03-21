import unittest
from datetime import datetime

# Logic from app.py
def calculate_stats(placements):
    total_count = len(placements)
    interview_count = sum(1 for p in placements if p["status"] == "Interview")
    selected_count = sum(1 for p in placements if p["status"] == "Selected")
    rejected_count = sum(1 for p in placements if p["status"] == "Rejected")
    
    if total_count > 0:
        progress_percentage = min(100, int((selected_count * 100 + interview_count * 50) / total_count))
    else:
        progress_percentage = 0
        
    return total_count, interview_count, selected_count, rejected_count, progress_percentage

class TestPlacementEnhancedLogic(unittest.TestCase):
    def test_stats_calc(self):
        # Case 1: Mixed statuses
        placements = [
            {"status": "Applied"},
            {"status": "Interview"},
            {"status": "Selected"},
            {"status": "Rejected"}
        ]
        total, interview, selected, rejected, progress = calculate_stats(placements)
        self.assertEqual(total, 4)
        self.assertEqual(interview, 1)
        self.assertEqual(selected, 1)
        self.assertEqual(rejected, 1)
        # (1*100 + 1*50) / 4 = 150 / 4 = 37.5 -> 37
        self.assertEqual(progress, 37)

    def test_stats_full_selected(self):
        placements = [{"status": "Selected"}, {"status": "Selected"}]
        total, interview, selected, rejected, progress = calculate_stats(placements)
        self.assertEqual(progress, 100)

    def test_stats_empty(self):
        placements = []
        total, interview, selected, rejected, progress = calculate_stats(placements)
        self.assertEqual(progress, 0)

if __name__ == "__main__":
    unittest.main()
