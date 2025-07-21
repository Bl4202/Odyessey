import json
import os
from random import randint, choice, random, uniform, seed
from math import floor
from collections import defaultdict
import random
from enum import Enum
import noise
import uuid

# Weapon system revamp
class WeaponTier(Enum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_4 = 4
    TIER_5 = 5

class WeaponType(Enum):
    HUNTING = "hunting"
    COMBAT = "combat"
    # Hunting weapons
    REVOLVER = "revolver"
    HUNTING_RIFLE = "hunting_rifle"

class Weapon:
    # Dice configurations for each tier (number of dice, sides per dice, modifier)
    dice_configs = {
        1: (1, 6, 2),    # 1d6+2 (avg: 5.5)
        2: (2, 6, 2),    # 2d6+2 (avg: 9)
        3: (3, 8, 4),    # 3d8+4 (avg: 17.5)
        4: (4, 10, 6),   # 4d10+6 (avg: 28)
        5: (6, 12, 10)   # 6d12+10 (avg: 49)
    }

    # Base damage range for each tier (for cost calculations)
    damage_ranges = {
        1: (4, 8),
        2: (6, 14),
        3: (12, 28),
        4: (16, 46),
        5: (28, 82)
    }

    def __init__(self, weapon_id=None, name=None, weapon_type=WeaponType.COMBAT, tier=1, dice_config=None):
        self.id = weapon_id or str(uuid.uuid4())
        self.weapon_type = weapon_type
        self.tier = tier

        # Generate name if not provided
        self.name = name or self.generate_name()

        # Set dice configuration for the weapon - randomized within tier
        if dice_config:
            self.dice_config = dice_config
        else:
            # Get the default configuration for this tier as a starting point
            default_config = self.dice_configs[self.tier]
            
            # Randomize the dice configuration while keeping overall power level similar
            if self.tier == 1:
                # Tier 1: Variations like 1d6+2, 1d8+1, 2d4+1, etc.
                dice_options = [(1, 6, 2), (1, 8, 1), (2, 4, 1), (2, 3, 2)]
                self.dice_config = choice(dice_options)  # Use 'choice' from random imported at the top
            elif self.tier == 2:
                # Tier 2: Variations like 2d6+2, 3d4+2, 2d8+1, 1d10+4, etc.
                dice_options = [(2, 6, 2), (3, 4, 2), (2, 8, 1), (1, 10, 4), (2, 5, 3)]
                self.dice_config = choice(dice_options)
            elif self.tier == 3:
                # Tier 3: Variations like 3d8+4, 2d12+2, 4d6+3, etc.
                dice_options = [(3, 8, 4), (2, 12, 2), (4, 6, 3), (3, 10, 2), (5, 4, 5)]
                self.dice_config = choice(dice_options)
            elif self.tier == 4:
                # Tier 4: Variations like 4d10+6, 6d6+8, 3d12+8, etc.
                dice_options = [(4, 10, 6), (6, 6, 8), (3, 12, 8), (5, 8, 6), (4, 12, 4)]
                self.dice_config = choice(dice_options)
            else:  # Tier 5
                # Tier 5: Variations like 6d12+10, 8d8+12, 5d20+5, etc.
                dice_options = [(6, 12, 10), (8, 8, 12), (5, 20, 5), (7, 10, 10), (10, 6, 15)]
                self.dice_config = choice(dice_options)
        
        self.num_dice = self.dice_config[0]
        self.dice_sides = self.dice_config[1]
        self.modifier = self.dice_config[2]
        
        # For display and cost calculation purposes
        self.avg_damage = self.calculate_avg_damage()

        self.last_shot_time = 0
        self.is_reloading = False
        self.reload_start_time = 0
        self.upgrade_level = 0

    def generate_name(self):
        prefixes = [
            "Rusty", "Ancient", "Gleaming", "Shadow", "Light", "Burning", 
            "Frozen", "Mystic", "Arcane", "Divine", "Infernal", "Blessed", 
            "Cursed", "Royal", "Forgotten", "Deadly", "Swift", "Mighty",
            "Vengeful", "Savage", "Precise", "Brutal", "Elegant", "Vicious"
        ]

        weapon_types = [
            "Blade", "Sword", "Saber", "Rapier", "Claymore", "Dagger", 
            "Slicer", "Cutter", "Reaver", "Fang", "Edge", "Bane", 
            "Slayer", "Cleaver", "Maul", "Destroyer", "Vanquisher"
        ]

        suffixes = [
            "of Power", "of Might", "of Glory", "of Triumph", "of Victory",
            "of Ruin", "of Doom", "of Despair", "of Sorrow", "of Agony",
            "of Souls", "of Eternity", "of Infinity", "of the Lion", 
            "of the Dragon", "of the Phoenix", "of the Serpent"
        ]

        # Higher tier weapons get more elaborate names
        if self.tier >= 3:
            return f"{choice(prefixes)} {choice(weapon_types)} {choice(suffixes)}"
        elif self.tier == 2:
            return f"{choice(prefixes)} {choice(weapon_types)}"
        else:
            return f"{choice(weapon_types)}"

    def calculate_avg_damage(self):
        """Calculate the average damage for this weapon based on dice configuration"""
        # Calculate average roll of the dice: (sides+1)/2 * num_dice + modifier
        avg = (self.dice_sides + 1) / 2 * self.num_dice + self.modifier
        return round(avg, 1)
        
    def roll_damage(self):
        """Roll the dice to determine actual damage dealt"""
        # Roll each die and add them up
        total = sum(randint(1, self.dice_sides) for _ in range(self.num_dice))
        # Add the modifier
        return total + self.modifier
        
    def generate_damage(self):
        """Legacy method for backward compatibility"""
        return self.calculate_avg_damage()

    def get_cost(self):
        # Base cost calculation based on tier and dice configuration
        base_costs = {
            1: 100,
            2: 300,
            3: 600,
            4: 1200,
            5: 2500
        }

        base_cost = base_costs[self.tier]
        min_damage, max_damage = self.damage_ranges[self.tier]
        
        # Use average damage to calculate price
        avg_damage = self.calculate_avg_damage()
        damage_factor = avg_damage / max_damage  # Normalize damage to 0-1 range
        
        return int(base_cost * (0.8 + (damage_factor * 0.4)))  # 20% variance based on damage

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'weapon_type': self.weapon_type.value,
            'tier': self.tier,
            'dice_config': self.dice_config,
            'upgrade_level': self.upgrade_level
        }

    @classmethod
    def from_dict(cls, data):
        weapon = cls(
            weapon_id=data.get('id'),
            name=data.get('name'),
            weapon_type=WeaponType(data.get('weapon_type', 'combat')),
            tier=data.get('tier', 1),
            dice_config=data.get('dice_config')
        )
        weapon.upgrade_level = data.get('upgrade_level', 0)
        return weapon

    def get_current_cooldown(self):
        # Base cooldown determined by weapon tier (higher tier = slightly faster cooldown)
        base_cooldown = 2.0 - (self.tier * 0.2)
        if self.weapon_type == WeaponType.HUNTING:
            base_cooldown += 1.0  # Hunting weapons have longer cooldown

        # Upgrades reduce cooldown
        if self.upgrade_level > 0:
            reduction = 0.15 * self.upgrade_level
            return max(0.5, base_cooldown * (1 - reduction))
        return base_cooldown

    def can_shoot(self, current_time):
        if self.weapon_type == WeaponType.HUNTING and self.tier >= 3:
            # High tier hunting weapons need reload
            if self.is_reloading:
                if current_time - self.reload_start_time >= self.get_current_cooldown():
                    self.is_reloading = False
                    return True
                return False
            return True
        else:  
            return current_time - self.last_shot_time >= self.get_current_cooldown()

    def shoot(self, current_time):
        if not self.can_shoot(current_time):
            return 0

        self.last_shot_time = current_time
        if self.weapon_type == WeaponType.HUNTING and self.tier >= 3:
            self.is_reloading = True
            self.reload_start_time = current_time
        
        # Roll for damage using the dice system
        return self.roll_damage()

    def start_reload(self, current_time):
        if self.weapon_type == WeaponType.HUNTING and self.tier >= 3:
            self.is_reloading = True
            self.reload_start_time = current_time

    def get_upgrade_cost(self):
        # Higher tier weapons cost more to upgrade
        base_cost = self.tier * 100
        return {
            "copper_bars": self.tier + self.upgrade_level,
            "iron_bars": max(1, self.tier - 1) + self.upgrade_level,
            "coins": base_cost * (self.upgrade_level + 1)
        }

