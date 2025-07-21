import tkinter as tk
from tkinter import ttk, messagebox
import random
from random import randint, choice, random as rand_float
from enum import Enum

class EnemyType(Enum):
    # City enemies
    BANDIT = {"tier": 1, "hp": 30, "damage": 5, "drops": {"coins": (10, 20), "lockpick": 0.3}}
    GUARD = {"tier": 2, "hp": 50, "damage": 8, "drops": {"coins": (20, 40), "iron_bar": 0.2}}
    KNIGHT = {"tier": 3, "hp": 80, "damage": 12, "drops": {"coins": (40, 80), "advanced_map": 0.1}}

    # Forest enemies
    WOLF = {"tier": 1, "hp": 25, "damage": 6, "drops": {"coins": (8, 15), "wolf_pelt": 0.5}}
    ARCHER = {"tier": 2, "hp": 40, "damage": 10, "drops": {"coins": (15, 30), "arrows": 0.4}}
    ENT = {"tier": 3, "hp": 100, "damage": 15, "drops": {"coins": (30, 60), "magic_wood": 0.3}}

    # Plains enemies
    TOURIST = {"tier": 1, "hp": 20, "damage": 3, "drops": {"coins": (15, 25), "map": 0.4}}
    HUNTER = {"tier": 2, "hp": 45, "damage": 7, "drops": {"coins": (25, 45), "bullets": 0.3}}
    BUFFALO = {"tier": 3, "hp": 90, "damage": 14, "drops": {"coins": (35, 70), "leather": 0.5}}

    # Water enemies
    CRAB = {"tier": 1, "hp": 22, "damage": 4, "drops": {"coins": (12, 18), "crab_meat": 0.6}}
    SHARK = {"tier": 2, "hp": 55, "damage": 9, "drops": {"coins": (22, 38), "shark_fin": 0.3}}
    MERMAN = {"tier": 3, "hp": 70, "damage": 11, "drops": {"coins": (45, 75), "pearl": 0.2}}

class Enemy:
    def __init__(self, enemy_type):
        self.type = enemy_type
        self.name = enemy_type.name.lower().replace('_', ' ').title()
        self.max_hp = enemy_type.value["hp"]
        self.hp = self.max_hp
        
        # Store base damage for reference
        self.base_damage = enemy_type.value["damage"]
        
        # Set up dice configuration based on tier
        tier = enemy_type.value["tier"]
        if tier == 1:
            self.num_dice = 1
            self.dice_sides = 6
            self.modifier = 1
        elif tier == 2:
            self.num_dice = 2
            self.dice_sides = 6
            self.modifier = 2
        else:  # Tier 3
            self.num_dice = 3
            self.dice_sides = 8
            self.modifier = 3
        
        self.drops = enemy_type.value["drops"]

    def attack(self):
        # Roll the dice to determine damage
        total = sum(randint(1, self.dice_sides) for _ in range(self.num_dice))
        return total + self.modifier

    def take_damage(self, damage):
        self.hp = max(0, self.hp - damage)
        return self.hp <= 0

    def get_drops(self):
        drops = {}
        for item, chance in self.drops.items():
            if isinstance(chance, tuple):
                drops[item] = randint(chance[0], chance[1])
            elif rand_float() < chance:
                drops[item] = 1
        return drops

