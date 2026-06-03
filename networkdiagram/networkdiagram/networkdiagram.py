import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from collections import deque

class Node:
    def __init__(self, name, duration=0, optimistic=0, most_likely=0, pessimistic=0):
        """
        Constructor for declaring a new Node or Activity

        Args:
            name (string): Name of the activity usually single character
            duration (__type__, optional): Duration of the activity. Defaults to 0.
            optimistic (number, optional): Optimistic time estimate (a). Defaults to 0.
            most_likely (number, optional): Most likely time estimate (m). Defaults to 0.
            pessimistic (number, optional): Pessimistic time estimate (b). Defaults to 0.
        """
        self.name = name
        self.optimistic = optimistic
        self.most_likely = most_likely
        self.pessimistic = pessimistic
        
        if optimistic or most_likely or pessimistic:
            self.duration = (optimistic + 4 * most_likely + pessimistic) / 6
            self.expected_time = self.duration
        else:
            self.duration = duration
            self.expected_time = duration
            
        self.predecessors = []
        self.successors = [] # Tells which activities can start once the current activity is finished
        self.early_start = self.early_finish = self.latest_start = self.latest_finish = 0 # Pending
        
    @property
    def variance(self):
        if self.pessimistic or self.optimistic:
            return ((self.pessimistic - self.optimistic) / 6) ** 2
        return 0
    
    @property
    def std_deviation(self):
        return self.variance ** 0.5
        
    def add_successor(self,node):
        """
        Used to add a successor of a specific activity

        Args:
            node (Node): Object of Node
        """
        self.successors.append(node)
        node.predecessors.append(self)
        
    def node_summary(self):
        """
        Generates Summary report of an Activity

        Returns:
            string: contains information like name, duration and successors.
        """
        if self.optimistic or self.most_likely or self.pessimistic:
            return (f"Name : {self.name}, O : {self.optimistic}, M : {self.most_likely}, "
                    f"P : {self.pessimistic}, TE : {self.expected_time:.2f}, "
                    f"Variance : {self.variance:.4f}, Std Dev : {self.std_deviation:.4f}, "
                    f"Successor : {self.successors}")
        return f"Name : {self.name}, Duration : {self.duration}, Successor : {self.successors}"
        
