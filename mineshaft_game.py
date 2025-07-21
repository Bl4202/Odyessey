import tkinter as tk
from tkinter import ttk, messagebox
import random
from enum import Enum
import math

class TileType(Enum):
    WALL = "wall"  # Dark grey wall
    PATH = "path"  # Empty space
    SILVER = "silver"  # Silver ore node
    GOLD = "gold"    # Gold ore node
    DIAMOND = "diamond"  # Diamond node

class MineshaftGame(tk.Toplevel):
    def __init__(self, parent, game_state):
        super().__init__(parent)
        self.title("Mineshaft Exploration")
        self.game_state = game_state

        # Game state
        self.grid_size = 20  # Larger grid for mineshaft
        self.tiles = [[TileType.WALL for _ in range(self.grid_size)] 
                     for _ in range(self.grid_size)]
        self.health = 100
        self.energy = 100
        self.player_pos = [1, 1]  # Start near top-left
        
        # Generate cave system
        self.generate_cave()
        self.add_resource_nodes()

        # Setup UI
        self.setup_ui()

        # Center window
        self.geometry("800x900")
        self.resizable(False, False)

        # Bind movement keys
        self.bind('<Up>', lambda e: self.move_player(0, -1))
        self.bind('<Down>', lambda e: self.move_player(0, 1))
        self.bind('<Left>', lambda e: self.move_player(-1, 0))
        self.bind('<Right>', lambda e: self.move_player(1, 0))
        self.bind('<Return>', lambda e: self.mine_resource())

    def setup_ui(self):
        # Main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Status bars frame
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Health bar
        ttk.Label(status_frame, text="Health:").pack(side=tk.LEFT)
        self.health_bar = ttk.Progressbar(status_frame, length=200, maximum=100)
        self.health_bar.pack(side=tk.LEFT, padx=(5, 20))
        self.health_bar['value'] = self.health

        # Energy bar
        ttk.Label(status_frame, text="Energy:").pack(side=tk.LEFT)
        self.energy_bar = ttk.Progressbar(status_frame, length=200, maximum=100)
        self.energy_bar.pack(side=tk.LEFT, padx=5)
        self.energy_bar['value'] = self.energy

        # Cave view
        self.canvas = tk.Canvas(self.main_frame, width=600, height=600, bg='black')
        self.canvas.pack()

        # Instructions
        instructions = ttk.Label(
            self.main_frame,
            text="Controls:\n" +
                 "Arrow keys - Move\n" +
                 "Enter - Mine resource\n\n" +
                 "Legend:\n" +
                 "@ - Player\n" +
                 "# - Wall\n" +
                 "S - Silver Ore\n" +
                 "G - Gold Ore\n" +
                 "D - Diamond\n",
            justify=tk.LEFT
        )
        instructions.pack(pady=10)

        # Status messages
        self.status_label = ttk.Label(self.main_frame, text="Explore the mineshaft!")
        self.status_label.pack(pady=10)

    def generate_cave(self):
        # Start with a small room at player position
        self.create_room(self.player_pos[0], self.player_pos[1], 3)
        
        # Generate multiple connected rooms
        num_rooms = random.randint(8, 12)
        for _ in range(num_rooms):
            room_x = random.randint(2, self.grid_size - 3)
            room_y = random.randint(2, self.grid_size - 3)
            room_size = random.randint(3, 5)
            self.create_room(room_x, room_y, room_size)
            
            # Connect to nearest room with tunnels
            self.connect_to_nearest_path(room_x, room_y)

    def create_room(self, center_x, center_y, size):
        half = size // 2
        for y in range(max(0, center_y - half), min(self.grid_size, center_y + half + 1)):
            for x in range(max(0, center_x - half), min(self.grid_size, center_x + half + 1)):
                self.tiles[y][x] = TileType.PATH

    def connect_to_nearest_path(self, start_x, start_y):
        # Find nearest existing path tile
        min_dist = float('inf')
        nearest = None
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if self.tiles[y][x] == TileType.PATH:
                    dist = math.hypot(x - start_x, y - start_y)
                    if dist < min_dist and dist > 2:  # Avoid connecting to same room
                        min_dist = dist
                        nearest = (x, y)
        
        if nearest:
            # Create tunnel
            current_x, current_y = start_x, start_y
            while (current_x, current_y) != nearest:
                self.tiles[current_y][current_x] = TileType.PATH
                if abs(current_x - nearest[0]) > abs(current_y - nearest[1]):
                    current_x += 1 if nearest[0] > current_x else -1
                else:
                    current_y += 1 if nearest[1] > current_y else -1

    def add_resource_nodes(self):
        # Count path tiles
        path_tiles = [(x, y) for y in range(self.grid_size) 
                     for x in range(self.grid_size) 
                     if self.tiles[y][x] == TileType.PATH]
        
        # Add resources based on available space
        num_tiles = len(path_tiles)
        num_silver = max(2, num_tiles // 20)  # About 5% silver
        num_gold = max(1, num_tiles // 40)    # About 2.5% gold
        num_diamond = max(1, num_tiles // 60)  # About 1.7% diamond
        
        # Place resources randomly on path tiles
        for resource, count in [(TileType.SILVER, num_silver),
                              (TileType.GOLD, num_gold),
                              (TileType.DIAMOND, num_diamond)]:
            for _ in range(count):
                if path_tiles:
                    pos = random.choice(path_tiles)
                    path_tiles.remove(pos)
                    self.tiles[pos[1]][pos[0]] = resource

    def draw_cave(self):
        self.canvas.delete('all')
        cell_size = 600 // self.grid_size

        for y in range(self.grid_size):
            for x in range(self.grid_size):
                x1 = x * cell_size
                y1 = y * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                tile = self.tiles[y][x]
                if tile == TileType.WALL:
                    color = '#404040'  # Dark grey
                    symbol = '#'
                elif tile == TileType.PATH:
                    color = '#202020'  # Very dark grey for path
                    symbol = None
                elif tile == TileType.SILVER:
                    color = '#C0C0C0'  # Silver
                    symbol = 'S'
                elif tile == TileType.GOLD:
                    color = '#FFD700'  # Gold
                    symbol = 'G'
                elif tile == TileType.DIAMOND:
                    color = '#B9F2FF'  # Light blue for diamond
                    symbol = 'D'
                
                self.canvas.create_rectangle(x1, y1, x2, y2, 
                                          fill=color, outline='#303030')
                if symbol:
                    self.canvas.create_text(x1 + cell_size/2, y1 + cell_size/2,
                                          text=symbol, fill='black')

        # Draw player
        px = self.player_pos[0] * cell_size + cell_size/2
        py = self.player_pos[1] * cell_size + cell_size/2
        self.canvas.create_text(px, py, text='@', fill='white', font=('Courier', 14, 'bold'))

    def move_player(self, dx, dy):
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy

        if (0 <= new_x < self.grid_size and 
            0 <= new_y < self.grid_size and
            self.tiles[new_y][new_x] != TileType.WALL):
            self.player_pos = [new_x, new_y]
            self.draw_cave()

    def mine_resource(self):
        x, y = self.player_pos
        tile = self.tiles[y][x]
        
        if tile not in [TileType.SILVER, TileType.GOLD, TileType.DIAMOND]:
            return
        
        if not self.game_state.can_mine():
            self.status_label['text'] = "You need a pickaxe to mine here!"
            return

        # Reduce energy
        self.energy = max(0, self.energy - 15)
        self.energy_bar['value'] = self.energy

        # Mining success chance and rewards
        if random.random() < 0.7:  # 70% success rate
            if tile == TileType.SILVER:
                amount = random.randint(1, 2)
                self.game_state.add_inventory_item("silver ore", amount)
                self.status_label['text'] = f"Mined {amount} silver ore!"
            elif tile == TileType.GOLD:
                amount = 1
                self.game_state.add_inventory_item("gold ore", amount)
                self.status_label['text'] = f"Mined {amount} gold ore!"
            elif tile == TileType.DIAMOND:
                amount = 1
                self.game_state.add_inventory_item("diamond", amount)
                self.status_label['text'] = f"Mined {amount} diamond!"

            # Remove the resource
            self.tiles[y][x] = TileType.PATH
            self.draw_cave()
        else:
            self.status_label['text'] = "Failed to mine the resource!"

        if self.energy <= 0:
            messagebox.showinfo("Mining", "Too tired to continue mining!")
            self.destroy()

    def run(self):
        self.draw_cave()
        self.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = MineshaftGame(root, None)
    root.mainloop()
