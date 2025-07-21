import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import styles as st
from game_logic import GameState, Weapon, WeaponType #Import necessary classes
from random import randint, choice
from collections import deque
from math import floor
import random
import traceback  # Added for better error reporting
import os
from user_auth import user_auth

# Check if we can import noise module
try:
    import noise
    print("Noise module successfully imported")
except ImportError as e:
    print(f"Error importing noise module: {e}")
    traceback.print_exc()

class WorldMapView(tk.Canvas):
    def __init__(self, parent, game_gui, game):
        super().__init__(parent, width=500, height=500, bg='black')
        self.game = game
        self.game_gui = game_gui
        self.base_viewport_size = 12  # Default viewport size
        self.viewport_size = self.get_viewport_size()  # Will be either 12 or 21
        self.colors = {
            'P': 'green',    # Plains
            'T_small': '#6F6F6F',  # Light gray for small towns
            'T_medium': '#4F4F4F',  # Medium gray for medium towns
            'T_large': '#2F2F2F',  # Dark gray for large towns
            'X': '#FF0000',    # Red for Temple
            'M': '#8B4513',    # Saddle Brown for Mineshaft
            'O': '#1a237e',    # Deep indigo for Deep Ocean
            'B': '#F4D03F',    # Sand Yellow for Beach
            'C': '#039be5',    # Light ocean blue for Coastline
            'F': '#006400',    # Default Forest Green (will be dynamic)
            'S1': '#ff9999',   # Light Red for Tier 1 Stronghold
            'S2': '#ff3333',   # Bright Red for Tier 2 Stronghold
            'S3': '#cc0000',   # Dark Red for Tier 3 Stronghold
            'F_F': '#FFD700',  # Changed to yellow (Gold) for Fort
            '@': 'white'     # Player
        }

        self.root = self.winfo_toplevel()
        self.root.bind('<Up>', lambda e: self.move_player(0, -1))
        self.root.bind('<Down>', lambda e: self.move_player(0, 1))
        self.root.bind('<Left>', lambda e: self.move_player(-1, 0))
        self.root.bind('<Right>', lambda e: self.move_player(1, 0))
        self.root.bind('<Return>', lambda e: self.interact())

        self.bind('<Configure>', self.on_resize)
        self.draw_map()

    def get_viewport_size(self):
        return 21 if 'advanced_map' in self.game.inventory else self.base_viewport_size

    def on_resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()
        self.viewport_size = self.get_viewport_size()  # Update viewport size
        self.cell_size = min(width, height) // self.viewport_size
        self.draw_map()

    def world_to_screen(self, world_x, world_y):
        view_x = world_x - self.game.player_x + self.viewport_size // 2
        view_y = world_y - self.game.player_y + self.viewport_size // 2
        return view_x, view_y

    def draw_map(self):
        self.delete('all')
        width = self.winfo_width()
        height = self.winfo_height()
        self.cell_size = min(width, height) // self.viewport_size
        offset_x = (width - self.cell_size * self.viewport_size) // 2
        offset_y = (height - self.cell_size * self.viewport_size) // 2
        min_x = self.game.player_x - self.viewport_size // 2
        max_x = self.game.player_x + self.viewport_size // 2
        min_y = self.game.player_y - self.viewport_size // 2
        max_y = self.game.player_y + self.viewport_size // 2
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                terrain = self.game.world.get_terrain(x, y)
                view_x, view_y = self.world_to_screen(x, y)
                x1 = view_x * self.cell_size + offset_x
                y1 = view_y * self.cell_size + offset_y
                if terrain == 'T':
                    town_type = self.game.world.get_town_type(x, y)
                    color = self.colors[f'T_{town_type}']
                elif terrain == 'F':
                    color = self.game.world.get_forest_color(x, y)
                elif terrain.startswith('S'): # Stronghold
                    color = self.colors[terrain]
                elif terrain == 'F_F': #Fort
                    color = self.colors['F_F']
                else:
                    color = self.colors[terrain]
                self.create_rectangle(x1, y1, 
                                        x1 + self.cell_size, 
                                        y1 + self.cell_size, 
                                        fill=color,
                                        outline='dark gray')
        player_x = (self.viewport_size // 2) * self.cell_size + offset_x + self.cell_size/2
        player_y = (self.viewport_size // 2) * self.cell_size + offset_y + self.cell_size/2
        self.create_text(player_x, player_y, text='@', 
                            fill=self.colors['@'], font=('Courier', 14, 'bold'))

    def move_player(self, dx, dy):
        new_x = self.game.player_x + dx
        new_y = self.game.player_y + dy

        if not self.game.can_move_to(new_x, new_y):
            self.game_gui.append_to_output("You need a boat to travel in deep ocean!")
            return

        success, message = self.game.move_player(dx, dy)
        if success:
            self.draw_map()
            self.game_gui.append_to_output(message)
            self.game_gui.update_action_buttons()

    def handle_temple_interaction(self):
        # Use the game_gui parameter instead of directly accessing the attribute
        if hasattr(self.game_gui, 'append_to_output'):
            self.game_gui.append_to_output(
                "You enter the ancient temple. The air is thick with mystery. " +
                "Strange symbols cover the walls, but their meaning eludes you. " +
                "A mysterious force gently guides you back outside.")

    def interact(self):
        terrain = self.game.world.get_terrain(self.game.player_x, self.game.player_y)
        if terrain == 'P':
            if messagebox.askyesno("Location", "Would you like to hunt here? (Or press No to mine)"):
                from hunting_game import HuntingGame
                HuntingGame(self, self.game)
                self.game_gui.update_inventory_display()
            elif 'shovel' in self.game.inventory:
                from mining_game import MiningGame
                MiningGame(self, self.game)
                self.game_gui.update_inventory_display()
            else:
                self.game_gui.append_to_output("You need a shovel to mine here!")
        elif terrain == 'T':
            town_type = self.game.world.get_town_type(
                self.game.player_x, self.game.player_y)
            TownView(self, self.game_gui, town_type)
        elif terrain == 'X':
            self.handle_temple_interaction()
        elif terrain == 'M':
            if 'pickaxe' in self.game.inventory:
                from mineshaft_game import MineshaftGame
                mineshaft_window = MineshaftGame(self.winfo_toplevel(), self.game)
                mineshaft_window.run()
                self.game_gui.update_inventory_display()
            else:
                self.game_gui.append_to_output("You need a pickaxe to enter the mineshaft!")
        elif terrain.startswith('S'): # Stronghold
            self.game_gui.start_combat()
        elif terrain == 'F_F': # Fort
            self.game_gui.show_trade_window("fort_keeper")



class InventoryWindow:
    def __init__(self, parent, game):
        self.window = tk.Toplevel(parent)
        self.window.title("Inventory")
        self.window.geometry("400x500")  # Made taller to accommodate weapons
        self.game = game

        # Create a notebook with tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Items tab
        self.items_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.items_frame, text='Items')

        # Weapons tab
        self.weapons_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.weapons_frame, text='Weapons')

        # Items inventory text
        self.inventory_text = tk.Text(
            self.items_frame,
            height=15,
            width=40,
            font=st.FONTS['normal']
        )
        self.inventory_text.pack(padx=10, pady=10, fill='both', expand=True)

        # Weapons section
        self.weapons_text = tk.Text(
            self.weapons_frame,
            height=12,
            width=40,
            font=st.FONTS['normal']
        )
        self.weapons_text.pack(padx=10, pady=5, fill='both', expand=True)

        # Weapon action buttons frame
        self.weapon_buttons_frame = ttk.Frame(self.weapons_frame)
        self.weapon_buttons_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(self.weapon_buttons_frame, text="Switch Combat Weapon", 
                  command=lambda: self.switch_weapon("combat")).pack(side='left', padx=5)

        ttk.Button(self.weapon_buttons_frame, text="Switch Hunting Weapon", 
                  command=lambda: self.switch_weapon("hunting")).pack(side='left', padx=5)

        self.update_display()

    def update_display(self):
        # Update items inventory
        self.inventory_text.config(state=tk.NORMAL)
        self.inventory_text.delete(1.0, tk.END)

        inventory_text = f"Coins: {self.game.coins}\n\n"
        for item, count in self.game.inventory.items():
            inventory_text += f"{item}: {count}\n"

        self.inventory_text.insert(tk.END, inventory_text)
        self.inventory_text.config(state=tk.DISABLED)

        # Update weapons inventory
        self.weapons_text.config(state=tk.NORMAL)
        self.weapons_text.delete(1.0, tk.END)

        # Get current weapons
        current_combat = self.game.get_current_weapon("combat")
        current_hunting = self.game.get_current_weapon("hunting")

        # List all weapons
        weapons_text = "COMBAT WEAPONS:\n"
        weapons_text += f"Current: {current_combat.name} (Tier {current_combat.tier}, Damage: {current_combat.damage:.1f})\n\n"

        combat_weapons = []
        hunting_weapons = []

        for weapon_id, weapon in self.game.weapons.items():
            if weapon.weapon_type.value == "combat":
                if weapon_id != current_combat.id:  # Don't list current weapon twice
                    combat_weapons.append(weapon)
            else:
                if weapon_id != current_hunting.id:  # Don't list current weapon twice
                    hunting_weapons.append(weapon)

        if combat_weapons:
            weapons_text += "Other combat weapons:\n"
            for weapon in combat_weapons:
                weapons_text += f"- {weapon.name} (Tier {weapon.tier}, Damage: {weapon.damage:.1f})\n"
        else:
            weapons_text += "No other combat weapons.\n"

        weapons_text += "\nHUNTING WEAPONS:\n"
        weapons_text += f"Current: {current_hunting.name} (Tier {current_hunting.tier}, Damage: {current_hunting.damage:.1f})\n\n"

        if hunting_weapons:
            weapons_text += "Other hunting weapons:\n"
            for weapon in hunting_weapons:
                weapons_text += f"- {weapon.name} (Tier {weapon.tier}, Damage: {weapon.damage:.1f})\n"
        else:
            weapons_text += "No other hunting weapons.\n"

        self.weapons_text.insert(tk.END, weapons_text)
        self.weapons_text.config(state=tk.DISABLED)

    def switch_weapon(self, weapon_type):
        # Simply switch the weapon and update the display
        success, message = self.game.switch_weapon(weapon_type)
        
        # Try to find the GameGUI parent to show messages
        # Since we might not reliably find it, we'll show a message box instead
        if message:
            messagebox.showinfo("Weapon Switch", message)
            
        # Always update the inventory display
        self.update_display()