# Generate weapon shop inventory for forts
def generate_fort_inventory():
    inventory = []
    # One weapon from each tier
    for tier in range(1, 6):
        weapon = Weapon(tier=tier, weapon_type=WeaponType.COMBAT)
        inventory.append(weapon)
    return inventory

class WorldMap:
    def __init__(self):
        self.map = defaultdict(lambda: defaultdict(str))
        self.town_types = {}
        self.town_names = {}
        self.mineshafts = set()
        self.town_layouts = {}
        self.looted_houses = set()
        self.forest_wood = defaultdict(lambda: 20)
        self.seed = random.randint(0, 1000000)
        self.fort_inventories = {}  # Store weapon inventories for each fort
        self.generate_initial_area()
        self.npc_names = {}

    def get_fort_inventory(self, x, y):
        if (x, y) not in self.fort_inventories:
            self.fort_inventories[(x, y)] = generate_fort_inventory()
        return self.fort_inventories[(x, y)]

    def get_town_name(self, x, y):
        if (x, y) not in self.town_names:
            town_type = self.town_types.get((x, y))
            if town_type:
                self.town_names[(x, y)] = generate_town_name(town_type)
        return self.town_names.get((x, y), "Unknown Town")

    def get_npc_name(self, x, y, profession):
        key = (x, y, profession)
        if key not in self.npc_names:
            self.npc_names[key] = generate_npc_name(profession)
        return self.npc_names[key]

    def get_forest_color(self, x, y):
        wood_left = self.forest_wood[(x, y)]
        if wood_left <= 0:
            return '#90EE90'
        elif wood_left <= 5:
            return '#228B22'
        elif wood_left <= 10:
            return '#006400'
        else:
            return '#004d00'

    def deplete_forest(self, x, y, amount):
        self.forest_wood[(x, y)] = max(0, self.forest_wood[(x, y)] - amount)
        if self.forest_wood[(x, y)] <= 0:
            self.map[y][x] = 'P'
            return True
        return False

    def is_ocean(self, x, y):
        scale = 15.0
        octaves = 1
        persistence = 0.5
        lacunarity = 2.0
        value = noise.pnoise2(x/scale, 
                            y/scale, 
                            octaves=octaves, 
                            persistence=persistence,
                            lacunarity=lacunarity,
                            repeatx=1000,
                            repeaty=1000,
                            base=self.seed)
        return value < -0.1

    def get_tile_type(self, x, y):
        if not self.is_ocean(x, y):
            return 'P'

        has_land_neighbor = False
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if not self.is_ocean(nx, ny):
                has_land_neighbor = True
                break

        if has_land_neighbor:
            return 'B'

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self.map[ny][nx] == 'B':
                return 'C'

        return 'O'

    def ensure_terrain_exists(self, x, y):
        if not self.map[y][x]:
            tile_type = self.get_tile_type(x, y)

            # Handle water-related tiles first
            if tile_type in ['O', 'B', 'C']:
                self.map[y][x] = tile_type
                return self.map[y][x]

            # Handle land-based features
            roll = random.random()
            if roll < 0.1:  # 10% chance for town
                self.map[y][x] = 'T'
                self.town_types[(x, y)] = choice(['small', 'medium', 'large'])
            elif roll < 0.15:  # 5% chance for temple
                self.map[y][x] = 'X'
            elif roll < 0.17:  # 2% chance for mineshaft
                self.map[y][x] = 'M'
                self.mineshafts.add((x, y))
            elif roll < 0.20:  # 3% chance for stronghold
                tier = random.randint(1, 3)
                self.map[y][x] = f'S{tier}'  # S1, S2, or S3 for different tiers
            elif roll < 0.30:  # 10% chance for forest
                self.map[y][x] = 'F'
                self.forest_wood[(x, y)] = 20
                # Create forest cluster
                for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                    if random.random() < 0.7:  # 70% chance to spread
                        nx, ny = x + dx, y + dy
                        if not self.map[ny][nx]:  # Only if tile is empty
                            self.map[ny][nx] = 'F'
                            self.forest_wood[(nx, ny)] = 20
            elif roll < 0.32: #2% chance for fort
                self.map[y][x] = 'F_F'
                # Generate fort inventory when creating the fort
                self.get_fort_inventory(x, y)
            else:
                self.map[y][x] = tile_type

        return self.map[y][x]

    def get_terrain(self, x, y):
        return self.ensure_terrain_exists(x, y)

    def get_town_type(self, x, y):
        return self.town_types.get((x, y))

    def store_town_layout(self, town_x, town_y, layout_data):
        self.town_layouts[(town_x, town_y)] = layout_data

    def get_town_layout(self, town_x, town_y):
        return self.town_layouts.get((town_x, town_y))

    def is_house_looted(self, town_x, town_y, house_x, house_y):
        return (town_x, town_y, house_x, house_y) in self.looted_houses

    def mark_house_looted(self, town_x, town_y, house_x, house_y):
        self.looted_houses.add((town_x, town_y, house_x, house_y))

    def generate_initial_area(self):
        for x in range(-2, 3):
            for y in range(-2, 3):
                self.ensure_terrain_exists(x, y)

    def can_move_to(self, x, y):
        terrain = self.get_terrain(x, y)
        return terrain != 'O'

    def to_dict(self):
        return {
            'map': {str(y): {str(x): tile for x, tile in row.items()} for y, row in self.map.items()},
            'town_types': self.town_types,
            'town_names': self.town_names,
            'mineshafts': list(self.mineshafts),
            'town_layouts': self.town_layouts,
            'looted_houses': list(self.looted_houses),
            'forest_wood': {f"{x},{y}": amount for (x, y), amount in self.forest_wood.items()},
            'npc_names': self.npc_names,
            'seed': self.seed,
            'fort_inventories': {f"{x},{y}": [w.to_dict() for w in weapons] 
                                for (x, y), weapons in self.fort_inventories.items()}
        }

    @classmethod
    def from_dict(cls, data):
        world_map = cls()
        world_map.seed = data['seed']
        for y, row in data['map'].items():
            for x, tile in row.items():
                world_map.map[int(y)][int(x)] = tile
        world_map.town_types = data['town_types']
        world_map.town_names = data.get('town_names', {})
        world_map.mineshafts = set(data['mineshafts'])
        world_map.town_layouts = data['town_layouts']
        world_map.looted_houses = set(data['looted_houses'])
        world_map.forest_wood = defaultdict(lambda: 20)
        for coord, amount in data.get('forest_wood', {}).items():
            x, y = map(int, coord.split(','))
            world_map.forest_wood[(x, y)] = amount
        world_map.npc_names = data.get('npc_names', {})

        # Load fort inventories
        for coord, weapons_data in data.get('fort_inventories', {}).items():
            x, y = map(int, coord.split(','))
            world_map.fort_inventories[(x, y)] = [Weapon.from_dict(w) for w in weapons_data]

        return world_map

    def get_stronghold_tier(self, x, y):
        terrain = self.get_terrain(x, y)
        if terrain.startswith('S'):
            return int(terrain[-1])
        return 0

    def get_surrounding_terrains(self, x, y):
        surroundings = []
        for dx, dy in [(0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1), (-1,0), (-1,1)]:
            nx, ny = x + dx, y + dy
            surroundings.append(self.get_terrain(nx, ny))
        return surroundings

