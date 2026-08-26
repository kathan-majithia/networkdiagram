from typing import List, Optional


class Node:
    """Represents an activity node in the network diagram."""
    
    def __init__(
        self,
        name: str,
        duration: float = 0,
        normal_cost: float = 0,
        crash_cost: float = 0,
        crash_duration: Optional[float] = None,
    ) -> None:
        """
        Constructor for declaring a new Node or Activity

        Args:
            name (str): Name of the activity usually single character
            duration (float, optional): Normal duration of the activity. Defaults to 0.
            normal_cost (float): Cost at normal duration. Defaults to 0.
            crash_cost (float): Cost at minimum duration. Defaults to 0.
            crash_duration (float): Minimum possible duration. Defaults to normal duration.
            
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
        self.normal_duration: float = duration
        self.crash_duration: float = crash_duration if crash_duration is not None else duration
        self.normal_cost: float = normal_cost
        self.crash_cost: float = crash_cost
        self.predecessors: List[str] = []
        self.successors: List[str] = []  # Tells which activities can start once the current activity is finished
        self.early_start: float = 0
        self.early_finish: float = 0
        self.latest_start: float = 0
        self.latest_finish: float = 0
        
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

    def cost_slope(self) -> float:
        """
        Cost Slope = (Crash Cost - Normal Cost) / (Normal Duration - Crash Duration)
        Tells how much extra it costs to reduce duration by 1 unit.
        Returns infinity if activity cannot be crashed further.

        Returns:
            float: Cost per unit time reduction
        """
        if self.normal_duration <= self.crash_duration:
            return float('inf')
        return (self.crash_cost - self.normal_cost) / (self.normal_duration - self.crash_duration)

    def can_be_crashed(self) -> bool:
        """
        Checks if this activity can still be crashed.
        Activity cannot go below its crash_duration.

        Returns:
            bool: True if current duration > crash_duration
        """
        return self.duration > self.crash_duration
        
    def __repr__(self) -> str:
        """String representation of the node."""
        return f"Node(name='{self.name}', duration={self.duration})"
