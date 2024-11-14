import numpy as np
import mesa
import random

# sample grid, definitely will change once gui is in place
width = 10
height = 10
attribute_grid = np.zeros((width, height))

# 0 is open space
# 1 is wall
# 2 is social space
# 3 is work space
# 4 is both
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

# spawn points for agents to start (entrances)
spawn_points = [(9, 0), (9, 9)]

# should be adjusted based off of what different features are labeled as
attributes = {
    'wall': 1,
    'open': 0,
    'social': 2,
    'work': 3,
    'both': 4
}

def plotLine(location, direction, goal='work') -> tuple | None:
    """
    Looks from loc1 to loc2 using Bresenham's line algorithm
    in an attempt to find goal

    Assumes access to a numpy array attribute_grid, although
    this can be easily changed if desired

    Args:
        location - tuple representing xy coordinates
        direction - tuple representing direction
    Returns:
        (x, y) location of goal if found, otherwise None
    """
    dx = direction[0]
    dy = direction[1]
    D = 2 * dy - dx
    y = location[1]
    x = location[0]
    
    while True:
        # can put code relating to looking at walls or finding a target here
        loc_type = attribute_grid[x, y]
        if loc_type == attributes['wall']:
            return None
        if loc_type[0] < 0 or loc_type[0] >= width or loc_type[1] < 0 or loc_type[1] >= height:
            return None
        if loc_type == attributes[goal]:
            return (x, y)

        if D > 0:
            y = y + 1
            D = D - 2 * dx
            
        D = D + 2 * dy
    
        x += 1

class StudentAgent(mesa.Agent):
    """An agent"""

    def __init__(self, model):
        super().__init__(model)
        self.focus = 100
        self.destinationStack = []

    def look(self):
        # choose random direction
        theta = random.randInt(0, 359)
        y_direction = np.sin(theta * np.pi / 180)
        x_direction = np.cos(theta * np.pi / 180)
        result = plotLine(self.pos, (x_direction, y_direction))
        if result:
            # found target
            self.destinationStack.append(result)

    def move(self):
        # very rudimentary
        # TODO: change this mess
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def tick(self):
        self.focus -= 1
      

class RoomModel(mesa.Model):
    """A model with some number of agents."""

    def __init__(self, n, width, height,seed=None):
        super().__init__(seed=seed)
        self.num_agents = n
        self.grid = mesa.space.SingleGrid(width, height, True)
        
        # Create agents
        for _ in range(self.num_agents):
            a = MoneyAgent(self)
            # Add the agent to a random grid cell
            spawn_point = spawn_points[0]
            self.grid.place_agent(a, spawn_point)


    def add_agents(self, n):
        self.num_agents += n
        for _ in range(n):
            a = StudentAgent(self)


    def step(self):
        self.datacollector.collect(self)
        # can use shuffle_do or do to randomize order
        self.agents.shuffle_do("move")


if __name__=="__main__":
    model = RoomModel(10)
    model.step()