import unittest
import sys
import os

# Add parent directory to path so we can import networkdiagram
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'networkdiagram', 'networkdiagram')))
from networkdiagram import CriticalPathMethod, Node

class TestDuplicateAndSelfReferential(unittest.TestCase):
    def setUp(self):
        self.cpm = CriticalPathMethod()
        self.cpm.add_activity('O', 0)

    def test_duplicate_activity_in_array(self):
        activities = ['A', 'B', 'A']
        durations = [1, 2, 3]
        predecessors = ['-', 'A', 'B']
        
        with self.assertRaises(ValueError) as context:
            self.cpm.add_activities_relations(activities, durations, predecessors)
        
        self.assertIn("Activity 'A' already exists. Duplicate names are not allowed.", str(context.exception))

    def test_self_referential_dependency(self):
        activities = ['A', 'B', 'C']
        durations = [1, 2, 3]
        predecessors = ['-', 'B', 'B'] # 'B' is predecessor of 'B'
        
        with self.assertRaises(ValueError) as context:
            self.cpm.add_activities_relations(activities, durations, predecessors)
            
        self.assertIn("Self-referential dependency detected: 'B' cannot be a predecessor of itself.", str(context.exception))

if __name__ == '__main__':
    unittest.main()