class TownView:
    def __init__(self, parent, game_gui, town_type):
        self.window = tk.Toplevel(parent)
        town_name = game_gui.game.world.get_town_name(
            game_gui.game.player_x, game_gui.game.player_y)
        self.window.title(f"{town_name}")
        self.window.geometry("600x400")
        self.game_gui = game_gui
        self.town_type = town_type
        self.game = game_gui.game

        self.town_size = (15, 15)  
        self.town_map = []
        self.house_lights = {}  
        self.town_sizes = {
            'small': 6,    
            'medium': 12,  
            'large': 20    
        }

        self.min_road_lengths = {
            'small': 3,
            'medium': 5,
            'large': 7
        }

        self.vendor_counts = {
            'small': (3, 4),    
            'medium': (4, 6),
            'large': (6, 8)
        }

        self.house_chances = {
            'small': 3,     
            'medium': 2,    
            'large': 1.5    
        }

        # Check if we have a stored layout for this town
        stored_layout = self.game.world.get_town_layout(
            self.game.player_x, self.game.player_y)
        if stored_layout:
            self.town_map, self.house_lights = stored_layout
        else:
            self.generate_town()
            # Store the new layout
            self.game.world.store_town_layout(
                self.game.player_x, self.game.player_y, 
                (self.town_map, self.house_lights))

        self.player_pos = [self.town_size[0]//2, self.town_size[1]//2]

        self.canvas = tk.Canvas(self.window, width=500, height=500, bg='black')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.window.bind('<Up>', lambda e: self.move_player(0, -1))
        self.window.bind('<Down>', lambda e: self.move_player(0, 1))
        self.window.bind('<Left>', lambda e: self.move_player(-1, 0))
        self.window.bind('<Right>', lambda e: self.move_player(1, 0))
        self.window.bind('<Return>', lambda e: self.interact())
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        self.draw_town()

    def generate_town(self):
        self.town_map = [['.' for _ in range(self.town_size[0])] 
                         for _ in range(self.town_size[1])]
        target_market_tiles = self.town_sizes[self.town_type]
        center_x = self.town_size[0] // 2
        center_y = self.town_size[1] // 2
        market_tiles = [(center_x, center_y)]
        self.town_map[center_y][center_x] = 'M'
        while len(market_tiles) < target_market_tiles:
            x, y = choice(market_tiles)
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                if (0 <= new_x < self.town_size[0] and 
                    0 <= new_y < self.town_size[1] and 
                    self.town_map[new_y][new_x] == '.'):
                    self.town_map[new_y][new_x] = 'M'
                    market_tiles.append((new_x, new_y))
                    break
        perimeter = set()
        for x, y in market_tiles:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_x, new_y = x + dx, y + dy
                if (0 <= new_x < self.town_size[0] and 
                    0 <= new_y < self.town_size[1] and 
                    self.town_map[new_y][new_x] == '.'):
                    perimeter.add((new_x, new_y))
        vendor_types = ['C', 'S', 'T', 'G', 'F', 'L']  # Added 'L' for lumberjack
        min_vendors, max_vendors = self.vendor_counts[self.town_type]
        num_vendors = randint(min_vendors, min(len(perimeter), max_vendors))
        perimeter_list = list(perimeter)

        vendor_colors = {
            'C': 'light blue',  # Chef
            'S': 'orange',      # Blacksmith
            'T': 'purple',      # Toolsmith
            'G': 'light green',  # Gunsmith
            'F': 'cyan',         # Fisher
            'L': 'brown'        # Lumberjack
        }

        for _ in range(num_vendors):
            if perimeter_list:
                pos = perimeter_list.pop(randint(0, len(perimeter_list) - 1))
                vendor_type = choice(vendor_types)
                self.town_map[pos[1]][pos[0]] = vendor_type
                perimeter.remove(pos)
        min_road_length = self.min_road_lengths[self.town_type]
        max_road_length = min_road_length + 5  
        for x, y in perimeter:
            if self.town_map[y][x] == '.':
                dx = 0 if abs(x - center_x) <= abs(y - center_y) else (1 if x < center_x else -1)
                dy = 0 if dx != 0 else (1 if y < center_y else -1)
                self.town_map[y][x] = '#'
                total_road_length = 1
                for direction in [-1, 1]:  
                    curr_x = x + dx * direction
                    curr_y = y + dy * direction
                    while (total_road_length < min_road_length and  
                           0 <= curr_x < self.town_size[0] and 
                           0 <= curr_y < self.town_size[1] and 
                           self.town_map[curr_y][curr_x] == '.'):
                               self.town_map[curr_y][curr_x] = '#'
                               total_road_length += 1
                               for side_dx, side_dy in [(-dy, dx), (dy, -dx)]:  
                                   house_x, house_y = curr_x + side_dx, curr_y + side_dy
                                   if (0 <= house_x < self.town_size[0] and 
                                       0 <= house_y < self.town_size[1] and 
                                       self.town_map[house_y][house_x] == '.' and
                                       randint(0, floor(self.house_chances[self.town_type])) == 0):  
                                       has_lights = randint(0, 1) == 1
                                       self.town_map[house_y][house_x] = 'H' if has_lights else 'h'
                                       self.house_lights[(house_x, house_y)] = has_lights
                               curr_x += dx * direction
                               curr_y += dy * direction
                               if total_road_length >= max_road_length:
                                   break

    def draw_town(self):
        self.canvas.delete('all')
        cell_size = 25
        for y in range(self.town_size[1]):
            for x in range(self.town_size[0]):
                x1, y1 = x * cell_size, y * cell_size
                char = self.town_map[y][x]
                color = 'white'
                if char == '.':
                    continue  
                elif char == 'M':
                    color = 'yellow'
                elif char == '#':
                    color = 'gray'
                elif char in ['H', 'h']:
                    # Check if house is looted
                    if self.game.world.is_house_looted(
                        self.game.player_x, self.game.player_y, x, y):
                        char = 'X'  # Show as looted
                        color = 'dark red'
                    else:
                        color = 'green' if char == 'H' else 'red'
                elif char == 'C':
                    color = 'light blue' #Added chef color
                elif char == 'S':
                    color = 'orange'
                elif char == 'T':
                    color = 'purple'
                elif char == 'G': #Added Gunsmith color
                    color = 'dark green'
                elif char == 'F': #Added Fisher color
                    color = 'cyan'
                elif char == 'L': #Added Lumberjack color
                    color = 'brown'
                self.canvas.create_text(x1 + cell_size/2, y1 + cell_size/2, 
                                        text=char, fill=color, font=('Courier', 12, 'bold'))

        # Draw player
        px = self.player_pos[0] * cell_size + cell_size/2
        py = self.player_pos[1] * cell_size + cell_size/2
        self.canvas.create_text(px, py, text='@', 
                                fill='white', font=('Courier', 12, 'bold'))

    def move_player(self, dx, dy):
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        if (0 <= new_x < self.town_size[0] and 
            0 <= new_y < self.town_size[1] and
            self.town_map[new_y][new_x] != '.'):  
            self.player_pos = [new_x, new_y]
            self.draw_town()
            self.game_gui.update_action_buttons()

    def interact(self):
        x, y = self.player_pos
        cell = self.town_map[y][x]
        if cell in ['C', 'S', 'T', 'G', 'F', 'L']:  # Added 'G' and 'C'
            vendor_types = {
                'C': 'chef',
                'S': 'blacksmith', 
                'T': 'toolsmith',
                'G': 'gunsmith',
                'F': 'fisher',
                'L': 'lumberjack'
            }
            self.game_gui.show_trade_window(vendor_types[cell])
        elif cell in ['H', 'h']:
            # Check if house has been looted
            if not self.game.world.is_house_looted(
                self.game.player_x, self.game.player_y, x, y):
                has_lights = cell == 'H'
                self.game_gui.show_house_interaction(
                    self.window, has_lights, self.town_type)
                # Mark house as looted after interaction
                self.game.world.mark_house_looted(
                    self.game.player_x, self.game.player_y, x, y)
                self.draw_town()  # Redraw to show looted status
            else:
                self.game_gui.append_to_output("This house has already been looted.")

class GameGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Odyssey")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.game = GameState()
        self.inventory_window = None
        self.setup_gui()

    def setup_gui(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # World map setup
        self.world_map = WorldMapView(self.main_frame, self, self.game)
        self.world_map.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Right frame setup
        right_frame = ttk.Frame(self.main_frame)
        right_frame.grid(row=0, column=1, sticky="n", padx=5, pady=5)

        # Buttons frame
        buttons_frame = ttk.Frame(right_frame)
        buttons_frame.pack(fill=tk.X)

        # Action buttons
        self.hunt_button = ttk.Button(buttons_frame, text="Hunt", command=self.handle_hunt)
        self.mine_button = ttk.Button(buttons_frame, text="Mine", command=self.handle_mine)
        self.enter_button = ttk.Button(buttons_frame, text="Enter Location", 
                                    command=self.handle_enter_location)
        self.combat_button = ttk.Button(buttons_frame, text="Combat", command=self.start_combat, state=tk.DISABLED) #Added combat button


        # Standard buttons
        ttk.Button(buttons_frame, text="View Inventory", 
                  command=self.toggle_inventory).pack(pady=5, fill=tk.X)

        # Window size buttons
        ttk.Button(buttons_frame, text="Larger Window", 
                  command=self.increase_window_size).pack(pady=2, fill=tk.X)
        ttk.Button(buttons_frame, text="Smaller Window", 
                  command=self.decrease_window_size).pack(pady=2, fill=tk.X)

        # Save/Load buttons
        ttk.Button(buttons_frame, text="Save Game", 
                  command=self.save_game).pack(pady=2, fill=tk.X)
        ttk.Button(buttons_frame, text="Load Game", 
                  command=self.load_game).pack(pady=2, fill=tk.X)

        # Test coins button (for debugging)
        def add_test_coins():
            self.game.coins += 9999
            self.append_to_output("Added 9999 test coins!")
            if self.inventory_window:
                self.inventory_window.update_display()

        ttk.Button(buttons_frame, text="Add Test Coins", 
                  command=add_test_coins).pack(pady=5, fill=tk.X)

        # Output text
        self.output_text = tk.Text(
            self.main_frame,
            height=8,
            wrap=tk.WORD,
            font=st.FONTS['normal']
        )
        self.output_text.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.update_action_buttons()

    def increase_window_size(self):
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        new_width = int(current_width * 1.2)
        new_height = int(current_height * 1.2)
        self.root.geometry(f"{new_width}x{new_height}")

    def decrease_window_size(self):
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        new_width = max(600, int(current_width * 0.8))
        new_height = max(400, int(current_height * 0.8))
        self.root.geometry(f"{new_width}x{new_height}")

    def update_action_buttons(self):
        terrain = self.game.world.get_terrain(self.game.player_x, self.game.player_y)

        # Configure hunt and mine buttons
        if terrain == 'P':
            self.hunt_button.pack(pady=5, fill=tk.X)
            if 'shovel' in self.game.inventory:
                self.mine_button.pack(pady=5, fill=tk.X)
            else:
                self.mine_button.pack_forget()
        else:
            self.hunt_button.pack_forget()
            self.mine_button.pack_forget()

        # Configure enter button
        if terrain in ['T', 'X', 'M', 'O', 'C', 'F', 'S1', 'S2', 'S3', 'F_F']: # Added 'O' for ocean and 'F' for forest and strongholds and fort
            button_text = {
                'T': "Enter Town",
                'X': "Enter Temple",
                'M': "Enter Mineshaft",
                'O': "Go Fishing", # Added ocean option
                'C': "Go Fishing", # Added coastline option
                'F': "Cut Wood", # Added forest option
                'S1': "Enter Stronghold",
                'S2': "Enter Stronghold",
                'S3': "Enter Stronghold",
                'F_F': "Enter Fort"
            }.get(terrain, "Enter Location") # Default to "Enter Location" if terrain is unexpected
            self.enter_button.configure(text=button_text)
            self.enter_button.pack(pady=5, fill=tk.X)
            self.combat_button.pack_forget() #Hide combat button if not on stronghold
        else:
            self.enter_button.pack_forget()
            if terrain.startswith('S'): #Show combat button on stronghold
                self.combat_button.pack(pady=5, fill=tk.X)
                self.combat_button.config(state=tk.NORMAL) #Enable combat button

    def handle_hunt(self):
        from hunting_game import HuntingGame
        HuntingGame(self.root, self.game)
        self.update_inventory_display()

    def handle_mine(self):
        terrain = self.game.world.get_terrain(self.game.player_x, self.game.player_y)
        if terrain == 'P' and 'shovel' in self.game.inventory:
            from mining_game import MiningGame
            MiningGame(self.root, self.game)
            self.update_inventory_display()
        else:
            self.append_to_output("You need a shovel to mine here!")

    def handle_enter_location(self):
        terrain = self.game.world.get_terrain(self.game.player_x, self.game.player_y)
        if terrain == 'T':
            town_type = self.game.world.get_town_type(
                self.game.player_x, self.game.player_y)
            TownView(self.world_map, self, town_type)
        elif terrain == 'X':
            self.world_map.handle_temple_interaction()
        elif terrain == 'M':
            if 'pickaxe' in self.game.inventory:
                from mineshaft_game import MineshaftGame
                MineshaftGame(self.root, self.game).run()
                self.update_inventory_display()
            else:
                self.append_to_output("You need a pickaxe to enter the mineshaft!")
        elif terrain in ['O', 'C']:  # Allow fishing in both ocean and coastline
            if 'fishing_rod' in self.game.inventory:
                self.append_to_output("Starting fishing minigame...")
                from fishing_game import start_fishing_game
                start_fishing_game(self.root, self.game)
                self.update_inventory_display()
            else:
                self.append_to_output("You need a fishing rod to fish here! Visit the fisher in town to buy one.")
        elif terrain == 'F':
            if 'axe' in self.game.inventory:
                success, message = self.game.attempt_woodcutting()
                self.append_to_output(message)
                self.world_map.draw_map()  # Redraw map to show forest depletion
                self.update_inventory_display()
            else:
                self.append_to_output("You need an axe to cut wood here! Visit the lumberjack in town to buy one.")
        elif terrain.startswith('S'): # Stronghold
            self.start_combat() # initiate combat
        elif terrain == 'F_F':
            self.append_to_output("Entering the Fort...")

    def start_combat(self):
        from combat_game import start_combat
        # Get the surrounding terrains and stronghold tier
        stronghold_tier = self.game.world.get_stronghold_tier(self.game.player_x, self.game.player_y)
        surrounding_terrains = self.game.world.get_surrounding_terrains(self.game.player_x, self.game.player_y)
        # Start combat with the appropriate parameters
        start_combat(self.root, self.game, stronghold_tier, surrounding_terrains)
        self.update_inventory_display()
        self.world_map.draw_map()  # Redraw map after combat


    def toggle_inventory(self):
        if self.inventory_window is None or not self.inventory_window.window.winfo_exists():
            self.inventory_window = InventoryWindow(self.root, self.game)
        else:
            self.inventory_window.window.lift()
            self.inventory_window.update_display()

    def update_inventory_display(self):
        if self.inventory_window and self.inventory_window.window.winfo_exists():
            self.inventory_window.update_display()

    def append_to_output(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, f"{text}\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def save_game(self):
        """Handle saving the game"""
        # Check if a user is logged in
        if not user_auth.is_logged_in():
            messagebox.showinfo("Login Required", 
                "You need to be logged in to save your game. Please restart the game and log in.")
            return
        
        # Let the user choose a save name
        save_name = simpledialog.askstring("Save Game", 
                                        "Enter a name for your save file:",
                                        initialvalue="default")
        if not save_name:
            return  # User cancelled
        
        # Convert game state to dictionary
        game_data = self.game.to_dict()
        
        # Save the game using the user_auth system
        success, message = user_auth.save_game(game_data, save_name)
        self.append_to_output(message)
        
        if success:
            messagebox.showinfo("Save Game", f"Game saved as '{save_name}' successfully!")
        else:
            messagebox.showerror("Save Error", message)

    def load_game(self):
        """Handle loading the game"""
        # Check if a user is logged in
        if not user_auth.is_logged_in():
            messagebox.showinfo("Login Required", 
                "You need to be logged in to load a saved game. Please restart the game and log in.")
            return
        
        # Get list of available save files
        save_files, message = user_auth.get_save_files()
        
        if not save_files:
            messagebox.showinfo("No Saves", "No save files found for this account.")
            return
        
        # Let the user choose a save file
        save_name = simpledialog.askstring("Load Game", 
                                        "Enter the name of the save to load:",
                                        initialvalue=save_files[0])
        
        if not save_name:
            return  # User cancelled
        
        if messagebox.askyesno("Load Game", 
                              f"Loading '{save_name}' will override current progress. Continue?"):
            
            # Load the game using the user_auth system
            game_data, message = user_auth.load_game(save_name)
            
            if game_data:
                # Load the game data into the current game state
                self.game.from_dict(game_data)
                self.world_map.draw_map()
                self.update_inventory_display()
                self.append_to_output(f"Game '{save_name}' loaded successfully!")
                messagebox.showinfo("Load Game", f"Game '{save_name}' loaded successfully!")
            else:
                self.append_to_output(message)
                messagebox.showerror("Load Error", message)

    def show_trade_window(self, villager_type):
        self.append_to_output(f"Trading with {villager_type}")
        trade_window = tk.Toplevel(self.root)
        trade_window.title("Trade")
        
        # Use a wider window for the fort to show more weapon details
        if villager_type == "fort_keeper":
            trade_window.geometry("700x600")
        else:
            trade_window.geometry("500x500")

        # Get NPC name
        npc_name = self.game.world.get_npc_name(
            self.game.player_x, self.game.player_y, villager_type)

        if villager_type == "fort_keeper":
            # Create label frame for fort keeper
            main_frame = ttk.LabelFrame(trade_window, text=f"Trading with {npc_name} the Fort Keeper")
            main_frame.pack(pady=10, padx=10, fill="x")

            # Show available weapons
            weapons_frame = ttk.LabelFrame(main_frame, text="Available Weapons")
            weapons_frame.pack(pady=5, padx=5, fill="x")

            # Get weapons from fort inventory
            fort_inventory = self.game.world.get_fort_inventory(
                self.game.player_x, self.game.player_y)

            # List available weapons from the fort inventory
            for weapon in fort_inventory:
                weapon_frame = ttk.Frame(weapons_frame)
                weapon_frame.pack(pady=2, fill="x")

                # Show tier with stars
                tier_stars = "★" * weapon.tier

                ttk.Label(weapon_frame, 
                         text=f"{weapon.name} (Tier {weapon.tier} {tier_stars})").pack(side="left")
                         
                # Display dice format: 2d6+2 (avg: 9.0)
                dice_text = f"{weapon.num_dice}d{weapon.dice_sides}+{weapon.modifier}"
                avg_damage = weapon.calculate_avg_damage()
                ttk.Label(weapon_frame, 
                         text=f"Damage: {dice_text} (avg: {avg_damage})").pack(side="left", padx=10)

                cost = weapon.get_cost()
                ttk.Label(weapon_frame, 
                         text=f"Cost: {cost} coins").pack(side="left", padx=10)

                # Create a button frame for better placement
                button_frame = ttk.Frame(weapon_frame)
                button_frame.pack(side="right", padx=5)
                
                def make_buy_command(weapon_id):
                    def buy():
                        success, message = self.game.attempt_trade(
                            "fort_keeper", "buy", weapon_id)
                        self.append_to_output(message)
                        self.update_inventory_display()
                        # Refresh the window to show updated inventory
                        trade_window.destroy()
                        self.show_trade_window("fort_keeper")
                    return buy

                ttk.Button(button_frame, text="Buy", 
                          command=make_buy_command(weapon.id)).pack(side="right", padx=5)

            # Add weapon comparison
            current_weapon = self.game.get_current_weapon("combat")
            
            # Handle the case when player doesn't have a weapon yet
            if current_weapon is None:
                ttk.Label(main_frame, 
                         text="You don't have a combat weapon yet").pack(pady=5)
            else:
                current_tier_stars = "★" * current_weapon.tier
                
                # Display current weapon with dice format
                dice_text = f"{current_weapon.num_dice}d{current_weapon.dice_sides}+{current_weapon.modifier}"
                avg_damage = current_weapon.calculate_avg_damage()
                
                ttk.Label(main_frame, 
                         text=f"Current weapon: {current_weapon.name} "
                              f"(Tier {current_weapon.tier} {current_tier_stars}) "
                              f"Damage: {dice_text} (avg: {avg_damage})").pack(pady=5)

            # Add button to switch weapons only if we have at least one weapon
            if current_weapon is not None:
                ttk.Button(main_frame, text="Switch Combat Weapon", 
                          command=lambda: self.switch_weapon("combat")).pack(pady=5)

            return

        elif villager_type == "gunsmith":
            ttk.Label(trade_window, text="Gunsmith's Shop", 
                     font=('Arial', 14, 'bold')).pack(pady=10)

            # Create frame for weapon display
            weapon_frame = ttk.LabelFrame(trade_window, text="Current Weapons")
            weapon_frame.pack(pady=10, padx=10, fill="x")

            # Show both weapons and their levels
            weapons_text = ""
            for weapon_type in [WeaponType.REVOLVER, WeaponType.HUNTING_RIFLE]:
                if weapon_type in self.game.weapons:
                    weapon = self.game.weapons[weapon_type]
                    weapons_text += f"{weapon_type.name}: Level {weapon.upgrade_level}\n"

            ttk.Label(weapon_frame, text=weapons_text).pack(pady=5)

            # Buy hunting rifle frame
            if WeaponType.HUNTING_RIFLE not in self.game.weapons:
                buy_frame = ttk.LabelFrame(trade_window, text="Buy Weapons")
                buy_frame.pack(pady=10, padx=10, fill="x")

                # Improved formatting for hunting rifle purchase
                info_frame = ttk.Frame(buy_frame)
                info_frame.pack(pady=5, fill="x")
                ttk.Label(info_frame, text="Hunting Rifle - 500 coins", font=('Helvetica', 10, 'bold')).pack(side=tk.LEFT, padx=5)
                ttk.Label(info_frame, text="(2x damage, requires reload)").pack(side=tk.RIGHT, padx=5)

                def buy_rifle():
                    success, message = self.game.attempt_trade("gunsmith", "buy", "hunting_rifle", 1)
                    self.append_to_output(message)
                    self.update_inventory_display()
                    if success:
                        trade_window.destroy()  # Refresh the window to show upgrade options
                        self.show_trade_window("gunsmith")

                ttk.Button(buy_frame, text="Buy Hunting Rifle", 
                          command=buy_rifle).pack(pady=10)

            # Upgrade frame for each owned weapon
            for weapon_type in [WeaponType.REVOLVER, WeaponType.HUNTING_RIFLE]:
                if weapon_type in self.game.weapons:
                    weapon_frame = ttk.LabelFrame(
                        trade_window, 
                        text=f"Upgrade {weapon_type.name}")
                    weapon_frame.pack(pady=10, padx=10, fill="x")

                    weapon = self.game.weapons[weapon_type]
                    cost = weapon.get_upgrade_cost()
                    cost_text = f"Next upgrade cost: {cost['copper_bars']} copper bars, {cost['iron_bars']} iron bars, {cost['coins']} coins"
                    cost_label = ttk.Label(weapon_frame, text=cost_text)
                    cost_label.pack(pady=5)

                    def make_upgrade_command(weapon_type):
                        def upgrade():
                            # Find the weapon's ID from the weapon_type
                            if weapon_type in self.game.weapons:
                                weapon_id = self.game.weapons[weapon_type].id
                                success, message = self.game.attempt_weapon_upgrade(weapon_id)
                                self.append_to_output(message)
                                self.update_inventory_display()
                                if success:
                                    trade_window.destroy()  # Refresh the window to show new costs
                                    self.show_trade_window("gunsmith")
                            else:
                                self.append_to_output(f"No {weapon_type.name} found to upgrade")
                        return upgrade

                    ttk.Button(weapon_frame, text=f"Upgrade {weapon_type.name}", 
                              command=make_upgrade_command(weapon_type)).pack(pady=5)

            # Bullet crafting frame
            bullet_frame = ttk.LabelFrame(trade_window, text="Craft Bullets")
            bullet_frame.pack(pady=10, padx=10, fill="x")

            ttk.Label(bullet_frame, text="20 bullets for 1 silver ore").pack(pady=5)

            def craft_bullets():
                success, message = self.game.attempt_trade("gunsmith", "buy", "bullets", 1)
                self.append_to_output(message)
                self.update_inventory_display()
                bullet_count.config(text=f"Current bullets: {self.game.inventory.get('bullets', 0)}")

            ttk.Button(bullet_frame, text="Craft Bullets", 
                      command=craft_bullets).pack(pady=5)
            bullet_count = ttk.Label(
                bullet_frame, 
                text=f"Current bullets: {self.game.inventory.get('bullets', 0)}")
            bullet_count.pack(pady=5)

            # Information section
            info_frame = ttk.LabelFrame(trade_window, text="Information")
            info_frame.pack(pady=10, padx=10, fill="x")
            ttk.Label(info_frame, 
                     text="• Each upgrade reduces reload/cooldown time\n" +
                          "• Costs increase with each upgrade\n" +
                          "• Press 'E' to switch weapons\n" +
                          "• Press 'R' to reload rifle").pack(pady=5)

        elif villager_type == "chef":
            # Sell meat frame
            trade_frame = ttk.LabelFrame(trade_window, text="Sell Food")
            trade_frame.pack(pady=10, padx=10, fill="x")

            # Create combobox with prices
            buy_items = self.game.villager_buy_items[villager_type]
            combobox_values = []
            for item_name, price in buy_items.items():
                combobox_values.append(f"{item_name} ({price} coins)")
                
            # Selling meat
            sell_items = ttk.Combobox(trade_frame, values=combobox_values)
            sell_items.pack(pady=5)

            amount_var = tk.StringVar(value="1")
            amount_entry = ttk.Entry(trade_frame, textvariable=amount_var)
            amount_entry.pack(pady=5)

            # Frame for buttons
            button_frame = ttk.Frame(trade_frame)
            button_frame.pack(pady=5, fill="x")

            def sell():
                item_with_price = sell_items.get()
                if not item_with_price:
                    self.append_to_output("Please select an item to sell")
                    return
                    
                # Extract item name from the combobox text (removing price)
                item = item_with_price.split(" (")[0]
                
                try:
                    amount = int(amount_var.get())
                    if amount > 0:
                        success, message = self.game.attempt_trade(villager_type, "sell", item, amount)
                        self.append_to_output(message)
                        self.update_inventory_display()
                except ValueError:
                    self.append_to_output("Please enter a valid number")

            ttk.Button(button_frame, text="Sell", command=sell).pack(side=tk.LEFT, padx=5)
            
            def sell_all():
                item_with_price = sell_items.get()
                if not item_with_price:
                    self.append_to_output("Please select an item to sell all of")
                    return
                
                # Extract item name from the combobox text (removing price)
                item = item_with_price.split(" (")[0]
                
                # Get the amount from inventory
                amount = self.game.inventory.get(item, 0)
                if amount <= 0:
                    self.append_to_output(f"You don't have any {item} to sell")
                    return
                    
                success, message = self.game.attempt_trade(villager_type, "sell", item, amount)
                self.append_to_output(message)
                self.update_inventory_display()
            
            ttk.Button(button_frame, text="Sell All", command=sell_all).pack(side=tk.LEFT, padx=5)

            # Meal crafting frame
            meal_frame = ttk.LabelFrame(trade_window, text="Craft Meals")
            meal_frame.pack(pady=10, padx=10, fill="x")

            meal_types = ["chicken", "venison", "bear", "bird"]
            meal_var = tk.StringVar(value=meal_types[0])

            for meal_type in meal_types:
                ttk.Radiobutton(meal_frame, text=f"{meal_type.title()} Meal", 
                              variable=meal_var, value=meal_type).pack(pady=2)

            def craft_meal():
                meal_type = meal_var.get()
                if meal_type:
                    success, message = self.game.attempt_trade(
                        villager_type, "craft_meal", f"{meal_type} meat", 5)
                    self.append_to_output(message)
                    self.update_inventory_display()

            ttk.Button(meal_frame, text="Craft Meal (5 meat + 100 coins)", 
                      command=craft_meal).pack(pady=5)

            # Information section
            info_frame = ttk.LabelFrame(trade_window, text="Information")
            info_frame.pack(pady=10, padx=10, fill="x")
            ttk.Label(info_frame, text="• Meals restore 25% health and energy").pack(pady=2)
            ttk.Label(info_frame, text="• Automatic consumption when mining").pack(pady=2)
            ttk.Label(info_frame, text="• Each meal requires 5 of the same meat type").pack(pady=2)
            ttk.Label(info_frame, text="• Crafting cost: 100 coins").pack(pady=2)

            # Show prices
            prices_frame = ttk.LabelFrame(trade_window, text="Selling Prices")
            prices_frame.pack(pady=10, padx=10, fill="x")
            for item, price in self.game.villager_buy_items[villager_type].items():
                ttk.Label(prices_frame, text=f"{item}: {price} coins").pack(pady=2)

        elif villager_type == "blacksmith":
            ttk.Label(trade_window, text="Smelting Workshop", font=('Helvetica', 14, 'bold')).pack(pady=5)

            # Create frame for ore display
            ore_frame = ttk.LabelFrame(trade_window, text="Available Ore")
            ore_frame.pack(pady=10, padx=10, fill="x")

            # Show current ore amounts
            copper_amount = self.game.inventory.get("copper ore", 0)
            iron_amount = self.game.inventory.get("iron ore", 0)

            # Smelting buttons frame
            smelt_frame = ttk.LabelFrame(trade_window, text="Smelt Ore into Bars")
            smelt_frame.pack(pady=10, padx=10, fill="x")

            def smelt_copper():
                success, message = self.game.attempt_trade("blacksmith", "smelt", "copper", 1)
                self.append_to_output(message)
                self.update_inventory_display()
                # Update both ore displays after smelting
                copper_label.config(text=f"Copper Ore: {self.game.inventory.get('copper ore', 0)}")
                iron_label.config(text=f"Iron Ore: {self.game.inventory.get('iron ore', 0)}")

            def smelt_iron():
                success, message = self.game.attempt_trade("blacksmith", "smelt", "iron", 1)
                self.append_to_output(message)
                self.update_inventory_display()
                # Update both ore displays after smelting
                copper_label.config(text=f"Copper Ore: {self.game.inventory.get('copper ore', 0)}")
                iron_label.config(text=f"Iron Ore: {self.game.inventory.get('iron ore', 0)}")

            # Store labels for updating
            copper_label = ttk.Label(ore_frame, text=f"Copper Ore: {copper_amount}")
            iron_label = ttk.Label(ore_frame, text=f"Iron Ore: {iron_amount}")

            # Copper smelting section with clearer labeling
            copper_frame = ttk.Frame(smelt_frame)
            copper_frame.pack(pady=5, fill="x")
            ttk.Label(copper_frame, text="Copper Bar (requires 5 copper ore)").pack(side="left", padx=10)
            ttk.Button(copper_frame, text="Smelt Copper", command=smelt_copper).pack(side="right", padx=10)

            # Iron smelting section with clearer labeling
            iron_frame = ttk.Frame(smelt_frame)
            iron_frame.pack(pady=5, fill="x")
            ttk.Label(iron_frame, text="Iron Bar (requires 5 iron ore)").pack(side="left", padx=10)
            ttk.Button(iron_frame, text="Smelt Iron", command=smelt_iron).pack(side="right", padx=10)

            # Replace duplicate labels with the updating ones
            copper_label.pack(pady=5)
            iron_label.pack(pady=5)

            # Information section
            info_frame = ttk.LabelFrame(trade_window, text="Information")
            info_frame.pack(pady=10, padx=10, fill="x")
            ttk.Label(info_frame, text="• Each bar requires 5 ore of the same type").pack(pady=5)
            ttk.Label(info_frame, text="• Bars are used for tool upgrades").pack(pady=5)
            ttk.Label(info_frame, text="• The process is irreversible").pack(pady=5)

        elif villager_type == "toolsmith":
            # Buy basic tools with dropdown
            buy_frame = ttk.LabelFrame(trade_window, text="Buy Tools")
            buy_frame.pack(pady=10, padx=10, fill="x")

            # Create combobox with prices
            available_items = self.game.villager_sell_items[villager_type]
            combobox_values = []
            for item_name, price in available_items.items():
                combobox_values.append(f"{item_name} ({price} coins)")
            
            buy_items = ttk.Combobox(buy_frame, values=combobox_values)
            buy_items.pack(pady=5)
            buy_items.set("Select a tool")

            def buy():
                item_with_price = buy_items.get()
                if not item_with_price or item_with_price == "Select a tool":
                    self.append_to_output("Please select a tool to buy")
                    return
                    
                # Extract item name from the combobox text (removing price)
                item = item_with_price.split(" (")[0]
                
                success, message = self.game.attempt_trade(villager_type, "buy", item, 1)
                self.append_to_output(message)
                self.update_inventory_display()

            ttk.Button(buy_frame, text="Buy", command=buy).pack(pady=5)

            # Upgrade tools
            ttk.Label(trade_window, text="Upgrade Tools").pack(pady=15)
            upgrade_frame = ttk.Frame(trade_window)
            upgrade_frame.pack(pady=5)

            ttk.Label(upgrade_frame, text="Tool:").pack(side=tk.LEFT)
            tool_var = tk.StringVar(value="shovel")
            ttk.Radiobutton(upgrade_frame, text="Shovel", 
                          variable=tool_var, value="shovel").pack(side=tk.LEFT)
            ttk.Radiobutton(upgrade_frame, text="Pickaxe", 
                          variable=tool_var, value="pickaxe").pack(side=tk.LEFT)

            tier_frame = ttk.Frame(trade_window)
            tier_frame.pack(pady=5)

            ttk.Label(tier_frame, text="Upgrade to:").pack(side=tk.LEFT)
            tier_var = tk.StringVar(value="copper")
            ttk.Radiobutton(tier_frame, text="Copper", 
                          variable=tier_var, value="copper").pack(side=tk.LEFT)
            ttk.Radiobutton(tier_frame, text="Iron", 
                          variable=tier_var, value="iron").pack(side=tk.LEFT)

            def upgrade():
                tool = tool_var.get()
                tier = tier_var.get()
                if tool and tier:
                    success, message = self.game.attempt_trade(
                        villager_type, "upgrade", f"{tool}->{tier}", 1)
                    self.append_to_output(message)
                    self.update_inventory_display()

            ttk.Button(trade_window, text="Upgrade", command=upgrade).pack(pady=5)

            # Show costs
            costs_text = tk.Text(trade_window, height=6, width=40)
            costs_text.pack(pady=10)
            costs_text.insert(tk.END, "Upgrade Costs:\n\n")
            costs_text.insert(tk.END, "Copper Shovel: 300 coins + 2 copper bars\n")
            costs_text.insert(tk.END, "Iron Shovel: 500 coins + 3 iron bars\n")
            costs_text.insert(tk.END, "Copper Pickaxe: 450 coins + 3 copper bars\n")
            costs_text.insert(tk.END, "Iron Pickaxe: 750 coins + 4 iron bars\n")
            costs_text.config(state=tk.DISABLED)

        else:
            # Regular buying/selling for other vendors
            # Create frames for selling
            sell_frame = ttk.LabelFrame(trade_window, text="Sell Items")
            sell_frame.pack(pady=10, padx=10, fill="x")

            # Only show sell frame if vendor buys items
            if villager_type in self.game.villager_buy_items and self.game.villager_buy_items[villager_type]:
                # Create combobox with prices
                buy_items = self.game.villager_buy_items[villager_type]
                combobox_values = []
                for item_name, price in buy_items.items():
                    combobox_values.append(f"{item_name} ({price} coins)")
                    
                sell_items = ttk.Combobox(sell_frame, values=combobox_values)
                sell_items.pack(pady=5)

                amount_var = tk.StringVar(value="1")
                amount_entry = ttk.Entry(sell_frame, textvariable=amount_var)
                amount_entry.pack(pady=5)

                # Frame for sell buttons
                button_frame = ttk.Frame(sell_frame)
                button_frame.pack(pady=5, fill="x")

                def sell():
                    item_with_price = sell_items.get()
                    if not item_with_price:
                        self.append_to_output("Please select an item to sell")
                        return
                        
                    # Extract item name from the combobox text (removing price)
                    item = item_with_price.split(" (")[0]
                    try:
                        amount = int(amount_var.get())
                        success, message = self.game.attempt_trade(villager_type, "sell", item, amount)
                        self.append_to_output(message)
                        self.update_inventory_display()
                    except ValueError:
                        self.append_to_output("Please enter a valid amount")

                ttk.Button(button_frame, text="Sell", command=sell).pack(side=tk.LEFT, padx=5)
                
                def sell_all():
                    item_with_price = sell_items.get()
                    if not item_with_price:
                        self.append_to_output("Please select an item to sell all of")
                        return
                    
                    # Extract item name from the combobox text (removing price)
                    item = item_with_price.split(" (")[0]
                    
                    # Get the amount from inventory
                    amount = self.game.inventory.get(item, 0)
                    if amount <= 0:
                        self.append_to_output(f"You don't have any {item} to sell")
                        return
                        
                    success, message = self.game.attempt_trade(villager_type, "sell", item, amount)
                    self.append_to_output(message)
                    self.update_inventory_display()
                
                ttk.Button(button_frame, text="Sell All", command=sell_all).pack(side=tk.LEFT, padx=5)

            # Create frames for buying
            buy_frame = ttk.LabelFrame(trade_window, text="Buy Items")
            buy_frame.pack(pady=10, padx=10, fill="x")

            # Only show buy frame if vendor sells items
            if villager_type in self.game.villager_sell_items and self.game.villager_sell_items[villager_type]:
                # Create combobox with prices
                sell_items = self.game.villager_sell_items[villager_type]
                combobox_values = []
                for item_name, price in sell_items.items():
                    combobox_values.append(f"{item_name} ({price} coins)")
                
                buy_items = ttk.Combobox(buy_frame, values=combobox_values)
                buy_items.pack(pady=5)
                buy_items.set("Select an item")

                amount_var = tk.StringVar(value="1")
                amount_entry = ttk.Entry(buy_frame, textvariable=amount_var)
                amount_entry.pack(pady=5)

                def buy():
                    item_with_price = buy_items.get()
                    if not item_with_price or item_with_price == "Select an item":
                        self.append_to_output("Please select an item to buy")
                        return
                        
                    # Extract item name from the combobox text (removing price)
                    item = item_with_price.split(" (")[0]
                    try:
                        amount = int(amount_var.get())
                        success, message = self.game.attempt_trade(villager_type, "buy", item, amount)
                        self.append_to_output(message)
                        self.update_inventory_display()
                    except ValueError:
                        self.append_to_output("Please enter a valid amount")

                ttk.Button(buy_frame, text="Buy", command=buy).pack(pady=5)

    def show_house_interaction(self, parent, has_lights=True, town_type='small'):
        status = "with" if has_lights else "without"
        if has_lights:
            from house_loot_game import start_house_loot_game
            start_house_loot_game(parent, self.game)
        else:
            if randint(0, 1) == 1:
                town_probabilities = {
                    'small': {'items': 0.7, 'coins': 0.3},
                    'medium': {'items': 0.5, 'coins': 0.5},
                    'large': {'items': 0.3, 'coins': 0.7}
                }

                possible_items = {
                    'lockpick': 0.3,
                    'iron ore': 0.2,
                    'copper ore': 0.2,
                    'iron bar': 0.15,
                    'shovel': 0.1,
                    'pickaxe': 0.05
                }

                if random.random() < town_probabilities[town_type]['items']:
                    item = random.choices(
                        list(possible_items.keys()),
                        weights=list(possible_items.values())
                    )[0]
                    amount = randint(1, 2)
                    self.game.add_inventory_item(item, amount)
                    self.append_to_output(f"You snuck in and found {amount} {item}!")
                else:
                    base_amount = {
                        'small': (10, 30),
                        'medium': (20, 50),
                        'large': (40, 100)
                    }[town_type]
                    coins_found = randint(base_amount[0], base_amount[1])
                    self.game.coins += coins_found
                    self.append_to_output(f"You snuck in and found {coins_found} coins!")
            else:
                self.append_to_output("The house is empty, and you found nothing of value.")

    def switch_weapon(self, weapon_type):
        success, message = self.game.switch_weapon(weapon_type)
        self.append_to_output(message)
        self.update_inventory_display()

    def run(self):
        terrain = self.game.get_current_terrain_description()
        self.append_to_output(f"Starting location: {terrain}")
        self.update_action_buttons()
        self.root.mainloop()

if __name__ == "__main__":
    try:
        # Import and initialize key modules
        print("Starting the game...")
        
        # Create and run the game
        game = GameGUI()
        game.run()
        
    except Exception as e:
        print(f"Error running game: {str(e)}")
        traceback.print_exc()
        
        # Show error in a messagebox if possible
        try:
            messagebox.showerror("Game Error", f"An error occurred:\n{str(e)}\n\nSee console for details.")
        except:
            # If even the messagebox fails, just print to console
            print("Could not display error messagebox.")