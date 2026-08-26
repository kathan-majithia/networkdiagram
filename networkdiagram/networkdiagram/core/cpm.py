from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import networkx as nx

from networkdiagram.core.node import Node
from networkdiagram.visualization.network_plot import display_network as _display_network
from networkdiagram.visualization.network_plot import get_hierarchical_layout as _get_hierarchical_layout


class CriticalPathMethod:
    """
    It is a Network diagram method used in Project management in which duration of all activities are already known
    """
    
    def __init__(self) -> None:
        """
        Constructor for declaring a new Network
        """
        self.nodes: Dict[str, Node] = {}  # nodes (dict): A dictionary with (key,value) = (name or alias, object of Node)
        self.probable_paths: List[List[str]] = []  # List of all possible paths that are possible
        self.total_project_duration: float = -1  # The maximum time that the project will take to complete
        self.duration_unit: str = "days"  # By default duration is in days
        self.critical_path: List[str] = []  # It is a probable path having the maximum completion time
        self.edges: List[Tuple[str, str, Dict[str, float]]] = []  # Tuple (from,to,duration)
        
    def _validate_activity_name(self, name: str) -> None:
        if not name or not isinstance(name, str):
            raise ValueError(f"Activity name must be a non-empty string. Got: {name}")
        if name.strip() == '':
            raise ValueError("Activity name cannot be empty or whitespace only")
            
    def _validate_duration(self, duration: float, activity_name: str = "") -> None:
        if duration < 0:
            msg = f"Activity duration cannot be negative. Got: {duration}"
            if activity_name:
                msg = f"Duration cannot be negative for activity '{activity_name}'. Got: {duration}"
            raise ValueError(msg)
            
    def _validate_duplicate(self, name: str) -> None:
        if name in self.nodes:
            raise ValueError(f"Activity '{name}' already exists. Duplicate names are not allowed.")
            
    def _detect_cycles(self) -> None:
        if not self.nodes:
            return
        visited = set()
        rec_stack = set()
        def dfs(node: str) -> None:
            if node in rec_stack:
                cycle_nodes = list(rec_stack) + [node]
                raise ValueError(f"Circular dependency detected: {' -> '.join(cycle_nodes)}")
            if node in visited:
                return
            visited.add(node)
            rec_stack.add(node)
            if node in self.nodes:
                for successor in self.nodes[node].successors:
                    dfs(successor)
            rec_stack.remove(node)
        for node in self.nodes:
            if node not in visited:
                dfs(node)
        
    def add_activity(self, name: str, duration: float, normal_cost: float = 0, crash_cost: float = 0, crash_duration: float = None) -> None:
        """
        Function to add a single activity with optional crashing parameters

        Args:
            name (str): Name or alias of the activity
            duration (float): Normal duration of the activity
            normal_cost (float): Cost at normal duration. Defaults to 0.
            crash_cost (float): Cost at crash duration. Defaults to 0.
            crash_duration (float): Minimum possible duration. Defaults to normal duration.
            
        Raises:
            ValueError: If name is invalid, duration is negative, or activity already exists
        """
        self._validate_activity_name(name)
        self._validate_duration(duration, name)
        self._validate_duplicate(name)
        
        if crash_duration is None:
            crash_duration = duration
        self.nodes[name] = Node(name, duration, normal_cost, crash_cost, crash_duration)
            
    def add_activities_relations(self, activities: List[str], durations: List[float], predecessors: List[str],
                                  normal_costs: List[float] = None, crash_costs: List[float] = None, crash_durations: List[float] = None) -> None:
        """
        Function to add multiple activities with their relations and optional crashing parameters

        Args:
            activities (list): List of all activity names
            durations (list): List of durations
            predecessors (list): List of predecessors
            normal_costs (list, optional): Normal costs per activity. Defaults to None.
            crash_costs (list, optional): Crash costs per activity. Defaults to None.
            crash_durations (list, optional): Crash durations per activity. Defaults to None.
            
        Raises:
            ValueError: If lists are empty, have mismatched lengths, or contain invalid data
            ValueError: If any activity name is invalid or duplicate
            ValueError: If any predecessor references a non-existent activity
        """
        # Validate activities list is not empty
        if not activities:
            raise ValueError("Activities list cannot be empty")
            
        # Validate lists have the same length (activities and durations)
        if len(activities) != len(durations):
            raise ValueError(
                f"Activities list length ({len(activities)}) must match "
                f"durations list length ({len(durations)})"
            )
            
        # Validate all activities and durations first
        all_valid_activities = set()
        for i, (act, dur) in enumerate(zip(activities, durations)):
            self._validate_activity_name(act)
            self._validate_duration(dur, act)
            self._validate_duplicate(act)
            all_valid_activities.add(act)
            
        # Validate predecessors exist (check before adding)
        for pred_list in predecessors:
            if pred_list == '-' or pred_list == '':
                continue
            preds = [p.strip() for p in pred_list.split(',') if p.strip()]
            for pred in preds:
                # Check if predecessor exists in current nodes or will be added
                if pred not in self.nodes and pred not in all_valid_activities:
                    raise ValueError(
                        f"Predecessor '{pred}' not found. "
                        f"Make sure it exists or is added before being referenced."
                    )
                    
        # Validate predecessors list length matches activities
        if len(activities) != len(predecessors):
            raise ValueError(
                f"Activities list length ({len(activities)}) must match "
                f"predecessors list length ({len(predecessors)})"
            )
            
        # Now add all activities and relations
        durations_with_origin = [0] + list(durations) + [0]
        
        for i in range(len(activities)):
            nc = normal_costs[i] if normal_costs else 0
            cc = crash_costs[i] if crash_costs else 0
            cd = crash_durations[i] if crash_durations else None
            self.add_activity(activities[i], durations_with_origin[i + 1],
                              normal_cost=nc, crash_cost=cc, crash_duration=cd)
            self.add_relation(activities[i], predecessors[i])
            
    def add_relation(self, cur: str, predecessors: str) -> None:
        """
        Function to add a relation of a single activity with validation.

        Args:
            cur (str): Current Activity
            predecessors (str): Consist of predecessors separated by ',' in which of multiple Predecessors
            
        Raises:
            ValueError: If current activity doesn't exist
            ValueError: If any predecessor doesn't exist
        """
        # Validate current activity exists
        if cur not in self.nodes:
            raise ValueError(f"Activity '{cur}' does not exist. Add it first.")
            
        # Validate predecessors
        if predecessors and predecessors != '-':
            preds = [p.strip() for p in predecessors.split(',') if p.strip()]
            for p in preds:
                if p != 'O' and p not in self.nodes:
                    raise ValueError(
                        f"Predecessor '{p}' does not exist. "
                        f"Make sure it's added before creating the relation."
                    )
        
        # Process each predecessor
        for p in predecessors.split(','):
            p = p.strip()
            
            if p == '-':
                """
                The first node will not have any predecessor so we will add origin as the predecessor
                """
                if 'O' in self.nodes:
                    parent = self.nodes['O']
                    if cur not in parent.successors:
                        parent.successors.append(cur)
                if cur in self.nodes:
                    if 'O' not in self.nodes[cur].predecessors:
                        self.nodes[cur].predecessors.append('O')
            
            elif p in self.nodes:
                parent = self.nodes[p]
                if cur not in parent.successors:
                    parent.successors.append(cur)
                if cur in self.nodes:
                    if p not in self.nodes[cur].predecessors:
                        self.nodes[cur].predecessors.append(p)
            
    def find_probable_paths(self, cur: Optional[str] = None, path: Optional[Union[str, List[str]]] = None) -> None:
        """
        Function to find all probable paths with cycle detection.

        Args:
            cur (str, optional): Current Activity name. Defaults to None.
            path (Union[str, List[str]], optional): Path starting from origin to current activity. Defaults to None.
            
        Raises:
            ValueError: If circular dependency is detected
        """
        # Check for circular dependencies before finding paths
        self._detect_cycles()
        
        if cur is None:
            if 'O' in self.nodes:
                cur = 'O'
            else:
                return
        
        if path is None:
            path = []
        elif isinstance(path, str):
            path = [p.strip() for p in path.split(',') if p.strip()]

        path = path + [cur]
            
        if len(self.nodes[cur].successors) == 0:
            self.probable_paths.append(path)
            return
        
        for c in self.nodes[cur].successors:
            if c in self.nodes:
                self.find_probable_paths(c, path)
    
    def find_critical_path(self, cur: Optional[str] = None) -> List[str]:
        """
        Function to find Critical Path

        Args:
            cur (str, optional): Current activity. Defaults to None.

        Returns:
            List[str]: The critical path as a list of activity names
        """
        if not self.probable_paths:
            self.find_probable_paths()
            
        self.critical_path = []
        self.total_project_duration = -1
        
        for probable_path in self.probable_paths:
            path_duration: float = sum(self.nodes[cur_node].duration for cur_node in probable_path if cur_node in self.nodes)
            if path_duration > self.total_project_duration:
                self.critical_path = probable_path
                self.total_project_duration = path_duration
            elif path_duration == self.total_project_duration:
                if isinstance(self.critical_path, list) and not isinstance(self.critical_path[0] if self.critical_path else None, str):
                    # Handle case where critical_path might be a list of paths
                    pass
                    
        return self.critical_path

    def forward_pass(self) -> None:
        """
        Function to calculate Early Start (ES) and Early Finish (EF) for each node
        """
        for node in self.nodes.values():
            node.early_start = 0.0
            node.early_finish = node.duration
            
        changed: bool = True
        while changed:
            changed = False
            for node in self.nodes.values():
                if node.predecessors:
                    max_ef: float = max((self.nodes[p].early_finish for p in node.predecessors if p in self.nodes), default=0.0)
                    if max_ef > node.early_start:
                        node.early_start = max_ef
                        node.early_finish = node.early_start + node.duration
                        changed = True

    def backward_pass(self) -> None:
        """
        Function to calculate Late Start (LS) and Late Finish (LF) for each node
        """
        if self.total_project_duration == -1:
            self.total_project_duration = max((n.early_finish for n in self.nodes.values()), default=0.0)
            
        for node in self.nodes.values():
            node.latest_finish = self.total_project_duration
            node.latest_start = node.latest_finish - node.duration
            
        changed: bool = True
        while changed:
            changed = False
            for node in self.nodes.values():
                if node.successors:
                    min_ls: float = min((self.nodes[s].latest_start for s in node.successors if s in self.nodes), default=node.latest_finish)
                    if min_ls < node.latest_finish:
                        node.latest_finish = min_ls
                        node.latest_start = node.latest_finish - node.duration
                        changed = True
                
    def get_edges(self) -> List[Tuple[str, str, Dict[str, float]]]:
        """
        Function to convert activity and successors in form of edges for visualization

        Returns:
            List[Tuple[str, str, Dict[str, float]]]: List of edges with duration attributes
        """
        self.edges = []
        for node in self.nodes:
            if self.nodes[node].successors:
                for suc in self.nodes[node].successors:
                    self.edges.append((self.nodes[node].name, suc, {'duration': self.nodes[node].duration}))
            else:
                self.edges.append((self.nodes[node].name, 'T', {'duration': self.nodes[node].duration}))
        return self.edges
    
    def get_hierarchical_layout(self, graph: nx.Graph, start_node: str) -> Dict[str, Tuple[float, float]]:
        """
        Calculates node positions for a hierarchical layout.

        Args:
            graph (nx.Graph): The graph to lay out.
            start_node (str): The node to start the layout from (usually the root).

        Returns:
            Dict[str, Tuple[float, float]]: A dictionary of node positions {node: (x, y)}.
        """
        return _get_hierarchical_layout(graph, start_node)
    
    def display_network(self) -> None:
        """
        Function to Visualize the Network Diagram.
        Uses Networkx and Matplotlib for plotting.
        """
        _display_network(self)

    def generate_gantt_chart(self, show: bool = True) -> None:
        """
        Function to Visualize the Project Schedule as a Gantt Chart.
        Uses Matplotlib for plotting.
        
        Args:
            show (bool): If True, displays the plot using plt.show(). Defaults to True.
        """
        if self.total_project_duration == -1:
            self.find_probable_paths()
            self.find_critical_path()
            self.forward_pass()
            self.backward_pass()
            
        if not self.nodes:
            print("No activities to display in Gantt Chart.")
            return

        # Prepare data for plotting
        activities = list(self.nodes.values())
            
        # Sort activities by early start, then by duration descending
        activities.sort(key=lambda x: (x.early_start, -x.duration))
        
        names = [node.name for node in activities]
        starts = [node.early_start for node in activities]
        durations = [node.duration for node in activities]
        
        # Colors: red for critical path, light blue for others
        colors = ['red' if node.name in self.critical_path else 'skyblue' for node in activities]
        
        fig, ax = plt.subplots(figsize=(10, max(4, len(activities) * 0.5)))
        
        # Y positions (reversed so earliest starts are at the top)
        y_pos = list(range(len(activities)))
        y_pos.reverse()
        
        # Plot slack/float
        slack_plotted = False
        for i, node in enumerate(activities):
            y = y_pos[i]
            slack = node.latest_finish - node.early_finish
            if slack > 0:
                label = 'Slack/Float' if not slack_plotted else ""
                ax.barh(y, slack, left=node.early_finish, height=0.5, color='lightgray', hatch='//', edgecolor='gray', alpha=0.5, label=label)
                slack_plotted = True
        
        # Plot main durations
        ax.barh(y_pos, durations, left=starts, height=0.5, color=colors, edgecolor='black')
        
        # Plot zero duration milestones as diamonds
        for i, node in enumerate(activities):
            if node.duration == 0:
                ax.plot(node.early_start, y_pos[i], marker='D', markersize=8, color=colors[i], markeredgecolor='black')
        
        # Labels and formatting
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.set_xlabel(f'Time ({self.duration_unit})')
        ax.set_ylabel('Activities')
        ax.set_title('Project Schedule - Gantt Chart')
        ax.grid(True, axis='x', linestyle='--', alpha=0.7)
        
        # Create custom legend
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D
        legend_elements = [
            Patch(facecolor='red', edgecolor='black', label='Critical Activity'),
            Patch(facecolor='skyblue', edgecolor='black', label='Normal Activity'),
            Patch(facecolor='lightgray', edgecolor='gray', hatch='//', alpha=0.5, label='Slack/Float'),
            Line2D([0], [0], marker='D', color='w', markerfacecolor='black', markersize=8, label='Milestone', linestyle='None')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        if self.total_project_duration > 0:
            ax.set_xlim(0, self.total_project_duration * 1.05)
            
        plt.tight_layout()
        
        if show:
            plt.show()


    def network_summary(self) -> None:
        """
        Function to generate entire Network Summary including number of nodes, Activities, 
        Probable paths, Critical Path, Total Project Duration and Edges
        """
        print("\n\n---------------Network Summary-----------------\n\n")
        print("Total number of Activities/Nodes : ", len(self.nodes))
        print("Nodes : ", end="")
        for c in self.nodes:
            print(c, " ", end="")
            
        print("\nAll Probable Paths : ")
        for p in self.probable_paths:
            print(p)
        print("Critical Path : ", self.critical_path)
        print("Total project duration : ", self.total_project_duration)
        print("Duration unit :", self.duration_unit)
        
        self.get_edges()
        print("Edges : ", self.edges)
        
        print("\nNode Properties:")
        print(f"{'Node':<5} | {'ES':<3} | {'EF':<3} | {'LS':<3} | {'LF':<3}")
        print("-" * 35)
        for name, node in self.nodes.items():
            print(f"{name:<5} | {node.early_start:<3} | {node.early_finish:<3} | {node.latest_start:<3} | {node.latest_finish:<3}")

    def get_critical_path_activities(self):
        """
        Returns activity names on the critical path, excluding origin (O) and terminal (T).
        Handles both single critical path and multiple critical paths of equal duration.

        Returns:
            list: Activity names eligible for crashing
        """
        if not self.critical_path:
            return []

        activities = set()

        for item in self.critical_path:
            if isinstance(item, list):
                for act in item:
                    if isinstance(act, str) and act in self.nodes and act not in ('O', 'T'):
                        activities.add(act)
            elif isinstance(item, str):
                if item in self.nodes and item not in ('O', 'T'):
                    activities.add(item)

        return list(activities)

    def crash_project(self, target_duration):
        """
        Implements Time-Cost Trade-off (Crashing) Algorithm.

        Steps:
            1. Find critical path
            2. Find critical path activity with minimum cost slope
            3. Crash it by 1 time unit
            4. Recalculate critical path
            5. Repeat until target duration reached or no more crashing possible

        Args:
            target_duration (int): Desired project duration after crashing

        Returns:
            list: Crashing schedule — one dict per iteration
        """
        self.forward_pass()
        self.backward_pass()
        self.find_probable_paths()
        self.find_critical_path()

        crash_schedule = []
        total_extra_cost = 0
        iteration = 0

        print(f"\n{'='*60}")
        print(f"  TIME-COST TRADE-OFF (CRASHING) ANALYSIS")
        print(f"{'='*60}")
        print(f"  Initial Project Duration : {self.total_project_duration} days")
        print(f"  Target Duration          : {target_duration} days")
        print(f"{'='*60}\n")

        while self.total_project_duration > target_duration:

            critical_activities = self.get_critical_path_activities()
            crashable = [
                act for act in critical_activities
                if self.nodes[act].can_be_crashed()
            ]

            if not crashable:
                print("  No more activities can be crashed. Minimum duration reached.")
                break

            best_activity = min(crashable, key=lambda act: self.nodes[act].cost_slope())
            node = self.nodes[best_activity]
            slope = node.cost_slope()

            node.duration -= 1
            total_extra_cost += slope
            iteration += 1

            self.probable_paths = []
            self.total_project_duration = -1
            self.critical_path = []
            self.forward_pass()
            self.backward_pass()
            self.find_probable_paths()
            self.find_critical_path()

            step = {
                'iteration': iteration,
                'activity_crashed': best_activity,
                'new_duration': node.duration,
                'cost_slope': round(slope, 2),
                'total_extra_cost': round(total_extra_cost, 2),
                'project_duration': self.total_project_duration,
                'critical_path': list(self.critical_path)
            }
            crash_schedule.append(step)

            print(f"  Iteration {iteration}:")
            print(f"    Activity Crashed     : {best_activity}")
            print(f"    New Duration         : {node.duration} days")
            print(f"    Cost Slope           : {round(slope, 2)}")
            print(f"    Total Extra Cost     : {round(total_extra_cost, 2)}")
            print(f"    New Project Duration : {self.total_project_duration} days")
            print(f"    Critical Path        : {' -> '.join(str(x) for x in self.critical_path)}")
            print()

        print(f"{'='*60}")
        print(f"  CRASHING COMPLETE")
        print(f"  Final Duration    : {self.total_project_duration} days")
        print(f"  Total Extra Cost  : {round(total_extra_cost, 2)}")
        print(f"{'='*60}\n")

        return crash_schedule

    def display_crash_schedule(self, crash_schedule):
        """
        Displays crashing schedule as a formatted table with aligned columns.

        Args:
            crash_schedule (list): Output from crash_project()
        """
        if not crash_schedule:
            print("No crashing was performed.")
            return

        col1, col2, col3, col4, col5, col6 = 6, 12, 10, 12, 12, 10
        total_width = col1 + col2 + col3 + col4 + col5 + col6 + 5

        print(f"\n{'='*total_width}")
        print(f"  CRASHING SCHEDULE")
        print(f"{'='*total_width}")
        print(
            f"  {'Iter':<{col1}}"
            f"{'Activity':<{col2}}"
            f"{'New Dur':<{col3}}"
            f"{'Cost Slope':<{col4}}"
            f"{'Total Cost':<{col5}}"
            f"{'Proj Dur':<{col6}}"
        )
        print(f"  {'-'*total_width}")

        for step in crash_schedule:
            print(
                f"  {step['iteration']:<{col1}}"
                f"{step['activity_crashed']:<{col2}}"
                f"{step['new_duration']:<{col3}}"
                f"{step['cost_slope']:<{col4}}"
                f"{step['total_extra_cost']:<{col5}}"
                f"{step['project_duration']:<{col6}}"
            )
        print(f"{'='*total_width}\n")


# Example usage
if __name__ == "__main__":
    cpm = CriticalPathMethod()
    
    cpm.add_activity('O', 0)
    
    activities      = ['A', 'B', 'C', 'D', 'E']
    durations       = [6, 4, 5, 3, 4]
    predecessors    = ['-', '-', 'A', 'B', 'C']
    normal_costs    = [800, 500, 600, 400, 700]
    crash_costs     = [1000, 700, 900, 500, 1100]
    crash_durations = [4, 2, 3, 2, 2]
    
    cpm.add_activities_relations(
        activities, durations, predecessors,
        normal_costs=normal_costs,
        crash_costs=crash_costs,
        crash_durations=crash_durations
    )
    
    crash_schedule = cpm.crash_project(target_duration=13)
    cpm.display_crash_schedule(crash_schedule)
    # Display results
    cpm.network_summary()
    cpm.display_network()
    cpm.generate_gantt_chart()
