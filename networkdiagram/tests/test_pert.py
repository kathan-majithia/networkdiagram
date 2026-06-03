import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from networkdiagram import PERTMethod, CriticalPathMethod, Node


class TestPERTFormulas(unittest.TestCase):
    """Test core PERT formula calculations."""

    def test_expected_time_formula(self):
        """TE = (O + 4M + P) / 6"""
        # O=2, M=4, P=6 -> TE = (2 + 16 + 6)/6 = 24/6 = 4.0
        node = Node("A", optimistic=2, most_likely=4, pessimistic=6)
        self.assertEqual(node.expected_time, 4.0)

    def test_expected_time_symmetric(self):
        """When O, M, P are equal, TE equals that value."""
        node = Node("B", optimistic=5, most_likely=5, pessimistic=5)
        self.assertEqual(node.expected_time, 5.0)

    def test_expected_time_skewed_right(self):
        """TE with right-skewed distribution."""
        # O=1, M=2, P=9 -> TE = (1 + 8 + 9)/6 = 18/6 = 3.0
        node = Node("C", optimistic=1, most_likely=2, pessimistic=9)
        self.assertEqual(node.expected_time, 3.0)

    def test_variance_formula(self):
        """Variance = ((P - O) / 6)^2"""
        # O=2, P=8 -> Variance = ((8-2)/6)^2 = (6/6)^2 = 1.0
        node = Node("D", optimistic=2, most_likely=5, pessimistic=8)
        self.assertAlmostEqual(node.variance, 1.0)

    def test_variance_zero(self):
        """When O == P, variance is 0."""
        node = Node("E", optimistic=4, most_likely=4, pessimistic=4)
        self.assertEqual(node.variance, 0.0)

    def test_std_deviation(self):
        """Standard deviation = sqrt(variance)."""
        node = Node("F", optimistic=2, most_likely=5, pessimistic=8)
        self.assertAlmostEqual(node.std_deviation, 1.0)

    def test_std_deviation_larger_range(self):
        """Larger range gives larger std deviation."""
        # O=1, P=13 -> Variance = ((12)/6)^2 = 4, SD = 2
        node = Node("G", optimistic=1, most_likely=5, pessimistic=13)
        self.assertAlmostEqual(node.variance, 4.0)
        self.assertAlmostEqual(node.std_deviation, 2.0)


class TestPERTMethodClass(unittest.TestCase):
    """Test the PERTMethod class integration."""

    def setUp(self):
        self.pert = PERTMethod()
        self.pert.add_activity('O', 0, 0, 0)

    def test_add_activity_creates_node(self):
        """Adding a PERT activity creates a Node with correct estimates."""
        self.pert.add_activity('A', optimistic=2, most_likely=4, pessimistic=6)
        self.assertIn('A', self.pert.nodes)
        self.assertEqual(self.pert.nodes['A'].optimistic, 2)
        self.assertEqual(self.pert.nodes['A'].most_likely, 4)
        self.assertEqual(self.pert.nodes['A'].pessimistic, 6)

    def test_add_activity_computes_expected_time(self):
        """Adding activity computes expected time automatically."""
        self.pert.add_activity('A', optimistic=2, most_likely=4, pessimistic=6)
        self.assertEqual(self.pert.nodes['A'].expected_time, 4.0)
        self.assertEqual(self.pert.nodes['A'].duration, 4.0)

    def test_get_expected_time(self):
        self.pert.add_activity('A', 2, 4, 6)
        self.assertEqual(self.pert.get_expected_time('A'), 4.0)

    def test_get_variance(self):
        self.pert.add_activity('A', 2, 4, 6)
        self.assertAlmostEqual(self.pert.get_variance('A'), ((6-2)/6)**2)

    def test_get_std_deviation(self):
        self.pert.add_activity('A', 2, 4, 6)
        self.assertAlmostEqual(self.pert.get_std_deviation('A'), ((6-2)/6))

    def test_get_expected_time_nonexistent(self):
        self.assertIsNone(self.pert.get_expected_time('Z'))

    def test_add_activity_no_duplicates(self):
        """Adding same activity twice should not duplicate it."""
        self.pert.add_activity('A', 2, 4, 6)
        self.pert.add_activity('A', 5, 7, 9)
        # Should retain the first entry
        self.assertEqual(self.pert.nodes['A'].optimistic, 2)
        self.assertEqual(len(self.pert.nodes), 2)  # O and A


