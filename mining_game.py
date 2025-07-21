import tkinter as tk
from tkinter import ttk, messagebox
import random
from enum import Enum

class TileState(Enum):
    HIDDEN = "hidden"  # Dark grey tile (unmined)
    REVEALED = "revealed"  # Empty space (mined)
    COLLAPSED = "collapsed"  # Black tile (landslide, unmovable)

class MiningGame(tk.Toplevel):
    def __init__(self, parent, game_state):
        super().__init__(parent)
        self.title("Mining")
        self.game_state = game_state

        # Game state
        self.grid_size = 10
        self.tiles = [[TileState.HIDDEN for _ in range(self.grid_size)] 
                     for _ in range(self.grid_size)]
        self.health = 100
        self.energy = 100

        # Reveal top row as mineable
        for x in range(self.grid_size):
            self.tiles[0][x] = TileState.HIDDEN  # Changed from HIGHLIGHTED

        # Setup UI
        self.setup_ui()

        # Center window
        self.geometry("600x700")
        self.resizable(False, False)

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

        # Mining grid
        self.canvas = tk.Canvas(self.main_frame, width=500, height=500, bg='gray')
        self.canvas.pack()

        # Bind click event
        self.canvas.bind('<Button-1>', self.handle_click)

        self.draw_grid()

        # Status messages
        self.status_label = ttk.Label(self.main_frame, text="Click highlighted tiles to mine")
        self.status_label.pack(pady=10)

    def draw_grid(self):
        self.canvas.delete('all')
        cell_size = 500 // self.grid_size

        for y in range(self.grid_size):
            for x in range(self.grid_size):
                x1 = x * cell_size
                y1 = y * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                if self.tiles[y][x] == TileState.HIDDEN:
                    color = '#404040'  # Dark grey for unmined tiles
                elif self.tiles[y][x] == TileState.REVEALED:
                    color = 'light gray'  # Mined area
                else:  # COLLAPSED
                    color = 'black'  # Landslide area

                self.canvas.create_rectangle(x1, y1, x2, y2, 
                                          fill=color, outline='gray')

    def is_adjacent_to_revealed(self, x, y):
        if y == 0:  # Top row is always mineable
            return True

        adjacent = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
        return any(0 <= ax < self.grid_size and 0 <= ay < self.grid_size and 
                  self.tiles[ay][ax] == TileState.REVEALED
                  for ax, ay in adjacent)

    def update_highlighted_tiles(self):
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if (self.tiles[y][x] == TileState.HIDDEN and 
                    self.is_adjacent_to_revealed(x, y)):
                    self.tiles[y][x] = TileState.HIGHLIGHTED

    def handle_click(self, event):
        if self.energy <= 0:
            messagebox.showinfo("Mining", "Too tired to continue mining!")
            self.destroy()
            return

        if self.health <= 0:
            messagebox.showinfo("Mining", "You're too injured to continue mining!")
            self.destroy()
            return

        # Convert click to grid coordinates
        cell_size = 500 // self.grid_size
        x = event.x // cell_size
        y = event.y // cell_size

        if (0 <= x < self.grid_size and 0 <= y < self.grid_size and 
            self.tiles[y][x] == TileState.HIDDEN and
            self.is_adjacent_to_revealed(x, y)):

            # Reduce energy
            self.energy = max(0, self.energy - 10)
            self.energy_bar['value'] = self.energy

            # Reveal tile
            self.tiles[y][x] = TileState.REVEALED

            # Random event - increased landslide chance
            event_roll = random.random()
            if event_roll < 0.3:  # 30% chance of cave-in (increased from 10%)
                self.health = max(0, self.health - 20)
                self.health_bar['value'] = self.health
                self.status_label['text'] = "Cave-in! You took damage!"

                # Mark the tile and adjacent tiles as collapsed
                self.tiles[y][x] = TileState.COLLAPSED
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    new_x, new_y = x + dx, y + dy
                    if (0 <= new_x < self.grid_size and 
                        0 <= new_y < self.grid_size and 
                        self.tiles[new_y][new_x] == TileState.HIDDEN):
                        self.tiles[new_y][new_x] = TileState.COLLAPSED
            else:
                # Reward and possible mineshaft discovery
                reward_roll = random.random()
                if reward_roll < 0.03:  # 3% chance to find a mineshaft
                    self.game_state.add_mineshaft()
                    messagebox.showinfo("Discovery!", 
                                      "You've discovered a mineshaft! You'll need a pickaxe to mine here.")
                    self.destroy()
                    return
                elif reward_roll < 0.4:  # 37% copper
                    amount = random.randint(1, 3)
                    self.game_state.add_inventory_item("copper ore", amount)
                    self.status_label['text'] = f"Found {amount} copper ore!"
                elif reward_roll < 0.7:  # 30% iron
                    amount = random.randint(1, 2)
                    self.game_state.add_inventory_item("iron ore", amount)
                    self.status_label['text'] = f"Found {amount} iron ore!"
                else:  # 30% coins
                    amount = random.randint(5, 15)
                    self.game_state.coins += amount
                    self.status_label['text'] = f"Found {amount} coins!"

            self.draw_grid()