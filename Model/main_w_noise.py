import numpy as np
import random
import networkx as nx
import mesa
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from numpy.typing import NDArray
import matplotlib.pyplot as plt
import json
import sys

def parse_block_data(file_name: str) -> tuple[NDArray, list[tuple[int, int]], list[tuple[int, int]], int]:
    """
    Parse a JSON-like string into a Python dictionary representing block data.

    Args:
        block_data (JSON): The JSON input.

    Returns:
        dict: Parsed block data.
    """

    with open(file_name, 'r') as f:
        block_data = json.load(f)
        attribute_grid = np.zeros((block_data["gridSize"], block_data["gridSize"]))
        spawns = []
        exits = []
        for key, value in block_data["data"].items():
            # Convert string keys like "0,0" to tuple keys like (0, 0)
            x, y = tuple(map(int, key.split(',')))
            attribute_grid[y, x] = value["type"]
            if value["associatedExit"] is not None:
                ex, ey = value["associatedExit"]
                spawns.append((y, x))
                exits.append((ey, ex))

        return attribute_grid, spawns, exits, block_data["gridSize"]


# Define attributes for grid locations
attributes = {'wall': 2, 'open': 0, 'social': 4, 'work': 3, 'both': 5}

file_name = r"C:\Users\nickc\OneDrive\Desktop\Purdue Files\4_Senior Year\Fall 2024\HONR 313\Final_pres\WALC_map.json"
attribute_grid, spawn_points, exit_points, side_length = parse_block_data(file_name) #sys.argv[1]

width = side_length
height = side_length

print(attribute_grid, spawn_points, exit_points)

NOISE_DECAY = 0.1


class IndoorModel(mesa.Model):
    """
    A model that simulates student movement, socializing, and studying
    in an indoor environment.
    """

    def __init__(self, num_agents, width, height, seed=None):
        super().__init__(seed=seed)
        self.num_agents = num_agents
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.graph = self.build_graph()
        self.noise = np.zeros((width, height))
        self.width = width
        self.height = height

        self.passages = np.zeros((width, height), dtype=int)

        # Create agents and place them at spawn points
        for _ in range(self.num_agents):
            agent = StudentAgent(self)
            spawn_point = random.choice(spawn_points)
            exit_point = random.choice(exit_points)
            agent.destination_stack.append(exit_point)

            self.grid.place_agent(agent, spawn_point)
            self.schedule.add(agent)

    def build_graph(self):
        """Converts the grid to a NetworkX graph for pathfinding."""
        G = nx.grid_2d_graph(width, height)
        for x in range(width):
            for y in range(height):
                if attribute_grid[x, y] == attributes['wall']:
                    G.remove_node((x, y))
        return G

    def step(self):
        """Advance the model by one step."""
        self.noise = np.maximum(self.noise - NOISE_DECAY, 0.0)
        self.schedule.step()

    def add_noise(self, cx: int, cy: int, noise: float = 1.0):
        center = [cx, cy]
        sigma = [noise * 3, noise * 3]
        x = np.arange(self.width)
        y = np.arange(self.height)
        x_grid, y_grid = np.meshgrid(x, y)

        # clamp example, for my notes
        #max(0, min(1, value))  # Clamp to 0-1

        # Gaussian equation
        gaussian = noise * np.exp(
            -((x_grid - center[1])**2 / (2 * sigma[1]**2) + (y_grid - center[0])**2 / (2 * sigma[0]**2))
        )
        self.noise = np.clip(self.noise + gaussian, 0, 1)

    def get_noise_at(self, pos):
        x, y = map(int, pos) 
        return self.noise[x, y]