class TestPERTCriticalPath(unittest.TestCase):
    """Test PERT critical path calculation."""

    def setUp(self):
        self.pert = PERTMethod()
        self.pert.add_activity('O', 0, 0, 0)

    def test_simple_path(self):
        """Simple linear path with three-point estimates."""
        activities = ['A', 'B', 'C']
        optimistic = [2, 3, 1]
        most_likely = [4, 5, 2]
        pessimistic = [6, 7, 3]
        predecessors = ['-', 'A', 'B']

        self.pert.add_activities_relations(activities, optimistic, most_likely, pessimistic, predecessors)
        self.pert.find_probable_paths()
        self.pert.find_critical_path()

        # Expected times: A=(2+16+6)/6=4, B=(3+20+7)/6=5, C=(1+8+3)/6=2
        # Total = 4+5+2 = 11
        self.assertAlmostEqual(self.pert.total_project_duration, 11.0)
        self.assertEqual(self.pert.critical_path, ['O', 'A', 'B', 'C'])

    def test_two_paths_chooses_longer(self):
        """
            O -> A(2,4,6) -> C(1,5,9)
            O -> B(3,5,7) -> C
        Path1 O-A-C: TE_A=4, TE_C=((1+20+9)/6)=5, total=9
        Path2 O-B-C: TE_B=5, TE_C=5, total=10
        Critical: O-B-C
        """
        self.pert.add_activity('A', 2, 4, 6)
        self.pert.add_activity('B', 3, 5, 7)
        self.pert.add_activity('C', 1, 5, 9)
        self.pert.add_relation('A', '-')
        self.pert.add_relation('B', '-')
        self.pert.add_relation('C', 'A,B')
        self.pert.find_probable_paths()
        self.pert.find_critical_path()

        self.assertAlmostEqual(self.pert.total_project_duration, 10.0)
        self.assertIn('B', self.pert.critical_path)

    def test_project_variance(self):
        """
        Simple path O-A-B-C
        A: O=2,M=4,P=6 -> Var=((6-2)/6)^2 = 0.4444
        B: O=3,M=5,P=7 -> Var=((7-3)/6)^2 = 0.4444
        C: O=1,M=2,P=3 -> Var=((3-1)/6)^2 = 0.1111
        Project Variance = 0.4444+0.4444+0.1111 = 1.0 (approx)
        """
        activities = ['A', 'B', 'C']
        optimistic = [2, 3, 1]
        most_likely = [4, 5, 2]
        pessimistic = [6, 7, 3]
        predecessors = ['-', 'A', 'B']
        self.pert.add_activities_relations(activities, optimistic, most_likely, pessimistic, predecessors)
        self.pert.find_probable_paths()
        self.pert.find_critical_path()

        expected_var = ((6-2)/6)**2 + ((7-3)/6)**2 + ((3-1)/6)**2
        self.assertAlmostEqual(self.pert.get_project_variance(), expected_var, places=4)

    def test_project_std_deviation(self):
        activities = ['A', 'B']
        optimistic = [2, 3]
        most_likely = [4, 5]
        pessimistic = [6, 7]
        predecessors = ['-', 'A']
        self.pert.add_activities_relations(activities, optimistic, most_likely, pessimistic, predecessors)
        self.pert.find_probable_paths()
        self.pert.find_critical_path()

        expected_var = ((6-2)/6)**2 + ((7-3)/6)**2
        expected_sd = expected_var ** 0.5
        self.assertAlmostEqual(self.pert.get_project_std_deviation(), expected_sd, places=4)


class TestBackwardCompatibility(unittest.TestCase):
    """Ensure original CriticalPathMethod still works unchanged."""

    def test_cpm_still_works(self):
        cpm = CriticalPathMethod()
        cpm.add_activity('O', 0)
        activities = ['A', 'B', 'C']
        durations = [2, 5, 4]
        predecessors = ['-', 'A', 'B']
        cpm.add_activities_relations(activities, durations, predecessors)
        cpm.find_probable_paths()
        cpm.find_critical_path()
        self.assertEqual(cpm.total_project_duration, 11)
        self.assertEqual(cpm.critical_path, ['O', 'A', 'B', 'C'])

    def test_node_without_pert(self):
        """Node created without PERT fields should work as before."""
        node = Node("X", duration=5)
        self.assertEqual(node.duration, 5)
        self.assertEqual(node.optimistic, 0)
        self.assertEqual(node.most_likely, 0)
        self.assertEqual(node.pessimistic, 0)
        self.assertEqual(node.variance, 0)
        self.assertEqual(node.std_deviation, 0)
        self.assertEqual(node.expected_time, 5)


if __name__ == '__main__':
    unittest.main()
