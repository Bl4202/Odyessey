import tkinter as tk
from tkinter import ttk, messagebox
import math
from random import randint, choice
from enum import Enum
import time
from PIL import Image, ImageTk

class AnimalType(Enum):
    CHICKEN = {"speed": 2, "value": 10, "health": 1, "pattern": "hop", "size": 25}
    DEER = {"speed": 6, "value": 25, "health": 2, "pattern": "flee", "size": 50}
    BEAR = {"speed": 2, "value": 50, "health": 3, "pattern": "graze", "size": 50}
    BIRD = {"speed": 6, "value": 25, "health": 1, "pattern": "fly", "size": 35}

class Animal:
    def __init__(self, animal_type, x, y, images):
        self.type = animal_type
        self.x = x
        self.y = y
        self.health = animal_type.value["health"]
        self.images = images
        self.current_image = 'right'
        self.original_speed = animal_type.value["speed"]
        self.current_speed = self.original_speed
        self.is_fleeing = False
        
        # Initialize flee_target to a safe default
        self.flee_target = (0, 0)  # Will get a better value when needed
        
        self.movement_angle = math.radians(randint(0, 360))
        self.boundary = {
            'left': 100,
            'right': 300,
            'top': 100,
            'bottom': 300
        }

    def get_nearest_edge(self):
        distances = [
            (0, self.y, self.x),
            (400, self.y, 400 - self.x),
            (self.x, 0, self.y),
            (self.x, 400, 400 - self.y)
        ]
        closest = min(distances, key=lambda x: x[2])
        return (closest[0], closest[1])

    def handle_hit(self, damage):
        self.health -= damage
        if self.type == AnimalType.BEAR:
            self.current_speed = self.original_speed * 2
        elif self.type == AnimalType.DEER:
            self.current_speed = self.original_speed * 1.5
        self.is_fleeing = True
        self.flee_target = self.get_nearest_edge()

    def check_boundary(self, new_x, new_y):
        if not self.is_fleeing:
            if new_x < self.boundary['left'] or new_x > self.boundary['right']:
                self.movement_angle = math.pi - self.movement_angle
                return False
            if new_y < self.boundary['top'] or new_y > self.boundary['bottom']:
                self.movement_angle = -self.movement_angle
                return False
            return True
        else:
            return True

    def move(self):
        if self.health <= 0:
            return

        # Initialize dx and dy default values
        dx, dy = 0, 0

        if self.is_fleeing:
            # If flee_target isn't set, initialize it
            if not hasattr(self, 'flee_target') or self.flee_target is None:
                self.flee_target = self.get_nearest_edge()
                
            dx = self.flee_target[0] - self.x
            dy = self.flee_target[1] - self.y
            distance = math.hypot(dx, dy)
            if distance > 0:
                dx = dx / distance * self.current_speed
                dy = dy / distance * self.current_speed
                new_x = self.x + dx
                new_y = self.y + dy
                self.x = new_x
                self.y = new_y
        else:
            if (self.type.value["pattern"] == "hop" and randint(0, 30) == 0) or \
               (self.type.value["pattern"] == "fly" and randint(0, 10) == 0) or \
               (self.type.value["pattern"] == "flee" and randint(0, 20) == 0) or \
               (self.type.value["pattern"] == "graze" and randint(0, 40) == 0):
                self.movement_angle = math.radians(randint(0, 360))

            speed_multiplier = 1.5 if self.type.value["pattern"] == "fly" else 1.0
            dx = math.cos(self.movement_angle) * self.current_speed * speed_multiplier
            dy = math.sin(self.movement_angle) * self.current_speed * speed_multiplier

            new_x = self.x + dx
            new_y = self.y + dy

            if self.check_boundary(new_x, new_y):
                self.x = new_x
                self.y = new_y

        # Update image direction based on movement
        if dx > 0:  # Moving right
            self.current_image = 'right'
        elif dx < 0:  # Moving left
            self.current_image = 'left'
        # If dx is 0, keep the current image direction

        self.x = max(0, min(self.x, 400))
        self.y = max(0, min(self.y, 400))

    def is_at_edge(self):
        margin = 5
        return (self.x <= margin or self.x >= 400 - margin or 
                self.y <= margin or self.y >= 400 - margin)

    def get_current_image(self):
        if self.health <= 0:
            return self.images['dead']
        return self.images[self.current_image]

    def get_hitbox_size(self):
        return self.type.value["size"] // 2

