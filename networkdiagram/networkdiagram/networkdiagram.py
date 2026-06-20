"""
NetworkDiagram - A lightweight library for CPM/PERT project network diagrams.
"""

from typing import Dict, List, Optional, Tuple, Union, Any, Set
from collections import deque
import networkx as nx
import matplotlib.pyplot as plt


class Node:
    """Represents an activity node in the network diagram."""
    
    def __init__(self, name: str, duration: float = 0) -> None:
        """
        Constructor for declaring a new Node or Activity

        Args:
            name (str): Name of the activity usually single character
            duration (float, optional): Duration of the activity. Defaults to 0.
            
        Raises:
            ValueError: If name is empty or duration is negative
        """
        # Input validation for Node
        if not name or not isinstance(name, str):
            raise ValueError(f"Activity name must be a non-empty string. Got: {name}")
        if duration < 0:
            raise ValueError(f"Activity duration cannot be negative. Got: {duration}")
            
        self.name: str = name
        self.duration: float = duration
        self.predecessors: List[str] = []
        self.successors: List[str] = []  # Tells which activities can start once the current activity is finished
        self.early_start: float = 0
        self.early_finish: float = 0
        self.latest_start: float = 0
        self.latest_finish: float = 0

        self.total_float: float = 0
        self.free_float: float = 0
        self.independent_float: float = 0

        
    def add_successor(self, node: 'Node') -> None:
        """
        Used to add a successor of a specific activity

        Args:
            node (Node): Object of Node
        """
        self.successors.append(node.name)
        node.predecessors.append(self.name)
        
    def node_summary(self) -> str:
        """
        Generates Summary report of an Activity

        Returns:
            str: contains information like name, duration and successors.
        """
        return f"Name : {self.name}, Duration : {self.duration}, Successor : {self.successors}"
        
    def __repr__(self) -> str:
        """String representation of the node."""
        return f"Node(name='{self.name}', duration={self.duration})"


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
        """
        Validate activity name.
        
        Args:
            name: Activity name to validate
            
        Raises:
            ValueError: If name is empty or not a string
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"Activity name must be a non-empty string. Got: {name}")
        if name.strip() == '':
            raise ValueError("Activity name cannot be empty or whitespace only")
            
    def _validate_duration(self, duration: float, activity_name: str = "") -> None:
        """
        Validate activity duration.
        
        Args:
            duration: Duration to validate
            activity_name: Name of the activity (for error message)
            
        Raises:
            ValueError: If duration is negative
        """
        if duration < 0:
            msg = f"Activity duration cannot be negative. Got: {duration}"
            if activity_name:
                msg = f"Duration cannot be negative for activity '{activity_name}'. Got: {duration}"
            raise ValueError(msg)
            
    def _validate_duplicate(self, name: str) -> None:
        """
        Check for duplicate activity names.
        
        Args:
            name: Activity name to check
            
        Raises:
            ValueError: If activity already exists
        """
        if name in self.nodes:
            raise ValueError(f"Activity '{name}' already exists. Duplicate names are not allowed.")
            
    def _detect_cycles(self) -> None:
        """
        Detect circular dependencies in the network.
        
        Raises:
            ValueError: If a circular dependency is detected
        """
        if not self.nodes:
            return
            
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> None:
            if node in rec_stack:
                cycle_nodes = list(rec_stack) + [node]
                raise ValueError(
                    f"Circular dependency detected: {' -> '.join(cycle_nodes)}"
                )
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            # Check all successors of this node
            if node in self.nodes:
                for successor in self.nodes[node].successors:
                    dfs(successor)
            
            rec_stack.remove(node)
        
        # Run DFS from each node
        for node in self.nodes:
            if node not in visited:
                dfs(node)
        
    def add_activity(self, name: str, duration: float) -> None:
        """
        Function to add a single activity with validation.

        Args:
            name (str): Name or alias of the activity
            duration (float): Duration of the activity
            
        Raises:
            ValueError: If name is invalid, duration is negative, or activity already exists
        """
        # Validate inputs
        self._validate_activity_name(name)
        self._validate_duration(duration, name)
        self._validate_duplicate(name)
        
        # Add the activity
        if name not in self.nodes:
            self.nodes[name] = Node(name, duration)
            
    def add_activities_relations(self, activities: List[str], durations: List[float], predecessors: List[str]) -> None:
        """
        Function to add multiple activities with its relation and validation.

        Args:
            activities (list): List of all activities
            durations (list): List of durations
            predecessors (list): List of predecessors
            
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
        durations_with_origin = durations.copy()
        durations_with_origin.append(0)  # For the Terminal Node
        
        for i in range(len(activities)):
            # Add activity (validation already done, so skip duplicate check)
            if activities[i] not in self.nodes:
                self.nodes[activities[i]] = Node(activities[i], durations[i])
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
                    min_ls: float = min(
                        (self.nodes[s].latest_start for s in node.successors if s in self.nodes), 
                        default=node.latest_finish
                    )

                    if min_ls < node.latest_finish:
                        node.latest_finish = min_ls
                        node.latest_start = node.latest_finish - node.duration
                        changed = True
        self.calculate_floats()

    def calculate_floats(self) -> None:
            """
            Calculate Total Float, Free Float and Independent Float
            """

            for node in self.nodes.values():

                # Total Float
                node.total_float = node.latest_start - node.early_start

                # Free Float
                if node.successors:
                    min_successor_es = min(
                        self.nodes[s].early_start
                        for s in node.successors
                        if s in self.nodes
                    )
                    node.free_float = min_successor_es - node.early_finish
                else:
                    node.free_float = node.total_float

                # Independent Float
                if node.predecessors and node.successors:

                    max_predecessor_lf = max(
                        self.nodes[p].latest_finish
                        for p in node.predecessors
                        if p in self.nodes
                    )

                    min_successor_es = min(
                        self.nodes[s].early_start
                        for s in node.successors
                        if s in self.nodes
                    )

                    node.independent_float = max(
                        0,
                        min_successor_es - max_predecessor_lf - node.duration
                    )
                else:
                    node.independent_float = 0
   

                
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
        pos: Dict[str, Tuple[float, float]] = {}
        levels: Dict[str, int] = {}

        # 1. Determine the level of each node using BFS
        q: deque = deque([(start_node, 0)])
        visited: Set[str] = {start_node}
        levels[start_node] = 0

        while q:
            node, level = q.popleft()
            neighbors = sorted(list(graph.neighbors(node)))  # Sort for consistent layout
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    levels[neighbor] = level + 1
                    q.append((neighbor, level + 1))

        # 2. Group nodes by level
        nodes_by_level: Dict[int, List[str]] = {}
        for node, level in levels.items():
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)

        # 3. Assign x, y coordinates
        for level, nodes in nodes_by_level.items():
            num_nodes_in_level = len(nodes)
            # Center the nodes vertically
            y_start: float = - (num_nodes_in_level - 1) / 2

            for i, node in enumerate(nodes):
                pos[node] = (float(level), y_start + float(i))

        return pos
    
    def display_network(self) -> None:
        """
        Function to Visualize the Network Diagram.
        Uses Networkx and Matplotlib for plotting.
        """
        self.get_edges()
        
        G = nx.Graph()
        plt.figure(figsize=(10, 4))
        
        # Add edges without duration for graph creation
        edges_without_duration: List[Tuple[str, str]] = [(e[0], e[1]) for e in self.edges]
        G.add_edges_from(edges_without_duration)    
        
        color_edges: List[Tuple[str, str]] = []
        if self.critical_path:
            l = 'O'
            for c in self.critical_path:
                color_edges.append((l, c))
                l = c
            color_edges.append((self.critical_path[-1], 'T'))  
        
        # If the edge falls in critical path then color of edge will be red, else it will be black
        edges_colors: List[str] = ['red' if (ed[0], ed[1]) in color_edges or (ed[1], ed[0]) in color_edges else 'black' for ed in G.edges()]
        
        initial_pos: Dict[str, Tuple[float, float]] = {'O': (0, 0), 'T': (10, 0)}
        fixed_nodes: List[str] = ['O', 'T']

        pos = self.get_hierarchical_layout(G, 'O')
        
        labels: Dict[str, str] = {}
        for node in G.nodes():
            if node in self.nodes:
                n = self.nodes[node]
                labels[node] = f"{node}\nES:{n.early_start} EF:{n.early_finish}\nLS:{n.latest_start} LF:{n.latest_finish}"
            else:
                labels[node] = str(node)
        
        nx.draw(G, pos, labels=labels, with_labels=True, node_size=2500, font_size=8, 
                edge_color=edges_colors, arrows=True, arrowstyle='-|>', arrowsize=20)
        
        # Create edge label dictionary
        edge_durations: Dict[Tuple[str, str], str] = {}
        for edge in self.edges:
            edge_durations[(edge[0], edge[1])] = str(edge[2]['duration'])
        
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_durations)

        plt.title("Network diagram with critical Path")
        plt.show()

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
        print(f"{'Node':<5} | {'ES':<3} | {'EF':<3} | {'LS':<3} | {'LF':<3} | {'TF':<3} | {'FF':<3} | {'IF':<3}")
        print("-" * 70)
        
        for name, node in self.nodes.items():
            print(
                f"{name:<5} | "
                f"{node.early_start:<3} | "
                f"{node.early_finish:<3} | "
                f"{node.latest_start:<3} | "
                f"{node.latest_finish:<3} | "
                f"{node.total_float:<3} | "
                f"{node.free_float:<3} | "
                f"{node.independent_float:<3}"
            )
        

# Example usage
if __name__ == "__main__":
    # Create a sample network
    cpm = CriticalPathMethod()
    
    # Add origin node
    cpm.add_activity('O', 0)
    
    # Add activities with relations
    activities = ['A', 'B', 'C', 'D', 'E']
    durations = [3, 4, 2, 5, 2]
    predecessors = ['-', 'A', 'A', 'B,C', 'C']
    
    cpm.add_activities_relations(activities, durations, predecessors)
    
    # Calculate paths
    cpm.find_probable_paths()
    cpm.find_critical_path()
    cpm.forward_pass()
    cpm.backward_pass()
    
    # Display results
    cpm.network_summary()
    cpm.display_network()
    cpm.generate_gantt_chart()