class StudentAgent(mesa.Agent):
    """
    A student agent that can look for goals, move towards them, and perform
    socializing or studying behaviors.
    """

    def __init__(self, model):
        super().__init__(model)
        self.focus = 100
        self.has_target = False
        self.destination_stack = []
        self.social=random.randint(0,100)               #added by NBC
        self.study=bool(random.randint(0,1))            #added by NBC
        #self.loudness=random.uniform(0,1)               #added by NBC
        self.loudness=random.randint(0,100)
        self.distractibility = 2

    def look(self):
        """
        Scan the environment for a target (e.g., a social or work area)
        and update the destination stack if a goal is found.
        """
        theta = random.randint(0, 359)
        y_direction = np.sin(np.radians(theta))
        x_direction = np.cos(np.radians(theta))
        mult = min(y_direction, x_direction)
        if y_direction != 0:
            if x_direction != 0:
                y_direction = int(y_direction / mult)
                x_direction = int(x_direction / mult)
            else:
                x_direction = 0
                y_direction = 1
        else:
            x_direction = 1
            y_direction = 0
        result = plot_line(self.pos, (x_direction, y_direction))
        if result:
            self.destination_stack.append(result)
            self.has_target = True

    def move(self):
        """
        Move towards the current target using A* pathfinding.
        """
        if not self.destination_stack:
            return  # No target to move towards

        target = self.destination_stack[-1]
        try:
            cur_best = float('inf')
            next_move = self.pos
            # for _dir in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            #     _start_pos = (self.pos[0] + _dir[0], self.pos[1] + _dir[1])
            #     if _start_pos in self.model.graph and target in self.model.graph:
            #         try:
            #             path = nx.astar_path(self.model.graph, _start_pos, target)
            #             if len(path) > 1:
            #                 if len(path) < cur_best:
            #                     cur_best = len(path)
            #                     next_move = path[1]
            #                 elif len(path) == cur_best and random.random() < 0.5:
            #                     next_move = path[1]
            #         except nx.NetworkXNoPath:
            #             continue
            #     else:
            #         continue

            path = nx.dijkstra_path(self.model.graph, self.pos, target)

            if len(path) < 2:
                next_move = path[0]
            else:
                next_move = path[1]
            self.model.grid.move_agent(self, next_move)

            # Track the space passed through
            x, y = next_move
            self.model.passages[x, y] += 1
            if next_move in spawn_points:
                self.model.grid.remove_agent(self)  # Remove from the grid
                self.model.schedule.remove(self)

        except nx.NetworkXNoPath:
            self.has_target = False  # Clear target if no path exists

    def perform_action(self):
        """
        Perform socializing or studying if at a valid location.
        """
        if self.pos is None:
            return
        cell_type = attribute_grid[self.pos[0], self.pos[1]]
        neighbors = self.model.grid.get_neighbors(
                self.pos,  # Position of the agent
                moore=True,
                include_center=False,
                radius=self.loudness
        )
        for neighbor in neighbors:
            #   print(f"Agent {self.unique_id} is distracting agent {neighbor.unique_id}")
            neighbor.focus -= neighbor.distractibility

    def make_noise(self):
        if self.pos is not None:
            cx, cy = self.pos                      
            self.model.add_noise(cx,cy,self.loudness)                 #added by nbc
            env_noise = self.model.get_noise_at(self.pos)             #added by NBC
            if env_noise > 0.7:                            
                self.focus -= 5
            elif env_noise > 0.6:
                self.focus -= 4
            elif env_noise > 0.5:                            
                self.focus -= 3
            elif env_noise > 0.4:
                self.focus -= 2
            else:
                self.focus -= 1
        if self.pos is None:
            return

    def step(self):
        """
        The agent's behavior at each step: look, move, perform action, and deplete focus.
        """

        if not self.has_target or self.study == True:
            self.look()
        self.move()
        self.make_noise()
        self.perform_action()

        if self.focus <= 0 or self.study == False:
            print(f"Agent {self.unique_id} is heading to exit.")
            self.destination_stack.append(spawn_points[1])  # Go to exit


def plot_line(location, direction):
    """
    Simulate a line of sight to find a target goal in a given direction.

    Args:
        location: Current position of the agent.
        direction: Tuple representing direction (dx, dy).

    Returns:
        Coordinates of the target goal if found, otherwise None.
    """
    x, y = location
    dx, dy = direction
    while 0 <= x < width and 0 <= y < height:
        loc_type = attribute_grid[x, y]
        if loc_type == attributes['wall']:
            return None
        if loc_type in [attributes['social'], attributes['work']]:
            return (x, y)
        x += dx
        y += dy
    return None


if __name__ == "__main__":
    model = IndoorModel(num_agents=40, width=width, height=height)
    for i in range(100):  # Simulate 10 steps
        print(f"Step {i + 1}")
        model.step()

    print(model.passages)

    plt.imshow(model.passages, cmap="viridis", interpolation="none")
    plt.colorbar(label="Passages Count")
    plt.title("Agent Passage Heatmap")
    plt.show()