class HuntingGame(tk.Toplevel):
    def __init__(self, parent, game_state):
        super().__init__(parent)
        self.title("Hunting Ground")
        self.game_state = game_state

        # Add the images with proper error handling
        self.animal_images = {}
        
        # Define image paths and sizes
        animal_image_config = {
            AnimalType.CHICKEN: {
                'size': (25, 25),
                'paths': {
                    'left': 'attached_assets/Chicken_Left.png',
                    'right': 'attached_assets/Chicken_Right.png',
                    'dead': 'attached_assets/Chicken_Dead.png'
                }
            },
            AnimalType.DEER: {
                'size': (50, 50),
                'paths': {
                    'left': 'attached_assets/Deer_Left.png',
                    'right': 'attached_assets/Deer_Right.png',
                    'dead': 'attached_assets/Deer_Dead.png'
                }
            },
            AnimalType.BEAR: {
                'size': (50, 50),
                'paths': {
                    'left': 'attached_assets/Bear_Left.png',
                    'right': 'attached_assets/Bear_Right.png',
                    'dead': 'attached_assets/Bear_Dead.png'
                }
            },
            AnimalType.BIRD: {
                'size': (35, 35),
                'paths': {
                    'left': 'attached_assets/Bird_Left.png',
                    'right': 'attached_assets/Bird_Right.png',
                    'dead': 'attached_assets/Bird_Dead.png'
                }
            }
        }
        
        # Load all images with error handling
        for animal_type, config in animal_image_config.items():
            self.animal_images[animal_type] = {}
            for position, path in config['paths'].items():
                try:
                    self.animal_images[animal_type][position] = ImageTk.PhotoImage(
                        Image.open(path).resize(config['size'])
                    )
                except Exception as e:
                    print(f"Error loading image {path}: {str(e)}")
                    # Create a colored rectangle as fallback
                    img = Image.new('RGB', config['size'], color=(255, 0, 0))
                    self.animal_images[animal_type][position] = ImageTk.PhotoImage(img)

        self.time_remaining = 60
        self.score = 0
        self.animals = []
        self.start_time = time.time()
        self.spawn_timer = 0

        self.setup_ui()
        self.spawn_animals(initial=True)
        self.after(50, self.game_loop)
        self.bind('<space>', self.shoot)
        self.bind('<Motion>', self.update_crosshair)
        self.bind('r', lambda e: self.reload_weapon())
        self.bind('e', lambda e: self.switch_weapon())
        self.geometry("600x500")
        self.resizable(False, False)

    def setup_ui(self):
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.main_frame, width=400, height=400, bg='darkgreen')
        self.canvas.pack(side=tk.LEFT)

        info_frame = ttk.Frame(self.main_frame)
        info_frame.pack(side=tk.RIGHT, padx=10, fill=tk.Y)

        ttk.Label(info_frame, text="HUNTING", font=('Courier', 16, 'bold')).pack()

        # Simple hunting weapon display
        has_rifle = 'hunting_rifle' in self.game_state.inventory
        weapon_name = "Hunting Rifle" if has_rifle else "Revolver"
        self.weapon_label = ttk.Label(info_frame, text=f"Weapon: {weapon_name}")
        self.weapon_label.pack(pady=5)

        self.cooldown_label = ttk.Label(info_frame, text="Ready")
        self.cooldown_label.pack(pady=5)

        self.bullet_label = ttk.Label(info_frame, text=f"Bullets: {self.game_state.inventory.get('bullets', 0)}")
        self.bullet_label.pack(pady=5)

        self.time_label = ttk.Label(info_frame, text="Time: 60")
        self.time_label.pack(pady=5)

        self.score_label = ttk.Label(info_frame, text="Score: 0")
        self.score_label.pack(pady=5)

        # Add leave button
        ttk.Button(info_frame, text="Leave Hunt", 
                  command=self.leave_hunt).pack(pady=10)

        controls_text = """
        Controls:
        - Move mouse to aim
        - Space to shoot
        """
        
        if has_rifle:
            controls_text += "- R to reload rifle\n"
            
        controls_text += """
        - Move quickly, animals may flee!
        """
        
        ttk.Label(info_frame, text=controls_text, justify=tk.LEFT).pack(pady=20)

        self.crosshair = self.canvas.create_line(0, 0, 0, 0, fill='red', width=2)

    def shoot(self, event):
        current_time = time.time()
        
        # Simple weapon logic without complex weapon object
        has_rifle = 'hunting_rifle' in self.game_state.inventory
        
        # Use cooldown based on weapon type
        cooldown = 3.0 if has_rifle else 1.0
        
        if hasattr(self, 'last_shot_time') and current_time - self.last_shot_time < cooldown:
            return
            
        # Check for bullets
        if self.game_state.inventory.get('bullets', 0) <= 0:
            self.cooldown_label.config(text="No bullets!")
            return

        # Track shot time
        self.last_shot_time = current_time
        
        x = self.winfo_pointerx() - self.canvas.winfo_rootx()
        y = self.winfo_pointery() - self.canvas.winfo_rooty()

        # Set damage based on weapon type
        damage = 2 if has_rifle else 1
        
        # Use a bullet
        if 'bullets' in self.game_state.inventory:
            self.game_state.inventory['bullets'] -= 1
            if self.game_state.inventory['bullets'] <= 0:
                del self.game_state.inventory['bullets']
        
        self.bullet_label.config(text=f"Bullets: {self.game_state.inventory.get('bullets', 0)}")

        for animal in self.animals[:]:
            distance = math.hypot(x - animal.x, y - animal.y)
            if distance < animal.get_hitbox_size():
                animal.handle_hit(damage)
                if animal.health <= 0:
                    self.score += animal.type.value["value"]
                    self.score_label.config(text=f"Score: {self.score}")
                    if animal.type == AnimalType.CHICKEN:
                        self.game_state.add_inventory_item("chicken meat", 1)
                    elif animal.type == AnimalType.DEER:
                        self.game_state.add_inventory_item("venison", 2)
                    elif animal.type == AnimalType.BEAR:
                        self.game_state.add_inventory_item("bear meat", 3)
                    elif animal.type == AnimalType.BIRD:
                        self.game_state.add_inventory_item("bird meat", 1)
            elif distance < animal.get_hitbox_size() * 2:
                animal.is_fleeing = True
                animal.flee_target = animal.get_nearest_edge()

    def reload_weapon(self):
        # Simple reload for rifle
        if 'hunting_rifle' in self.game_state.inventory:
            self.last_shot_time = 0  # Reset cooldown
            self.cooldown_label.config(text="Reloaded!")

    def switch_weapon(self):
        # We're using a simplified weapon system, so just update the UI
        has_rifle = 'hunting_rifle' in self.game_state.inventory
        weapon_name = "Hunting Rifle" if has_rifle else "Revolver"
        self.weapon_label.config(text=f"Weapon: {weapon_name}")

    def spawn_animals(self, initial=False):
        if initial:
            for _ in range(2):
                self.spawn_animal(AnimalType.CHICKEN)
            for _ in range(2):
                self.spawn_animal(AnimalType.DEER)
            self.spawn_animal(AnimalType.BEAR)
            for _ in range(2):
                self.spawn_animal(AnimalType.BIRD)
        else:
            self.spawn_timer += 1
            if self.spawn_timer >= 20:
                self.spawn_timer = 0
                if randint(0, 100) < 30:
                    animal_type = choice(list(AnimalType))
                    self.spawn_animal(animal_type)

    def spawn_animal(self, animal_type):
        center_x, center_y = 200, 200
        spawn_radius = 100

        angle = math.radians(randint(0, 360))
        distance = randint(20, spawn_radius)

        x = center_x + math.cos(angle) * distance
        y = center_y + math.sin(angle) * distance

        self.animals.append(Animal(animal_type, x, y, self.animal_images[animal_type]))

    def update_crosshair(self, event):
        x, y = event.x, event.y
        size = 10
        self.canvas.coords(self.crosshair,
                         x - size, y,
                         x + size, y,
                         x, y,
                         x, y - size,
                         x, y + size)

    def game_loop(self):
        current_time = time.time()
        elapsed = int(current_time - self.start_time)
        remaining = max(0, self.time_remaining - elapsed)
        self.time_label.config(text=f"Time: {remaining}")

        # Simple weapon cooldown system
        if hasattr(self, 'last_shot_time'):
            has_rifle = 'hunting_rifle' in self.game_state.inventory
            cooldown = 3.0 if has_rifle else 1.0
            time_since_shot = current_time - self.last_shot_time
            
            if time_since_shot < cooldown:
                remaining_cooldown = cooldown - time_since_shot
                self.cooldown_label.config(text=f"Cooldown: {remaining_cooldown:.1f}s")
            else:
                self.cooldown_label.config(text="Ready")
        else:
            self.cooldown_label.config(text="Ready")

        self.spawn_animals()

        self.canvas.delete("animal")
        for animal in self.animals[:]:
            animal.move()
            if animal.is_at_edge():
                self.animals.remove(animal)
                continue
            self.canvas.create_image(animal.x, animal.y, 
                                   image=animal.get_current_image(), 
                                   tags="animal")

        if remaining <= 0:
            messagebox.showinfo("Hunt Over", 
                              f"Hunt finished!\nScore: {self.score}")
            self.destroy()
            return

        self.after(50, self.game_loop)

    def leave_hunt(self):
        """Handle leaving the hunt early"""
        if messagebox.askyesno("Leave Hunt", 
                             "Are you sure you want to leave? You'll keep your gains and spent bullets."):
            self.destroy()

# Function to start the hunting game from the main game
def start_hunting_game(parent, game_state):
    """Initialize and show the hunting game window"""
    hunting_game = HuntingGame(parent, game_state)
    
    # Make sure we have bullets!
    if game_state.inventory.get("bullets", 0) <= 0:
        game_state.add_inventory_item("bullets", 10)
        hunting_game.bullet_label.config(text=f"Bullets: {game_state.inventory.get('bullets', 0)}")
    
    return hunting_game

if __name__ == "__main__":
    # For testing the game standalone
    import sys
    from game_logic import GameState
    
    root = tk.Tk()
    test_game_state = GameState()
    test_game_state.inventory = {
        'bullets': 10,
        'hunting_rifle': 1  # Uncomment to test with rifle
    }
    
    app = HuntingGame(root, test_game_state)
    root.mainloop()