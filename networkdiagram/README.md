# NetworkDiagram

A lightweight Python library for creating Project Network Diagrams (CPM/PERT), calculating paths, and visualizing activity dependencies using NetworkX and Matplotlib.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Easy Node Management**: Add activities with durations and string-based predecessor lists (e.g., `"A,B"`).
- **Automatic Pathfinding**: Detects all probable paths from Start to End.
- **Visualisation**: Generates directed graphs with arrows and duration labels using `matplotlib`.
- **CPM Ready**: Built on a node structure supporting Probable Paths, Critical Path.

# Publisher
- **Name**: Kathan Majithia
- **Contact**: kathanmajithia@gmail.com

## Dependencies

To use the visualization features, you must have the following libraries installed:

* **networkx** (for graph theory and structure)
* **matplotlib** (for plotting the diagram)

## Installation
pip install networkdiagram

```bash

from networkdiagram import CriticalPathMethod

cpm = CriticalPathMethodk()

activities = ['A','B','C','D']
durations = [2,5,4,2]
predecessors = ['-','A','B','B,C']

cpm.add_activity('O',0)
cpm.add_activities_relations(activities,durations,predecessors)