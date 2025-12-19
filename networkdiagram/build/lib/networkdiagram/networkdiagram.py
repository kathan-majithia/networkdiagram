import networkx as nx
import matplotlib.pyplot as plt
from collections import deque

class Node:
    def __init__(self,name,duration=0):
        """
        Constructor for declaring a new Node or Activity

        Args:
            name (string): Name of the activity usually single character
            duration (__type__, optional): Duration of the activity. Defaults to 0.
        """
        self.name = name
        self.duration = duration
        self.predecessors = []
        self.successors = [] # Tells which activities can start once the current activity is finished
        self.early_start = self.early_finish = self.latest_start = self.latest_finish = 0 # Pending
        
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
            for suc in self.nodes[node].successors:
                    self.edges.append((self.nodes[node].name,suc,{'duration':self.nodes[node].duration}))
                
            if suc == []:
                self.edges.append((self.nodes[node].name,'T',{'duration':0}))
    
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