def generate_town_name(size):
    prefixes = {
        'small': ['Little', 'Quiet', 'Peaceful', 'Hidden', 'Green', 'Sunny', 'Cozy', 'Meadow', 'Pine', 'Brook'],
        'medium': ['Silver', 'Golden', 'River', 'Lake', 'Forest', 'Market', 'Harbor', 'Mill', 'Bridge', 'Trade'],
        'large': ['Royal', 'Grand', 'Imperial', 'Great', 'Capital', 'Crown', 'High', 'Stone', 'Castle', 'King\'s']
    }
    suffixes = {
        'small': ['hamlet', 'brook', 'crossing', 'meadow', 'grove', 'glen', 'vale', 'rest', 'garden', 'spring'],
        'medium': ['port', 'town', 'market', 'bridge', 'mill', 'ford', 'haven', 'cross', 'field', 'wood'],
        'large': ['city', 'keep', 'castle', 'gate', 'spire', 'throne', 'realm', 'crown', 'shire', 'hold']
    }
    return f"{choice(prefixes[size])} {choice(suffixes[size])}".title()

def generate_npc_name(profession):
    first_names = [
        'John', 'William', 'Thomas', 'Henry', 'Edward', 'Arthur', 'Mary', 'Elizabeth', 'Anne', 'Margaret',
        'James', 'Robert', 'George', 'Charles', 'Richard', 'Emma', 'Sarah', 'Catherine', 'Alice', 'Jane'
    ]
    profession_titles = {
        'fisher': ['Sea', 'Storm', 'Wave', 'Salt', 'Tide', 'Shore', 'Shell', 'Harbor', 'Bay', 'Net'],
        'lumberjack': ['Wood', 'Oak', 'Pine', 'Forest', 'Axe', 'Timber', 'Cedar', 'Maple', 'Birch', 'Elm'],
        'blacksmith': ['Iron', 'Steel', 'Forge', 'Hammer', 'Fire', 'Anvil', 'Coal', 'Flame', 'Metal', 'Bronze'],
        'toolsmith': ['Craft', 'Smith', 'Work', 'Tool', 'Metal', 'Gear', 'Wrench', 'Maker', 'Builder', 'Trade'],
        'gunsmith': ['Gun', 'Powder', 'Shot', 'Arms', 'Steel', 'Flint', 'Barrel', 'Trigger', 'Bullet', 'Lead'],
        'chef': ['Pan', 'Cook', 'Spice', 'Kitchen', 'Salt', 'Pepper', 'Sage', 'Thyme', 'Baker', 'Brew']
    }
    titles = profession_titles.get(profession, [''])
    name_type = random.choice(['profession', 'location'])
    if name_type == 'profession' and profession in profession_titles:
        last_name = f"{choice(titles)}{'smith' if 'smith' in profession else 'son'}"
    else:
        last_name = f"{choice(titles)}{'worth' if random.random() < 0.5 else 'ton'}"
    return f"{choice(first_names)} {last_name}"

