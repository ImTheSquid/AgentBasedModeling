"""
Indoor Movement Model
===================
A Mesa implementation of an Indoor movement model.
Uses numpy arrays to represent vectors.
"""

import numpy as np
import json
import networkx as nx
from mesa import Model
#from mesa.examples.basic.boid_flockers.agents import Boid
from mesa.space import ContinuousSpace
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector

class IndoorModel(Model):
    """Overall model class. Handles agent creation, entrance selection, 
       update space attractiveness, removing agents, time stepping, 
       placement, and scheduling."""

    def __init__(
        # Figure out what we want to initialize
        self,
        population=5,
        width=100,          #updated in get_space
        height=100,         #updated in get_space
        # Agent Attributes
        speed=1,
        vision=10,
        separation=2,
        cohere=0.03,
        separate=0.015,
        match=0.05,
        social=0.15,            #added by NBC
        study=0.4,              #added by NBC
        focus=0.1,              #added by NBC
        friendship_group=1,     #added by NBC
        loudness=0.2,           #added by NBC
        leave_need=0.05,        #added by NBC
        seed=None,              
    ):
        """Create a new ABM student model.

        Args:
            population: Number of students in the simulation (default: 100)
            width: Width of the space (default: 100)
            height: Height of the space (default: 100)
            speed: How fast the students move (default: 1)
            vision: How far each Boid can see (default: 10)
            separation: Minimum distance between students (default: 2)
            cohere: Weight of cohesion behavior (default: 0.03)
            separate: Weight of separation behavior (default: 0.015)
            match: Weight of alignment behavior (default: 0.05)
            
            
            
            
            
            seed: Random seed for reproducibility (default: None)
        """
        super().__init__(seed=seed)

        # Model Parameters
        self.population = population
        self.vision = vision
        self.speed = speed
        self.separation = separation

        # Set up the space
        input_string = ""
        block_data = parse_block_data(input_string)
        width = #insert width from block_data
        height = #insert height from block_data
        self.space = SingleGrid(width, height, torus=True)       
 
        self.entrance_blocks = [
            tuple(map(int, coord.split(","))) for coord, attr in space.items() if attr["type"] == "entrance"
        ]

        # Store "flocking" weights - Need?
        self.factors = {"cohere": cohere, "separate": separate, "match": match}

        # Create and place the student agents
        self.make_agents()

        # For tracking statistics
        # Take Philip functions for movement
        self.average_heading = None
        self.update_average_heading()

    def parse_block_data(input_string):
        """
        Parse a JSON-like string into a Python dictionary representing block data.
        
        Args:
            input_string (str): The JSON-like string input.
            
        Returns:
            dict: Parsed block data.
        """
        # Parse the input string into a Python dictionary
        block_data = json.loads(input_string)
        
        processed_block_data = {}
        for key, value in block_data.items():
            # Convert string keys like "0,0" to tuple keys like (0, 0)
            coords = tuple(map(int, key.split(',')))
            processed_block_data[coords] = value
        
        return processed_block_data

    # def make_agents(self):
    #     """Create and place all Boid agents randomly in the space."""
    #     for _ in range(self.population):
    #         # Random position
    #         x = self.random.random() * self.space.x_max
    #         y = self.random.random() * self.space.y_max
    #         pos = np.array((x, y))

    #         # Random initial direction
    #         direction = np.random.random(2) * 2 - 1  # Random vector between -1 and 1
    #         direction /= np.linalg.norm(direction)  # Normalize

    #         # Create and place the Boid
    #         boid = Boid(
    #             model=self,
    #             speed=self.speed,
    #             direction=direction,
    #             vision=self.vision,
    #             separation=self.separation,
    #             **self.factors,
    #         )
    #         self.space.place_agent(boid, pos)

    def make_agents(self):
        """Create and place initial # of student agents at entrances of the space."""
        for _ in range(self.population):
            # Entrance position
            entrance_pos = self.random.choice(self.entrance_blocks)

            # Initial direction is "straight" from the entrance
            direction = calculate_valid_direction(entrance_pos)

            # Create and place the Boid
            boid = Boid(
                model=self,
                speed=self.speed,
                direction=direction,
                vision=self.vision,
                separation=self.separation,
                **self.factors,
            )
            self.space.place_agent(boid, pos)

    # def update_average_heading(self):
    #     """Calculate the average heading (direction) of all Boids."""
    #     if not self.agents:
    #         self.average_heading = 0
    #         return

    #     headings = np.array([agent.direction for agent in self.agents])
    #     mean_heading = np.mean(headings, axis=0)
    #     self.average_heading = np.arctan2(mean_heading[1], mean_heading[0])

    def calculate_valid_direction(current_pos, space, block_data):
        """
        Calculate a valid direction for an agent to move, avoiding walls, exits,
        and boundaries.
        
        entrance_pos: tuple - (x, y) coordinates of the entrance block
        space: MultiGrid or ContinuousSpace - the simulation space
        block_data: dict - a dictionary with block types keyed by coordinates
        """
        x, y = current_pos

        # Directions: (dx, dy) for right, up, left, down
        directions = {
            "right": (1, 0),
            "up": (0, 1),
            "left": (-1, 0),
            "down": (0, -1)
        }

        valid_directions = []

        # Check each adjacent block
        for name, (dx, dy) in directions.items():
            neighbor_pos = (x + dx, y + dy)

            # Check if neighbor position is within the bounds of the space
            if space.out_of_bounds(neighbor_pos):
                continue

            if warn_if_agent_has_position_already == 1:     # need to learn how this warning works better, mesa doc
                continue

            # Check if neighbor is a wall or other restricted type
            block_type = block_data.get(neighbor_pos, {}).get("type", "empty")
            if block_type not in ["wall", "exit"]:
                valid_directions.append((dx, dy))

        # Avoid cases where no valid directions are found
        if not valid_directions:
            return np.array([0, 0])  # No movement (stay in place)

        # Chooses a random valid movement (FIX THIS)
        #   - We want the agent to move towards friends if they see them
        #   - Agent movement might not necessarily be random (usually towards exit if passing through)
        direction = space.random.choice(valid_directions)
        return np.array(direction)

    def step(self):
        # Get the agent's current position
        current_pos = self.pos

        # Calculate a valid direction based on surroundings
        valid_direction = calculate_valid_direction(current_pos, self.model.space, self.model.block_data)

        # Move the agent
        new_pos = (current_pos[0] + valid_direction[0], current_pos[1] + valid_direction[1]) # x and y movement in one step??
        if not self.model.space.out_of_bounds(new_pos) and not self.model.space.get_cell_list_contents([new_pos]):
            self.model.space.move_agent(self, new_pos)