"""End-to-end smoke tests for PERT implementation."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from networkdiagram import CriticalPathMethod, PERTMethod

print('=== Test 1: Original CPM still works ===')
cpm = CriticalPathMethod()
cpm.add_activity('O', 0)
cpm.add_activity('A', 2)
cpm.add_activity('B', 5)
cpm.add_activity('C', 4)
cpm.add_relation('A', '-')
cpm.add_relation('B', 'A')
cpm.add_relation('C', 'B')
cpm.find_probable_paths()
cpm.find_critical_path()
assert cpm.critical_path == ['O', 'A', 'B', 'C'], f"Expected ['O','A','B','C'], got {cpm.critical_path}"
assert cpm.total_project_duration == 11, f"Expected 11, got {cpm.total_project_duration}"
print('PASS')

print('=== Test 2: PERTMethod basic ===')
pert = PERTMethod()
pert.add_activity('O')
pert.add_activity('A', optimistic=2, most_likely=4, pessimistic=6)
pert.add_activity('B', optimistic=3, most_likely=5, pessimistic=7)
pert.add_activity('C', optimistic=1, most_likely=2, pessimistic=3)
pert.add_relation('A', '-')
pert.add_relation('B', 'A')
pert.add_relation('C', 'B')
pert.find_probable_paths()
pert.find_critical_path()
assert pert.critical_path == ['O', 'A', 'B', 'C'], f"Expected ['O','A','B','C'], got {pert.critical_path}"
assert pert.total_project_duration == 11.0, f"Expected 11.0, got {pert.total_project_duration}"
assert pert.get_expected_time('A') == 4.0
assert pert.get_expected_time('B') == 5.0
assert pert.get_expected_time('C') == 2.0
print('PASS')

print('=== Test 3: PERT add_activities_relations ===')
pert2 = PERTMethod()
pert2.add_activity('O')
activities = ['A', 'B', 'C']
optimistic = [2, 3, 1]
most_likely = [4, 5, 2]
pessimistic = [6, 7, 3]
predecessors = ['-', 'A', 'B']
pert2.add_activities_relations(activities, optimistic, most_likely, pessimistic, predecessors)
pert2.find_probable_paths()
pert2.find_critical_path()
assert pert2.total_project_duration == 11.0, f"Expected 11.0, got {pert2.total_project_duration}"
print('PASS')

print('=== Test 4: Original add_activities_relations (backward compat) ===')
cpm2 = CriticalPathMethod()
cpm2.add_activity('O', 0)
cpm2.add_activities_relations(['A','B','C'], [2,5,4], ['-','A','B'])
cpm2.find_probable_paths()
cpm2.find_critical_path()
assert cpm2.critical_path == ['O', 'A', 'B', 'C'], f"Expected ['O','A','B','C'], got {cpm2.critical_path}"
assert cpm2.total_project_duration == 11, f"Expected 11, got {cpm2.total_project_duration}"
print('PASS')

print('=== Test 5: PERT with branching paths ===')
pert3 = PERTMethod()
pert3.add_activity('O')
pert3.add_activity('A', 2, 4, 6)
pert3.add_activity('B', 3, 5, 7)
pert3.add_activity('C', 1, 5, 9)
pert3.add_relation('A', '-')
pert3.add_relation('B', '-')
pert3.add_relation('C', 'A,B')
pert3.find_probable_paths()
pert3.find_critical_path()
assert pert3.total_project_duration == 10.0, f"Expected 10.0, got {pert3.total_project_duration}"
assert 'B' in pert3.critical_path, f"Expected B in critical path, got {pert3.critical_path}"
print('PASS')

print('=== Test 6: PERT variance calculations ===')
pert4 = PERTMethod()
pert4.add_activity('O')
pert4.add_activity('A', 2, 4, 6)
pert4.add_activity('B', 3, 5, 7)
pert4.add_relation('A', '-')
pert4.add_relation('B', 'A')
pert4.find_probable_paths()
pert4.find_critical_path()
expected_project_var = ((6-2)/6)**2 + ((7-3)/6)**2
assert abs(pert4.get_project_variance() - expected_project_var) < 0.001
assert abs(pert4.get_project_std_deviation() - expected_project_var**0.5) < 0.001
print('PASS')

print('=== Test 7: CPM without PERT fields ===')
node_from_cpm = cpm2.nodes['A']
assert node_from_cpm.optimistic == 0
assert node_from_cpm.most_likely == 0
assert node_from_cpm.pessimistic == 0
assert node_from_cpm.variance == 0
assert node_from_cpm.std_deviation == 0
print('PASS')

print()
print('All smoke tests passed!')
