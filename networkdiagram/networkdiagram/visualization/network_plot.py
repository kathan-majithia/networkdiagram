from typing import Dict, List, Set, Tuple
from collections import deque

import networkx as nx
import matplotlib.pyplot as plt


def get_hierarchical_layout(graph: nx.Graph, start_node: str) -> Dict[str, Tuple[float, float]]:
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


def display_network(cpm) -> None:
    """
    Function to Visualize the Network Diagram.
    Uses Networkx and Matplotlib for plotting.
    """
    cpm.get_edges()
    
    G = nx.Graph()
    plt.figure(figsize=(10, 4))
    
    # Add edges without duration for graph creation
    edges_without_duration: List[Tuple[str, str]] = [(e[0], e[1]) for e in cpm.edges]
    G.add_edges_from(edges_without_duration)    
    
    color_edges: List[Tuple[str, str]] = []
    if cpm.critical_path:
        l = 'O'
        for c in cpm.critical_path:
            color_edges.append((l, c))
            l = c
        color_edges.append((cpm.critical_path[-1], 'T'))  
    
    # If the edge falls in critical path then color of edge will be red, else it will be black
    edges_colors: List[str] = ['red' if (ed[0], ed[1]) in color_edges or (ed[1], ed[0]) in color_edges else 'black' for ed in G.edges()]
    
    initial_pos: Dict[str, Tuple[float, float]] = {'O': (0, 0), 'T': (10, 0)}
    fixed_nodes: List[str] = ['O', 'T']

    pos = get_hierarchical_layout(G, 'O')
    
    labels: Dict[str, str] = {}
    for node in G.nodes():
        if node in cpm.nodes:
            n = cpm.nodes[node]
            labels[node] = f"{node}\nES:{n.early_start} EF:{n.early_finish}\nLS:{n.latest_start} LF:{n.latest_finish}"
        else:
            labels[node] = str(node)
    
    nx.draw(G, pos, labels=labels, with_labels=True, node_size=2500, font_size=8, 
            edge_color=edges_colors, arrows=True, arrowstyle='-|>', arrowsize=20)
    
    # Create edge label dictionary
    edge_durations: Dict[Tuple[str, str], str] = {}
    for edge in cpm.edges:
        edge_durations[(edge[0], edge[1])] = str(edge[2]['duration'])
    
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_durations)

    plt.title("Network diagram with critical Path")
    plt.show()
