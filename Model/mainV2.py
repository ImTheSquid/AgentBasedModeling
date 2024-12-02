import numpy as np
import random
import networkx as nx
import mesa
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import matplotlib.pyplot as plt

# Define attributes for grid locations
attributes = {'wall': 1, 'open': 0, 'social': 2, 'work': 3, 'both': 4}

# Grid dimensions and layout
# Would need to reintegrate with the JSON parser
w, h = 10, 10
attribute_grid = np.array([
    [0, 0, 0, 0, 0, 1, 3, 3, 3, 3],
    [0, 3, 3, 3, 0, 1, 3, 0, 0, 3],
    [0, 3, 3, 3, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 2, 2, 2, 2, 0, 0, 0],
    [0, 0, 0, 2, 2, 2, 2, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
])
spawn_points = [(0, 0), (9, 0)]
exit_points = [(9, 9), (0, 9)]


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

        self.passages = np.zeros((width, height), dtype=int)

        # Create agents and place them at spawn points
        for _ in range(self.num_agents):
            agent = StudentAgent(self.next_id(), self)
            spawn_point = random.choice(spawn_points)
            exit_point = random.choice(exit_points)
            agent.destination_stack.append(exit_point)

            self.grid.place_agent(agent, spawn_point)
            self.schedule.add(agent)

    def build_graph(self):
        """Converts the grid to a NetworkX graph for pathfinding."""
        G = nx.grid_2d_graph(w, h)
        for x in range(w):
            for y in range(h):
                if attribute_grid[x, y] == attributes['wall']:
                    G.remove_node((x, y))
        return G

    def step(self):
        """Advance the model by one step."""
        self.schedule.step()


class StudentAgent(mesa.Agent):
    """
    A student agent that can look for goals, move towards them, and perform
    socializing or studying behaviors.
    """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.focus = 100
        self.has_target = False
        self.destination_stack = []
        self.social=random.randint(0,100),               #added by NBC
        self.study=bool(random.randint(0,1)),            #added by NBC
        self.friendship_group=random.randint(0,10),      #added by NBC
        self.loudness=random.randint(0,100),             #added by NBC
        self.leave_need=random.randint(0,100),           #added by NBC

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
            for _dir in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                _start_pos = (self.pos[0] + _dir[0], self.pos[1] + _dir[1])
                if _start_pos in self.model.graph and target in self.model.graph:
                    try:
                        path = nx.astar_path(self.model.graph, _start_pos, target)
                        if len(path) > 1:
                            if len(path) < cur_best:
                                cur_best = len(path)
                                next_move = path[1]
                            elif len(path) == cur_best and random.random() < 0.5:
                                next_move = path[1]
                    except nx.NetworkXNoPath:
                        continue
                else:
                    continue

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
        cell_type = attribute_grid[self.pos[0], self.pos[1]]
        if cell_type == attributes['social']:
            print(f"Agent {self.unique_id} is socializing at {self.pos}")
        elif cell_type == attributes['work']:
            print(f"Agent {self.unique_id} is studying at {self.pos}")

    def step(self):
        """
        The agent's behavior at each step: look, move, perform action, and deplete focus.
        """

        if not self.has_target or self.study == True:
            self.look()
        self.move()
        self.perform_action()
        self.focus -= 1
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
    while 0 <= x < w and 0 <= y < h:
        loc_type = attribute_grid[x, y]
        if loc_type == attributes['wall']:
            return None
        if loc_type in [attributes['social'], attributes['work']]:
            return (x, y)
        x += dx
        y += dy
    return None


if __name__ == "__main__":
    model = IndoorModel(num_agents=40, width=w, height=h)
    for i in range(100):  # Simulate 10 steps
        print(f"Step {i + 1}")
        model.step()

    print(model.passages)

    plt.imshow(model.passages, cmap="viridis", interpolation="none")
    plt.colorbar(label="Passages Count")
    plt.title("Agent Passage Heatmap")
    plt.show()