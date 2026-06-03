import networkx as nx
import matplotlib.pyplot as plt
from collections import deque

class Node:
    def __init__(self,name,duration=0):
        self.name = name
        self.duration = duration
        self.predecessors = []
        self.successors = [] 
        self.early_start = self.early_finish = self.latest_start = self.latest_finish = 0 
        # Added float attributes
        self.total_float = 0
        self.free_float = 0
        self.independent_float = 0
        
    def add_successor(self,node):
        self.successors.append(node)
        node.predecessors.append(self)
        
    def node_summary(self):
        return f"Name : {self.name}, Duration : {self.duration}, Successor : {self.successors}"
        
class CriticalPathMethod:
    def __init__(self):
        self.nodes = {} 
        self.probable_paths = [] 
        self.total_project_duration = -1 
        self.duration_unit = "days" 
        self.critical_path = [] 
        self.edges = [] 
        
    def add_activity(self,name,duration):
        if name not in self.nodes:
            self.nodes[name] = Node(name,duration)
            
    def add_activities_relations(self,activities,durations,predecessors):
        durations.append(0) 
        for i in range(0,len(activities)):
            self.add_activity(activities[i],durations[i+1])
            self.add_relation(activities[i],predecessors[i])
            
    def add_relation(self,cur,predecessors):
        for p in predecessors.split(','):
            p = p.strip()
            if p == '-':
                parent = self.nodes['O']
                parent.successors.append(cur)
            elif p in self.nodes:
                parent = self.nodes[p]
                parent.successors.append(cur)
                
    # NEW METHOD ADDED HERE
    def calculate_floats(self):
        """Calculates Total, Free, and Independent Float for all nodes."""
        for name, node in self.nodes.items():
            # Total Float = LS - ES or LF - EF
            node.total_float = node.latest_finish - node.early_finish
            
            # Free Float = Min(ES of successors) - EF of current
            if not node.successors:
                node.free_float = 0
            else:
                successor_es = [self.nodes[s].early_start for s in node.successors if s in self.nodes]
                node.free_float = min(successor_es) - node.early_finish
            
            # Independent Float = Max(0, Min(ES successors) - Max(LF predecessors) - Duration)
            if not node.predecessors or not node.successors:
                node.independent_float = 0
            else:
                min_successor_es = min([self.nodes[s].early_start for s in node.successors if s in self.nodes])
                max_predecessor_lf = max([p.latest_finish for p in node.predecessors])
                node.independent_float = max(0, min_successor_es - max_predecessor_lf - node.duration)

    def find_probable_paths(self,cur=None,path=""):
        if cur is None:
            if 'O' in self.nodes:
                cur = self.nodes['O']
            else: return
        path +=  str(cur.name)
        if len(cur.successors) == 0:
            path = [p for p in path]
            self.probable_paths.append(path)
            return
        for c in cur.successors:
            if c in self.nodes:
                self.find_probable_paths(self.nodes[c],path)
    
    def find_critical_path(self,cur=None):
        for probable_path in self.probable_paths:
            duration = sum(self.nodes[cur_node].duration for cur_node in probable_path if cur_node in self.nodes)
            if(duration > self.total_project_duration):
                self.critical_path = probable_path
                self.total_project_duration = duration
            elif(duration == self.total_project_duration):
                self.critical_path.append(probable_path)
                
    def network_summary(self):
        print("\n\n---------------Network Summary-----------------\n\n")
        print("Nodes : ",list(self.nodes.keys()))
        print("Critical Path : ",self.critical_path)
        print("Total project duration : ",self.total_project_duration)
        
        # Added float reporting
        print("\n--- Float Calculations ---")
        for name, node in self.nodes.items():
            print(f"Node {name}: Total Float={node.total_float}, Free Float={node.free_float}, Ind. Float={node.independent_float}")

    # ... (Keep your existing display_network and get_hierarchical_layout methods here)