class CriticalPathMethod:
    """
    It is a Network diagram method used in Project management in which duration of all activities are already known
    """
    def __init__(self):
        """
        Constructor for declaring a new Network
        """
        self.nodes = {} # nodes (dict): A dictionary with (key,value) = (name or alias, object of Node)
        self.probable_paths = [] # List of all possible paths that are possible
        self.total_project_duration = -1 # The maximum time that the project will take to complete
        self.duration_unit = "days" # By default duration is in days
        self.critical_path = [] # It is a probable path having the maximum completion time
        self.edges = [] # Tuple (from,to,duration)
        
    def add_activity(self,name,duration):
        """
        Function to add a single activity

        Args:
            name (string): Name or alias of the activity
            duration (__type__): Duration of the activity
        """
        if name not in self.nodes:
            self.nodes[name] = Node(name,duration)
            
    def add_activities_relations(self,activities,durations,predecessors):
        """
        Function to add multiple activities with its relation

        Args:
            activities (list): List of all activities
            durations (list): List of durations
            predecessors (list): List of predecessors
        """
        
        durations.append(0) # For the Terminal Node
        for i in range(0,len(activities)):
            self.add_activity(activities[i],durations[i])
            self.add_relation(activities[i],predecessors[i])
            
    def add_relation(self,cur,predecessors):
        """
        Function to add a relation of a single activity

        Args:
            cur (string): Current Activity
            predecessors (string): Consist of predecessors seperated by ',' in which of multiple Predecessors
        """
        
        for p in predecessors.split(','):
            p = p.strip()
            
            if p == '-':
                """
                The first node will not have any predecessor so we will add origin as the predecessor
                """
                parent = self.nodes['O']
                parent.successors.append(cur)
            
            elif p in self.nodes:
                parent = self.nodes[p]
                parent.successors.append(cur)
            
    def find_probable_paths(self,cur=None,path=""):
        """
        Function to find all probable paths

        Args:
            cur (Node, optional): Current Activity. Defaults to None.
            path (string, optional): Path starting from origin to current activity. Defaults to "".
        """
        
        if cur is None:
            if 'O' in self.nodes:
                cur = self.nodes['O']
            else:
                return
        
        path +=  str(cur.name)
            
        if len(cur.successors) == 0:
            path = [p for p in path]
            self.probable_paths.append(path)
            return
        for c in cur.successors:
            if c in self.nodes:
                self.find_probable_paths(self.nodes[c],path)
    
    def find_critical_path(self,cur=None):
        """
        Function to find Critical Path

        Args:
            cur (Node, optional): Current activity. Defaults to None.
        """

        
        for probable_path in self.probable_paths:
            if(sum(self.nodes[cur_node].duration for cur_node in probable_path) > self.total_project_duration):
                self.critical_path = probable_path
                self.total_project_duration = sum(self.nodes[cur_node].duration for cur_node in probable_path)
            elif(sum(self.nodes[cur_node].duration for cur_node in probable_path) == self.total_project_duration):
                self.critical_path.append(probable_path)
                
    def get_edges(self):
        """
        Function to convert activity and successors in form of edges for visualization
        """
        for node in self.nodes:
            if self.nodes[node].successors:
                for suc in self.nodes[node].successors:
                    self.edges.append((self.nodes[node].name,suc,{'duration':self.nodes[node].duration}))
                
            else:
                self.edges.append((self.nodes[node].name,'T',{'duration':self.nodes[node].duration}))
    
    def get_hierarchical_layout(self,graph, start_node):
        """
        Calculates node positions for a hierarchical layout.

        Args:
            graph (nx.Graph): The graph to lay out.
            start_node: The node to start the layout from (usually the root).

        Returns:
            dict: A dictionary of node positions {node: (x, y)}.
        """
        pos = {}
        levels = {}

        # 1. Determine the level of each node using BFS
        q = deque([(start_node, 0)])
        visited = {start_node}
        levels[start_node] = 0

        while q:
            node, level = q.popleft()
            neighbors = sorted(list(graph.neighbors(node))) # Sort for consistent layout
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    levels[neighbor] = level + 1
                    q.append((neighbor, level + 1))

        # 2. Group nodes by level
        nodes_by_level = {}
        for node, level in levels.items():
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)

        # 3. Assign x, y coordinates
        for level, nodes in nodes_by_level.items():
            num_nodes_in_level = len(nodes)
            # Center the nodes vertically
            y_start = - (num_nodes_in_level - 1) / 2

            for i, node in enumerate(nodes):
                pos[node] = (level, y_start + i)

        return pos
    
    def display_network(self):
        """
        Function to Visualize the Network Diagram.
        Uses Networkx and Matplotlib for plotting.
        """
        G = nx.Graph()
        plt.figure(figsize=(10,4))
        G.add_edges_from(self.edges)    
        
        color_edges = []
        l = 'O'
        for c in self.critical_path:
            color_edges.append((l,c))
            l = c
            
        color_edges.append((self.critical_path[-1],'T'))  
        
        # If the edge falls in critical path then color of edge will be red, else it will be black
        edges_colors = ['red' if ed in color_edges else 'black' for ed in G.edges()]
        
        initial_pos = {'O':(0,0),'T':(10,0)}

        fixed_nodes = ['O','T']

        pos = self.get_hierarchical_layout(G,'O')
        
        nx.draw(G,pos,with_labels=True,node_size=700,edge_color=edges_colors,arrows=True,arrowstyle='-|>',arrowsize=20)
        
        edge_durations = nx.get_edge_attributes(G,'duration')
        
        nx.draw_networkx_edge_labels(G,pos,edge_labels=edge_durations)

        plt.title("Network diagram with critical Path")
        plt.show()


    def network_summary(self):
        """
        Function to generate entire Network Summary including number of nodes, Activities, Probable paths, Critical Path, Total Project Duration and Edges
        """
        print("\n\n---------------Network Summary-----------------\n\n")
        print("Total number of Activities/Nodes : ",len(self.nodes))
        # print("Nodes : ",self.nodes)
        print("Nodes : ",end="")
        for c in self.nodes:
            print(c," ",end="")
            
        print("\nAll Probable Paths : ")
        for p in self.probable_paths:
            print(p)
        print("Critical Path : ",self.critical_path)
        print("Total project duration : ",self.total_project_duration)
        print("Duration unit :",self.duration_unit)
        print("Edges : ",self.edges)


