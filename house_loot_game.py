import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
from collections import deque
from math import floor

class HouseLootGame:
    def __init__(self, parent, game):
        self.window = tk.Toplevel(parent)
        self.window.title("House Looting")
        self.window.geometry("400x400")

        self.game = game
        self.canvas = tk.Canvas(self.window, width=300, height=300, bg='black')
        self.canvas.pack(pady=20)

        self.cell_size = 20
        self.grid_width = 15
        self.grid_height = 15

        self.player_pos = [1, 1]
        self.guards = []
        self.guard_types = []  # 'chase' or 'patrol'
        self.guard_patrol_points = []  # For patrol guards
        self.trinkets = []
        self.walls = []
        self.exits = []
        self.collected_trinkets = 0
        self.total_trinkets = random.randint(5, 10)

        self.setup_game()

        # Bind keys
        self.window.bind('<Up>', lambda e: self.move_player(0, -1))
        self.window.bind('<Down>', lambda e: self.move_player(0, 1))
        self.window.bind('<Left>', lambda e: self.move_player(-1, 0))
        self.window.bind('<Right>', lambda e: self.move_player(1, 0))
        self.window.bind('<Escape>', lambda e: self.end_game(False))

        # Start guard movement
        self.move_guards()

    def find_path_to_player(self, guard_pos):
        # BFS pathfinding with weighted directions based on player position
        queue = deque([(guard_pos, [])])
        visited = {tuple(guard_pos)}

        # Calculate direction to player for weighting
        px, py = self.player_pos
        gx, gy = guard_pos
        preferred_dx = 1 if px > gx else -1 if px < gx else 0
        preferred_dy = 1 if py > gy else -1 if py < gy else 0

        while queue:
            current, path = queue.popleft()
            if current == self.player_pos:
                return path

            # Prioritize directions that move towards the player
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            directions.sort(key=lambda d: (
                abs(d[0] - preferred_dx) + abs(d[1] - preferred_dy)
            ))

            for dx, dy in directions:
                next_pos = [current[0] + dx, current[1] + dy]
                if (tuple(next_pos) not in visited and 
                    next_pos not in self.walls and 
                    0 <= next_pos[0] < self.grid_width and 
                    0 <= next_pos[1] < self.grid_height):
                    visited.add(tuple(next_pos))
                    new_path = path + [next_pos]
                    queue.append((next_pos, new_path))

        return None

    def generate_patrol_points(self):
        points = []
        for _ in range(4):  # Generate 4 patrol points for each patrol guard
            while True:
                x = random.randint(1, self.grid_width-2)
                y = random.randint(1, self.grid_height-2)
                if [x, y] not in self.walls and [x, y] not in points:
                    points.append([x, y])
                    break
        return points

    def setup_game(self):
        self.generate_pacman_style_maze()

        # Ensure starting position is clear
        self.player_pos = [1, 1]
        while self.player_pos in self.walls:
            if [1, 1] in self.walls:
                self.walls.remove([1, 1])

        # Place trinkets in open spaces
        while len(self.trinkets) < self.total_trinkets:
            x = random.randint(1, self.grid_width-2)
            y = random.randint(1, self.grid_height-2)
            if [x, y] not in self.walls and [x, y] != self.player_pos and [x, y] not in self.trinkets:
                self.trinkets.append([x, y])

        # Place guards with different behaviors
        num_guards = 2
        for _ in range(num_guards):
            while True:
                x = random.randint(1, self.grid_width-2)
                y = random.randint(1, self.grid_height-2)
                if [x, y] not in self.walls and [x, y] not in self.trinkets and [x, y] != self.player_pos:
                    self.guards.append([x, y])
                    # Assign guard type (50% chance for each type)
                    guard_type = 'chase' if random.random() < 0.5 else 'patrol'
                    self.guard_types.append(guard_type)
                    if guard_type == 'patrol':
                        self.guard_patrol_points.append(self.generate_patrol_points())
                    else:
                        self.guard_patrol_points.append([])
                    break

        self.draw_game()

    def move_guards(self):
        for i, (guard, guard_type) in enumerate(zip(self.guards, self.guard_types)):
            if guard_type == 'chase':
                # Chasing guard - directly pursue player
                path = self.find_path_to_player(guard)
                if path and len(path) > 1:
                    self.guards[i] = path[0]

            else:  # 'patrol' type
                # Patrol guard - move between patrol points unless player is very close
                player_distance = abs(guard[0] - self.player_pos[0]) + abs(guard[1] - self.player_pos[1])

                if player_distance <= 3:  # Switch to chase mode if player is close
                    path = self.find_path_to_player(guard)
                    if path and len(path) > 1:
                        self.guards[i] = path[0]
                else:
                    # Continue patrol
                    patrol_points = self.guard_patrol_points[i]
                    if patrol_points:
                        current_target = patrol_points[0]
                        if guard == current_target:
                            # Move to next patrol point
                            patrol_points.append(patrol_points.pop(0))
                            current_target = patrol_points[0]

                        # Find path to current patrol point
                        path = self.find_path_to_player(guard)  # Reuse pathfinding logic
                        if path and len(path) > 1:
                            self.guards[i] = path[0]

        # Check for player collision
        if self.player_pos in self.guards:
            self.end_game(False)
            return

        self.draw_game()
        self.window.after(500, self.move_guards)  # Move guards every 500ms

    def generate_pacman_style_maze(self):
        # Initialize grid with walls
        self.walls = []

        # Create a grid pattern with corridors
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                # Add walls at the borders
                if (x == 0 or x == self.grid_width-1 or 
                    y == 0 or y == self.grid_height-1):
                    self.walls.append([x, y])
                # Create a pattern of walls
                elif x % 2 == 0 and y % 2 == 0:
                    # Add some randomness to wall placement
                    if random.random() < 0.7:  # 70% chance of wall
                        self.walls.append([x, y])

        # Create exits
        possible_exits = []
        for i in range(1, self.grid_width-1):
            if [i, 1] not in self.walls:
                possible_exits.append([i, 0])
            if [i, self.grid_height-2] not in self.walls:
                possible_exits.append([i, self.grid_height-1])
        for i in range(1, self.grid_height-1):
            if [1, i] not in self.walls:
                possible_exits.append([0, i])
            if [self.grid_width-2, i] not in self.walls:
                possible_exits.append([self.grid_width-1, i])

        # Select 2-3 exits
        num_exits = random.randint(2, 3)
        self.exits = random.sample(possible_exits, min(len(possible_exits), num_exits))
        for exit_pos in self.exits:
            if exit_pos in self.walls:
                self.walls.remove(exit_pos)

    def draw_game(self):
        self.canvas.delete('all')

        # Draw walls
        for wall in self.walls:
            x, y = wall
            self.canvas.create_rectangle(
                x * self.cell_size, y * self.cell_size,
                (x + 1) * self.cell_size, (y + 1) * self.cell_size,
                fill='blue'
            )

        # Draw exits
        for exit_pos in self.exits:
            x, y = exit_pos
            self.canvas.create_rectangle(
                x * self.cell_size, y * self.cell_size,
                (x + 1) * self.cell_size, (y + 1) * self.cell_size,
                fill='green'
            )

        # Draw trinkets
        for trinket in self.trinkets:
            x, y = trinket
            self.canvas.create_oval(
                x * self.cell_size + 5, y * self.cell_size + 5,
                (x + 1) * self.cell_size - 5, (y + 1) * self.cell_size - 5,
                fill='yellow'
            )

        # Draw guards
        for guard in self.guards:
            x, y = guard
            self.canvas.create_oval(
                x * self.cell_size, y * self.cell_size,
                (x + 1) * self.cell_size, (y + 1) * self.cell_size,
                fill='red'
            )

        # Draw player
        x, y = self.player_pos
        self.canvas.create_oval(
            x * self.cell_size, y * self.cell_size,
            (x + 1) * self.cell_size, (y + 1) * self.cell_size,
            fill='white'
        )

        # Draw score
        self.canvas.create_text(
            150, 15,
            text=f"Trinkets: {self.collected_trinkets}/{self.total_trinkets}",
            fill='white',
            font=('Helvetica', 12)
        )

    def move_player(self, dx, dy):
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy

        # Check if move is valid
        if [new_x, new_y] not in self.walls:
            self.player_pos = [new_x, new_y]

            # Check for exit
            if self.player_pos in self.exits:
                self.end_game(True)
                return

            # Check for trinket collection
            if self.player_pos in self.trinkets:
                self.trinkets.remove(self.player_pos)
                self.collected_trinkets += 1

            # Check for guard collision
            if self.player_pos in self.guards:
                self.end_game(False)
                return

            self.draw_game()

    def end_game(self, success):
        if success:
            # Increased rewards based on collected trinkets
            base_reward = 100  # Base reward per trinket
            size_multiplier = {'small': 1, 'medium': 1.5, 'large': 2}[self.game.town_type]
            total_reward = int(self.collected_trinkets * base_reward * size_multiplier)
            self.game.coins += total_reward
            message = f"Success! You collected {self.collected_trinkets} trinkets and earned {total_reward} coins!"
        else:
            message = "You were caught by the guards!"

        self.window.destroy()
        messagebox.showinfo("Game Over", message)

def start_house_loot_game(parent, game):
    HouseLootGame(parent, game)