class GameState:
    def __init__(self):
        self.items = {
            "iron": "mine for it underground.",
            "chicken meat": "hunt chickens in the plains.",
            "venison": "hunt deer in the plains.",
            "bear meat": "hunt bears in the plains.",
            "bird meat": "hunt birds in the plains.",
            "iron bar": "smelt 5 iron ore at the blacksmith.",
            "copper bar": "smelt 5 copper ore at the blacksmith.",
            "iron ore": "mine for it.",
            "copper ore": "mine for it.",
            "shovel": "buy it from the toolsmith.",
            "copper shovel": "upgrade basic shovel at the toolsmith.",
            "iron shovel": "upgrade copper shovel at the toolsmith.",
            "pickaxe": "buy it from the toolsmith.",
            "copper pickaxe": "upgrade basic pickaxe at the toolsmith.",
            "iron pickaxe": "upgrade copper pickaxe at the toolsmith.",
            "silver ore": "mine it in mineshafts.",
            "gold ore": "mine it in mineshafts.",
            "diamond": "mine it in mineshafts.",
            "chicken meal": "craft it at the chef from 5 chicken meat.",
            "venison meal": "craft it from 5 venison.",
            "bear meal": "craft it from 5 bear meat.",
            "bird meal": "craft it from 5 bird meat.",
            "bullets": "craft at gunsmith using silver ore.",
            "salmon": "catch it in the ocean",
            "tuna": "catch it in the ocean",
            "cod": "catch it in the ocean",
            "fishing_rod": "buy it from the fisher",
            "boat": "buy it from the fisher",
            "axe": "buy it from the lumberjack",
            "wood": "cut down trees in the forest with an axe"
        }

        self.recipes = {}
        self.villager_buy_items = {
            "chef": {
                "chicken meat": 20,
                "venison": 60,
                "bear meat": 40,
                "bird meat": 100
            },
            "toolsmith": {},
            "blacksmith": {
                "copper ore": 0,
                "iron ore": 0,
                "silver ore": 200,
                "gold ore": 500,
                "diamond": 1000
            },
            "fisher": {
                "cod": 30,
                "bass": 45,
                "trout": 60,
                "salmon": 80,
                "angelfish": 100,
                "hammerhead shark": 150
            },
            "lumberjack": {
                "wood": 5
            }
        }

        self.villager_sell_items = {
            "chef": {"pork": 50},
            "toolsmith": {
                "shovel": 200,
                "pickaxe": 350,
            },
            "blacksmith": {},
            "gunsmith": {
                "hunting_rifle": 500,
                "bullets": {"cost": 0, "silver_ore": 1, "amount": 20}
            },
            "fisher": {
                "fishing_rod": 250,
                "boat": 1000
            },
            "lumberjack": {
                "axe": 150,
                "advanced_map": 300
            }
        }

        self.inventory = {
            "bullets": 100
        }
        self.coins = 0
        self.world = WorldMap()
        self.player_x = 0
        self.player_y = 0

        # Create starting weapons
        self.weapons = {}
        # Default hunting weapon
        self.default_hunting_weapon = Weapon(
            name="Old Revolver", 
            weapon_type=WeaponType.HUNTING, 
            tier=1
        )
        self.weapons[self.default_hunting_weapon.id] = self.default_hunting_weapon

        # Default combat weapon
        self.default_combat_weapon = Weapon(
            name="Rusty Sword", 
            weapon_type=WeaponType.COMBAT, 
            tier=1
        )
        self.weapons[self.default_combat_weapon.id] = self.default_combat_weapon

        # Set current weapons
        self.current_hunting_weapon_id = self.default_hunting_weapon.id
        self.current_combat_weapon_id = self.default_combat_weapon.id

        self.health = 100
        self.energy = 100

    def to_dict(self):
        """Convert game state to a dictionary for saving."""
        return {
            'inventory': self.inventory,
            'coins': self.coins,
            'player_x': self.player_x,
            'player_y': self.player_y,
            'world': self.world.to_dict(),
            'weapons': {weapon_id: weapon.to_dict() 
                       for weapon_id, weapon in self.weapons.items()},
            'current_hunting_weapon_id': self.current_hunting_weapon_id,
            'current_combat_weapon_id': self.current_combat_weapon_id,
            'health': self.health,
            'energy': self.energy
        }
    
    def from_dict(self, save_data):
        """Load game state from a dictionary."""
        self.inventory = save_data['inventory']
        self.coins = save_data['coins']
        self.player_x = save_data['player_x']
        self.player_y = save_data['player_y']
        self.world = WorldMap.from_dict(save_data['world'])

        self.weapons = {}
        for weapon_id, weapon_data in save_data['weapons'].items():
            self.weapons[weapon_id] = Weapon.from_dict(weapon_data)

        self.current_hunting_weapon_id = save_data.get('current_hunting_weapon_id', self.default_hunting_weapon.id)
        self.current_combat_weapon_id = save_data.get('current_combat_weapon_id', self.default_combat_weapon.id)

        # Ensure weapon IDs exist, fallback to defaults if not
        if self.current_hunting_weapon_id not in self.weapons:
            self.current_hunting_weapon_id = self.default_hunting_weapon.id
            self.weapons[self.current_hunting_weapon_id] = self.default_hunting_weapon

        if self.current_combat_weapon_id not in self.weapons:
            self.current_combat_weapon_id = self.default_combat_weapon.id
            self.weapons[self.current_combat_weapon_id] = self.default_combat_weapon

        self.health = save_data['health']
        self.energy = save_data['energy']
    
    def save_game(self, filename="save_game.json"):
        """Save the game state to a file."""
        save_data = self.to_dict()
        
        try:
            with open(filename, 'w') as f:
                json.dump(save_data, f)
            return True, "Game saved successfully!"
        except Exception as e:
            return False, f"Error saving game: {str(e)}"

    def load_game(self, filename="save_game.json"):
        """Load the game state from a file."""
        try:
            with open(filename, 'r') as f:
                save_data = json.load(f)
            
            self.from_dict(save_data)
            return True, "Game loaded successfully!"
        except FileNotFoundError:
            return False, "No save file found!"
        except Exception as e:
            return False, f"Error loading save file: {str(e)}"

    def get_tool_tier(self, tool_type):
        if f"iron_{tool_type}" in self.inventory:
            return "iron"
        elif f"copper_{tool_type}" in self.inventory:
            return "copper"
        elif tool_type in self.inventory:
            return "basic"
        return None

    def can_mine(self):
        terrain = self.world.get_terrain(self.player_x, self.player_y)
        if terrain == 'P':
            return self.get_tool_tier("shovel") is not None
        elif terrain == 'M':
            return self.get_tool_tier("pickaxe") is not None
        return False

    def attempt_trade(self, villager_type, action, item, amount=1):
        if action == "buy" and villager_type == "fort_keeper":
            # Handle weapon purchases from fort keeper - item is the weapon ID
            x, y = self.player_x, self.player_y
            fort_inventory = self.world.get_fort_inventory(x, y)

            # Find the weapon with the matching ID
            weapon = None
            for w in fort_inventory:
                if w.id == item:
                    weapon = w
                    break

            if weapon:
                cost = weapon.get_cost()
                if self.coins >= cost:
                    self.coins -= cost
                    # Add to player's weapons
                    self.weapons[weapon.id] = weapon
                    # Remove from fort inventory
                    fort_inventory.remove(weapon)
                    # Generate a new weapon of the same tier to replace it
                    new_weapon = Weapon(tier=weapon.tier, weapon_type=WeaponType.COMBAT)
                    fort_inventory.append(new_weapon)

                    # Auto-equip if it's better than current or if we don't have a current weapon
                    current_weapon = self.get_current_weapon("combat")
                    if current_weapon is None or weapon.tier > current_weapon.tier:
                        self.current_combat_weapon_id = weapon.id

                    return True, f"Bought {weapon.name} for {cost} coins"
                return False, "Not enough coins"
            return False, "Weapon not found"
        elif action == "buy":
            # Handle regular item purchases
            if villager_type in self.villager_sell_items and item in self.villager_sell_items[villager_type]:
                item_info = self.villager_sell_items[villager_type][item]
                if isinstance(item_info, dict):
                    cost = item_info["cost"]
                else:
                    cost = item_info
                total_cost = cost * amount

                if total_cost <= self.coins:
                    self.coins -= total_cost
                    self.add_inventory_item(item, amount)
                    return True, f"Bought {amount} {item} for {total_cost} coins"
                return False, "Not enough coins"
            return False, f"This vendor doesn't sell {item}"
        elif action == "sell":
            if villager_type in self.villager_buy_items and item in self.villager_buy_items[villager_type]:
                if item in self.inventory and self.inventory[item] >= amount:
                    cost = self.villager_buy_items[villager_type][item]
                    total_gain = cost * amount
                    self.inventory[item] -= amount
                    if self.inventory[item] <= 0:
                        del self.inventory[item]
                    self.coins += total_gain
                    return True, f"Sold {amount} {item} for {total_gain} coins"
                return False, "Not enough items"
            return False, f"This vendor doesn't buy {item}"
        return False, "Invalid trade"

    def move_player(self, dx, dy):
        self.player_x += dx
        self.player_y += dy

        for x in range(self.player_x - 2, self.player_x + 3):
            for y in range(self.player_y - 2, self.player_y + 3):
                self.world.ensure_terrain_exists(x, y)

        return True, self.get_current_terrain_description()

    def get_current_terrain_description(self):
        terrain = self.world.get_terrain(self.player_x, self.player_y)

        terrain_descriptions = {
            'P': [
                "A vast expanse of rolling plains stretches before you",
                "Tall grass sways gently in the breeze",
                "The wide open grasslands extend to the horizon",
                "A serene meadow surrounds you",
                "You stand in an open field dotted with wildflowers"
            ],
            'T': {
                'small': [
                    "A quaint village nestles in the landscape",
                    "A small settlement bustles with modest activity",
                    "A peaceful hamlet sits before you"
                ],
                'medium': [
                    "A thriving town spreads out ahead",
                    "A well-established town center beckons",
                    "A bustling marketplace draws your attention"
                ],
                'large': [
                    "An impressive city rises before you",
                    "A sprawling urban center dominates the area",
                    "The grand architecture of a large city surrounds you"
                ]
            },
            'X': [
                "An ancient temple looms mysteriously",
                "Stone ruins hint at forgotten mysteries",
                "Sacred walls hold untold secrets",
                "Weathered temple stones stand silent guard"
            ],
            'M': [
                "A dark mineshaft descends into the earth",
                "Mining equipment surrounds a deep shaft",
                "A well-worn path leads to a mine entrance",
                "Pick marks and mining debris scatter the area"
            ],
            'O': [
                "Deep ocean waters stretch to the horizon",
                "Waves roll endlessly across the deep blue",
                "The vast ocean extends as far as the eye can see",
                "Dark waters move in hypnotic patterns"
            ],
            'B': [
                "Soft sand crunches beneath your feet",
                "Gentle waves lap at the sandy shore",
                "A pristine beach stretches along the coast",
                "Seashells dot the sandy beach"
            ],
            'C': [
                "Shallow coastal waters shimmer invitingly",
                "The coastline curves gracefully ahead",
                "Clear waters reveal hints of marine life",
                "Gentle waves break in the shallows"
            ],
            'F': [
                "Dense forest canopy towers overhead",
                "Ancient trees stand like silent sentinels",
                "The forest air is thick with earthy scents",
                "Sunlight filters through leafy branches"
            ],
            'S1': ["A imposing stronghold stands before you. It seems to be the first of three."],
            'S2': ["This is a more fortified stronghold than the first. The second of three."],
            'S3': ["This is the final stronghold, the most heavily guarded of them all."],
            'F_F': ["You stand before a formidable fort."]
        }

        base_description = ""
        if terrain == 'T':
            town_type = self.world.get_town_type(self.player_x, self.player_y)
            town_name = self.world.get_town_name(self.player_x, self.player_y)
            base_description = f"Welcome to {town_name}, "
            base_description += random.choice(terrain_descriptions[terrain][town_type])
        elif terrain == 'O':
            if 'boat' in self.inventory:
                base_description = random.choice([
                    "Your boat glides through the deep ocean waters",
                    "Waves gently rock your vessel as you sail",
                    "The vast sea stretches endlessly around your boat",
                    "Your boat cuts through the rolling waves"
                ])
            else:
                base_description = random.choice([
                    "The deep ocean lies before you, but you'll need a boat to traverse it",
                    "These waters are too deep to swim. A boat would be necessary",
                    "Only a sturdy boat could take you across these waters",
                    "The ocean beckons, but you need a boat to venture forth"
                ])
        elif terrain.startswith('S'):
            base_description = random.choice(terrain_descriptions[terrain])
        elif terrain == 'F_F':
            base_description = random.choice(terrain_descriptions[terrain])
        else:
            base_description = random.choice(terrain_descriptions[terrain])

        if terrain == 'F':
            wood_left = self.world.forest_wood[(self.player_x, self.player_y)]
            if wood_left <= 0:
                base_description = "Only saplings and stumps remain in this depleted forest"
            elif 'axe' in self.inventory:
                base_description += f". There are {wood_left} trees suitable for cutting"
            else:
                base_description += ". You'll need an axe to harvest wood here"
        elif terrain == 'C' or terrain == 'O':
            if 'fishing_rod' in self.inventory:
                base_description += ". The waters look promising for fishing"
            else:
                base_description += ". A fishing rod would be useful here"

        surroundings = []
        terrain_names = {
            'P': "plains",
            'T': "a town",
            'X': "a temple",
            'M': "a mineshaft",
            'O': "ocean",
            'B': "a beach",
            'C': "the coast",
            'F': "a forest",
            'S1': "a stronghold (tier 1)",
            'S2': "a stronghold (tier 2)",
            'S3': "a stronghold (tier 3)",
            'F_F': "a fort"
        }

        directions = {
            (0, -1): "north",
            (1, -1): "northeast",
            (1, 0): "east",
            (1, 1): "southeast",
            (0, 1): "south",
            (-1, 1): "southwest",
            (-1, 0): "west",
            (-1, -1): "northwest"
        }

        for (dx, dy), direction in directions.items():
            nearby_x = self.player_x + dx
            nearby_y = self.player_y + dy
            nearby_terrain = self.world.get_terrain(nearby_x, nearby_y)
            if nearby_terrain != terrain:
                if nearby_terrain in terrain_names:
                    surroundings.append(f"{terrain_names[nearby_terrain]} to the {direction}")

        if surroundings:
            if len(surroundings) == 1:
                base_description += f". There is {surroundings[0]}"
            else:
                base_description += f". You can see {', '.join(surroundings[:-1])} and {surroundings[-1]}"

        return base_description

    def add_inventory_item(self, item, count):
        if item in self.inventory:
            self.inventory[item] += count
        else:
            self.inventory[item] = count
        return f"You got {count} {item}."

    def count_inventory_item(self, item):
        return self.inventory.get(item, 0)

    def can_hunt(self):
        terrain = self.world.get_terrain(self.player_x, self.player_y)
        return terrain in ['P', 'F']

    def attempt_house_entry(self, lights_on=True, town_type='small'):
        if lights_on:
            if randint(0, 1) == 1:
                self.coins = 0
                return False, "You were caught! The guards confiscated all your coins."
            return True, "The house is occupied. Better leave before someone notices."
        else:
            town_probabilities = {
                'small': {'items': 0.7, 'coins': 0.3},
                'medium': {'items': 0.5, 'coins': 0.5},
                'large': {'items': 0.3, 'coins': 0.7}
            }

            possible_items = {
                'lockpick': 0.3,
                'iron_ore': 0.2,
                'copper_ore': 0.4,
                'silver_ore': 0.1,
                'gold_ore': 0.05,
                'diamond': 0.02
            }

            if randint(0, 1) == 1:
                if random.random() < town_probabilities[town_type]['items']:
                    item = random.choices(
                        list(possible_items.keys()),
                        weights=list(possible_items.values())
                    )[0]
                    amount = randint(1, 2)
                    self.add_inventory_item(item, amount)
                    return True, f"You snuck in and found {amount} {item}!"
                else:
                    base_amount = {
                        'small': (10, 30),
                        'medium': (20, 50),
                        'large': (40, 100)
                    }[town_type]
                    coins_found = randint(base_amount[0], base_amount[1])
                    self.coins += coins_found
                    return True, f"You snuck in and found {coins_found} coins!"
            return True, "The house is empty, and you found nothing of value."

    def switch_weapon(self, weapon_type="combat"):
        """Switch to next available weapon of the specified type"""
        available_weapons = []

        # Get all weapons of the specified type
        for weapon_id, weapon in self.weapons.items():
            if weapon.weapon_type == WeaponType(weapon_type):
                available_weapons.append(weapon)

        if not available_weapons:
            return False, f"No {weapon_type} weapons available"

        # Sort by tier for consistent cycling
        available_weapons.sort(key=lambda w: w.tier)

        # Find current weapon index
        current_id = self.current_hunting_weapon_id if weapon_type == "hunting" else self.current_combat_weapon_id
        current_index = -1

        for i, weapon in enumerate(available_weapons):
            if weapon.id == current_id:
                current_index = i
                break

        # Cycle to next weapon
        next_index = (current_index + 1) % len(available_weapons)
        next_weapon = available_weapons[next_index]

        # Update current weapon
        if weapon_type == "hunting":
            self.current_hunting_weapon_id = next_weapon.id
        else:
            self.current_combat_weapon_id = next_weapon.id

        return True, f"Switched to {next_weapon.name}"

    def get_current_weapon(self, weapon_type="combat"):
        """Get the current weapon of the specified type"""
        weapon_id = self.current_hunting_weapon_id if weapon_type == "hunting" else self.current_combat_weapon_id
        return self.weapons.get(weapon_id)

    def attempt_weapon_upgrade(self, weapon_id):
        """Upgrade a specific weapon"""
        if weapon_id not in self.weapons:
            return False, "Weapon not found"

        weapon = self.weapons[weapon_id]
        cost = weapon.get_upgrade_cost()

        if (self.inventory.get("copper_bars", 0) < cost["copper_bars"] or 
            self.inventory.get("iron_bars", 0) < cost["iron_bars"] or 
            self.coins < cost["coins"]):
            return False, f"Not enough materials. Need: {cost['copper_bars']} copper bars, {cost['iron_bars']} iron bars, and {cost['coins']} coins"

        self.inventory["copper_bars"] -= cost["copper_bars"]
        self.inventory["iron_bars"] -= cost["iron_bars"]
        self.coins -= cost["coins"]

        weapon.upgrade_level += 1
        
        # Improve dice config for upgraded weapons
        if weapon.upgrade_level == 1:
            # Add +1 to all dice rolls
            weapon.modifier += 1
        elif weapon.upgrade_level == 2:
            # Add an extra die at level 2
            weapon.num_dice += 1
        elif weapon.upgrade_level >= 3:
            # Add both more dice and better modifier at higher levels
            weapon.num_dice += 1
            weapon.modifier += 1
            
        # Update the dice config tuple
        weapon.dice_config = (weapon.num_dice, weapon.dice_sides, weapon.modifier)
        
        # Calculate new average damage
        new_avg = weapon.calculate_avg_damage()

        return True, f"Upgraded {weapon.name} to level {weapon.upgrade_level}. New damage: {weapon.num_dice}d{weapon.dice_sides}+{weapon.modifier} (avg: {new_avg})"

    def use_bullet(self):
        if self.inventory.get("bullets", 0) > 0:
            self.inventory["bullets"] -= 1
            if self.inventory["bullets"] <= 0:
                del self.inventory["bullets"]
            return True
        return False

    def consume_meal_if_needed(self):
        if self.health <= 75 or self.energy <= 75:
            for item in list(self.inventory.keys()):
                if item.endswith(" meal") and self.inventory[item] > 0:
                    self.inventory[item] -= 1
                    if self.inventory[item] <= 0:
                        del self.inventory[item]
                    self.health = min(100, self.health + 25)
                    self.energy = min(100, self.energy + 25)
                    return True, f"Consumed {item} and restored health and energy"
        return False, "No need to consume a meal or no meals available"

    tool_upgrade_costs = {
        "shovel": {
            "copper": {"coins": 100, "copper_bars": 2},
            "iron": {"coins": 250, "iron_bars": 3}
        },
        "pickaxe": {
            "copper": {"coins": 150, "copper_bars": 3},
            "iron": {"coins": 300, "iron_bars": 4}
        }
    }

    def can_move_to(self, x, y):
        terrain = self.world.get_terrain(x, y)
        if terrain == 'O':
            return 'boat' in self.inventory
        return True

    def attempt_woodcutting(self):
        if 'axe' not in self.inventory:
            return False, "You need an axe to cut trees!"

        terrain = self.world.get_terrain(self.player_x, self.player_y)
        if terrain != 'F':
            return False, "You can only cut trees in the forest!"

        wood_amount = random.randint(1, 5)
        current_wood = self.world.forest_wood[(self.player_x, self.player_y)]

        if current_wood <= 0:
            return False, "This forest has been depleted of wood!"

        wood_amount = min(wood_amount, current_wood)

        forest_depleted = self.world.deplete_forest(self.player_x, self.player_y, wood_amount)
        self.add_inventory_item("wood", wood_amount)

        message = f"You cut down some trees and got {wood_amount} wood!"
        if forest_depleted:
            message += " The forest has been depleted and turned into plains."

        return True, message