class PERTMethod(CriticalPathMethod):
    """
    PERT (Program Evaluation and Review Technique) method using three-point estimation.
    Extends CriticalPathMethod with Optimistic, Most Likely, and Pessimistic time estimates.
    """
    def __init__(self):
        super().__init__()

    def add_activity(self, name, optimistic=0, most_likely=0, pessimistic=0):
        """
        Add a single activity with three-point estimates (PERT).

        Args:
            name (string): Name or alias of the activity
            optimistic (number): Optimistic time estimate (O)
            most_likely (number): Most likely time estimate (M)
            pessimistic (number): Pessimistic time estimate (P)

        The expected time (duration) is automatically computed as (O + 4M + P) / 6.
        """
        if name not in self.nodes:
            expected_time = (optimistic + 4 * most_likely + pessimistic) / 6
            self.nodes[name] = Node(name, expected_time, optimistic, most_likely, pessimistic)

    def add_activities_relations(self, activities, optimistic_times, most_likely_times, pessimistic_times, predecessors):
        """
        Add multiple activities with three-point PERT estimates and predecessor relations.

        Args:
            activities (list): List of all activity names
            optimistic_times (list): List of optimistic time estimates
            most_likely_times (list): List of most likely time estimates
            pessimistic_times (list): List of pessimistic time estimates
            predecessors (list): List of predecessor strings (comma-separated, '-' for none)
        """
        for i in range(len(activities)):
            self.add_activity(activities[i], optimistic_times[i], most_likely_times[i], pessimistic_times[i])
            self.add_relation(activities[i], predecessors[i])

    def get_expected_time(self, name):
        """Get the expected time (TE) for an activity."""
        if name in self.nodes:
            return self.nodes[name].expected_time
        return None

    def get_variance(self, name):
        """Get the variance for an activity."""
        if name in self.nodes:
            return self.nodes[name].variance
        return None

    def get_std_deviation(self, name):
        """Get the standard deviation for an activity."""
        if name in self.nodes:
            return self.nodes[name].std_deviation
        return None

    def get_project_variance(self):
        """
        Calculate the total project variance by summing variances along the critical path.
        """
        crit_path = self.critical_path if isinstance(self.critical_path[0], str) else []
        return sum(self.nodes[n].variance for n in crit_path
                   if n in self.nodes and self.nodes[n].variance > 0)

    def get_project_std_deviation(self):
        """Calculate the project standard deviation."""
        return self.get_project_variance() ** 0.5

    def find_critical_path(self, cur=None):
        """
        Find the critical path using expected times as durations.
        """
        self.total_project_duration = -1
        for probable_path in self.probable_paths:
            path_duration = sum(self.nodes[cur_node].expected_time for cur_node in probable_path)
            if path_duration > self.total_project_duration:
                self.critical_path = probable_path
                self.total_project_duration = path_duration
            elif path_duration == self.total_project_duration:
                if isinstance(self.critical_path, list):
                    self.critical_path.append(probable_path)

    def network_summary(self):
        """
        Generate the full network summary including PERT details.
        """
        super().network_summary()
        print("\n----------- PERT Three-Point Estimates -----------\n")
        for name in sorted(self.nodes):
            node = self.nodes[name]
            if name in ('O', 'T'):
                continue
            if node.optimistic or node.most_likely or node.pessimistic:
                print(f"Activity {name}:  O = {node.optimistic},  M = {node.most_likely},  "
                      f"P = {node.pessimistic}  |  "
                      f"TE = {node.expected_time:.2f},  Var = {node.variance:.4f},  SD = {node.std_deviation:.4f}")

        crit_path = self.critical_path if isinstance(self.critical_path, list) else []
        pert_nodes = [n for n in crit_path if n in self.nodes and n not in ('O', 'T')]
        if pert_nodes:
            proj_var = self.get_project_variance()
            proj_sd = self.get_project_std_deviation()
            print(f"\nProject Variance (critical path sum): {proj_var:.4f}")
            print(f"Project Standard Deviation: {proj_sd:.4f}")

    def display_pert_distribution(self):
        """
        Visualize the PERT Beta-PERT distribution for each activity.
        Shows a grouped bar chart of Optimistic, Most Likely, and Pessimistic estimates
        with Expected Time overlaid.
        """
        pert_activities = []
        for name in sorted(self.nodes):
            node = self.nodes[name]
            if name in ('O', 'T'):
                continue
            if node.optimistic or node.most_likely or node.pessimistic:
                pert_activities.append(name)

        if not pert_activities:
            print("No PERT activities to display.")
            return

        n_activities = len(pert_activities)
        x = np.arange(n_activities)
        width = 0.2

        optimistic_vals = [self.nodes[a].optimistic for a in pert_activities]
        most_likely_vals = [self.nodes[a].most_likely for a in pert_activities]
        pessimistic_vals = [self.nodes[a].pessimistic for a in pert_activities]
        expected_vals = [self.nodes[a].expected_time for a in pert_activities]

        fig, ax = plt.subplots(figsize=(max(8, n_activities * 1.5), 5))
        bars1 = ax.bar(x - 1.5*width, optimistic_vals, width, label='Optimistic (O)', color='green', alpha=0.7)
        bars2 = ax.bar(x - 0.5*width, most_likely_vals, width, label='Most Likely (M)', color='blue', alpha=0.7)
        bars3 = ax.bar(x + 0.5*width, pessimistic_vals, width, label='Pessimistic (P)', color='red', alpha=0.7)
        bars4 = ax.bar(x + 1.5*width, expected_vals, width, label='Expected (TE)', color='orange', alpha=0.9)

        ax.set_xlabel('Activities')
        ax.set_ylabel('Time')
        ax.set_title('PERT Three-Point Estimates and Expected Times')
        ax.set_xticks(x)
        ax.set_xticklabels(pert_activities)
        ax.legend()

        plt.tight_layout()
        plt.show()