class CombatGame(tk.Toplevel):
    def __init__(self, parent, game_state, stronghold_tier, surrounding_terrains):
        super().__init__(parent)
        self.title("Combat")
        self.geometry("800x600")

        self.game_state = game_state
        self.tier = stronghold_tier
        self.enemy = self.generate_enemy(surrounding_terrains)
        self.player_hp = 100  # Base player HP

        self.setup_ui()
        self.update_status()

    def generate_enemy(self, surrounding_terrains):
        # Count terrain types
        terrain_counts = {}
        total_tiles = len(surrounding_terrains)

        for terrain in surrounding_terrains:
            if terrain in terrain_counts:
                terrain_counts[terrain] += 1
            else:
                terrain_counts[terrain] = 1

        # Select terrain based on probabilities
        terrain_choice = random.choices(
            list(terrain_counts.keys()),
            weights=[count/total_tiles for count in terrain_counts.values()]
        )[0]

        # Get appropriate enemies for the chosen terrain and tier
        enemy_pool = []
        if terrain_choice in ['T', 'T_small', 'T_medium', 'T_large']:  # City
            enemy_pool = [EnemyType.BANDIT, EnemyType.GUARD, EnemyType.KNIGHT]
        elif terrain_choice == 'F':  # Forest
            enemy_pool = [EnemyType.WOLF, EnemyType.ARCHER, EnemyType.ENT]
        elif terrain_choice == 'P':  # Plains
            enemy_pool = [EnemyType.TOURIST, EnemyType.HUNTER, EnemyType.BUFFALO]
        elif terrain_choice in ['O', 'C', 'B']:  # Water (Ocean, Coast, Beach)
            enemy_pool = [EnemyType.CRAB, EnemyType.SHARK, EnemyType.MERMAN]
        else:  # Default to city enemies if terrain type not recognized
            enemy_pool = [EnemyType.BANDIT, EnemyType.GUARD, EnemyType.KNIGHT]

        # Ensure tier is valid (1-3)
        tier_index = max(0, min(2, self.tier - 1))
        enemy_type = enemy_pool[tier_index]
        return Enemy(enemy_type)

    def setup_ui(self):
        # Main combat frame with ascii art style border
        combat_frame = ttk.Frame(self)
        combat_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # ASCII art border
        border = ttk.Label(combat_frame, text="+" + "-"*70 + "+", font=('Courier', 12))
        border.pack()

        # Enemy info section
        enemy_frame = ttk.Frame(combat_frame)
        enemy_frame.pack(pady=10)

        self.enemy_name = ttk.Label(enemy_frame, 
                                  text=f"You are fighting a mighty {self.enemy.name}!",
                                  font=('Courier', 14, 'bold'))
        self.enemy_name.pack()

        self.enemy_hp_bar = ttk.Label(enemy_frame, 
                                    text=self.generate_hp_bar(self.enemy.hp, self.enemy.max_hp),
                                    font=('Courier', 12))
        self.enemy_hp_bar.pack()

        # Combat log
        self.combat_log = tk.Text(combat_frame, height=10, width=60, font=('Courier', 10))
        self.combat_log.pack(pady=10)
        self.combat_log.config(state="disabled")

        # Player status
        player_frame = ttk.Frame(combat_frame)
        player_frame.pack(pady=10)

        self.player_hp_label = ttk.Label(player_frame, 
                                       text=self.generate_hp_bar(self.player_hp, 100, "You"),
                                       font=('Courier', 12))
        self.player_hp_label.pack()

        # Action buttons frame with Kingdom of Loathing style
        action_frame = ttk.Frame(combat_frame)
        action_frame.pack(pady=10)

        weapon = self.game_state.get_current_weapon("combat")  # Specify combat weapon
        weapon_name = weapon.name
        
        # Display dice format: 2d6+2 (avg: 9.0)
        dice_text = f"{weapon.num_dice}d{weapon.dice_sides}+{weapon.modifier}"
        avg_damage = weapon.calculate_avg_damage()
        damage_text = f"Attack with {weapon_name} (Damage: {dice_text}, avg: {avg_damage})"

        ttk.Button(action_frame, text=damage_text, 
                  command=self.player_attack).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Use Item", 
                  command=self.use_item).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Run Away", 
                  command=self.attempt_run).pack(side="left", padx=5)

        # Bottom border
        border = ttk.Label(combat_frame, text="+" + "-"*70 + "+", font=('Courier', 12))
        border.pack()

        self.log_message(f"A {self.enemy.name} approaches! Prepare for battle!")

    def generate_hp_bar(self, current, maximum, name="Enemy"):
        percentage = (current / maximum) * 100
        bar_length = 20
        filled = int((percentage / 100) * bar_length)
        bar = "=" * filled + "-" * (bar_length - filled)
        return f"{name} HP: [{bar}] {current}/{maximum}"

    def log_message(self, message):
        self.combat_log.config(state="normal")
        self.combat_log.insert("end", message + "\n")
        self.combat_log.see("end")
        self.combat_log.config(state="disabled")

    def update_status(self):
        if not self.winfo_exists():
            return
        try:
            self.enemy_hp_bar.config(text=self.generate_hp_bar(self.enemy.hp, self.enemy.max_hp))
            self.player_hp_label.config(text=self.generate_hp_bar(self.player_hp, 100, "You"))
        except tk.TclError:
            pass  # Widget was destroyed

    def player_attack(self):
        if not self.winfo_exists():
            return

        # Get combat weapon and roll for damage using the dice system
        weapon = self.game_state.get_current_weapon("combat")
        damage = weapon.roll_damage()  # Uses the randomized dice configuration

        # Apply damage to enemy
        killed = self.enemy.take_damage(damage)
        
        # Simple combat message without dice notation
        self.log_message(f"You hit the {self.enemy.name} with your {weapon.name} for {damage} damage!")

        if killed:
            self.handle_victory()
        elif self.winfo_exists():  # Check if window still exists
            self.enemy_turn()
            self.update_status()

    def enemy_turn(self):
        damage = self.enemy.attack()
        self.player_hp -= damage
        
        # Simple combat message without dice notation
        self.log_message(f"The {self.enemy.name} hits you for {damage} damage!")

        if self.player_hp <= 0:
            self.handle_defeat()

        self.update_status()

    def use_item(self):
        # Show available healing items
        items_window = tk.Toplevel(self)
        items_window.title("Use Item")

        healing_items = {
            "chicken_meal": 25,
            "venison_meal": 25,
            "bear_meal": 25,
            "bird_meal": 25
        }

        for item, heal_amount in healing_items.items():
            if self.game_state.inventory.get(item, 0) > 0:
                def make_use_command(item_name, heal):
                    def use():
                        self.game_state.inventory[item_name] -= 1
                        self.player_hp = min(100, self.player_hp + heal)
                        self.log_message(f"Used {item_name} to heal {heal} HP!")
                        self.update_status()
                        items_window.destroy()
                        self.enemy_turn()
                    return use

                ttk.Button(items_window, 
                          text=f"{item} (Heal {heal_amount})", 
                          command=make_use_command(item, heal_amount)).pack(pady=2)

    def attempt_run(self):
        if rand_float() < 0.5:  # 50% chance to run
            self.log_message("You successfully ran away!")
            self.after(1000, self.destroy)
        else:
            self.log_message("Couldn't escape!")
            self.enemy_turn()

    def handle_victory(self):
        self.log_message(f"You defeated the {self.enemy.name}!")
        drops = self.enemy.get_drops()

        drop_message = "You received:\n"
        for item, amount in drops.items():
            if item == "coins":
                self.game_state.coins += amount
                drop_message += f"{amount} coins\n"
            else:
                self.game_state.add_inventory_item(item, amount)
                drop_message += f"{amount} {item}\n"

        messagebox.showinfo("Victory", drop_message)
        self.destroy()

    def handle_defeat(self):
        lost_coins = self.game_state.coins // 4  # Lose 25% of coins
        self.game_state.coins -= lost_coins

        messagebox.showinfo("Defeat", 
                          f"You were defeated by the {self.enemy.name}!\n"
                          f"You lost {lost_coins} coins.")
        self.destroy()

def start_combat(parent, game_state, stronghold_tier, surrounding_terrains):
    return CombatGame(parent, game_state, stronghold_tier, surrounding_terrains)