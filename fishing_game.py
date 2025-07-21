import tkinter as tk
from tkinter import ttk, messagebox
import random
import time

class FishingGame:
    def __init__(self, parent, game_state):
        self.window = tk.Toplevel(parent)
        self.window.title("Fishing")
        self.game_state = game_state

        # Fish types and their values
        self.fish_types = ["cod", "bass", "trout", "salmon", "angelfish", "hammerhead shark"]

        # Game state variables
        self.current_time = 2.0
        self.current_fish = None
        self.start_time = None
        self.score = 0

        # Create UI elements
        self.create_ui()

        # Configure window
        self.window.geometry("400x300")
        self.window.resizable(False, False)

    def create_ui(self):
        # Main frame
        frame = ttk.Frame(self.window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Instructions
        ttk.Label(frame, text="Type the fish name and press Enter!", 
                 font=('Helvetica', 12)).pack(pady=10)

        # Fish display
        self.fish_label = ttk.Label(frame, text="", font=('Helvetica', 16, 'bold'))
        self.fish_label.pack(pady=20)

        # Timer display
        self.timer_label = ttk.Label(frame, text=f"Time: {self.current_time:.1f}s", 
                                   font=('Helvetica', 12))
        self.timer_label.pack(pady=5)

        # Entry field
        self.entry = ttk.Entry(frame, font=('Helvetica', 12))
        self.entry.pack(pady=10)
        self.entry.bind('<Return>', self.check_answer)

        # Score display
        self.score_label = ttk.Label(frame, text="Fish Caught: 0", 
                                   font=('Helvetica', 12))
        self.score_label.pack(pady=5)

        # Start button
        self.start_button = ttk.Button(frame, text="Start Fishing!", 
                                     command=self.start_game)
        self.start_button.pack(pady=10)

    def start_game(self):
        if 'fishing_rod' not in self.game_state.inventory:
            messagebox.showerror("Error", "You need a fishing rod to fish!")
            self.window.destroy()
            return

        # Disable start button
        self.start_button.config(state='disabled')

        # Select and display first fish
        self.current_fish = random.choice(self.fish_types)
        self.fish_label.config(text=self.current_fish)

        # Clear and focus entry
        self.entry.delete(0, tk.END)
        self.entry.focus()

        # Start timer
        self.start_time = time.time()
        self.update_timer()

    def update_timer(self):
        if self.start_time is None:
            return

        # Calculate remaining time
        elapsed = time.time() - self.start_time
        remaining = max(0, self.current_time - elapsed)

        # Update timer display
        self.timer_label.config(text=f"Time: {remaining:.1f}s")

        if remaining > 0:
            # Schedule next update
            self.window.after(100, self.update_timer)
        else:
            self.game_over()

    def check_answer(self, event=None):
        if self.start_time is None:
            return

        # Get elapsed time and user answer
        elapsed = time.time() - self.start_time
        user_answer = self.entry.get().strip()

        # Check if answer is correct and within time limit
        if elapsed <= self.current_time and user_answer == self.current_fish:
            # Increase score
            self.score += 1
            self.score_label.config(text=f"Fish Caught: {self.score}")

            # Add fish to inventory
            self.game_state.add_inventory_item(self.current_fish, 1)

            # Decrease time for next fish
            self.current_time = max(0.5, self.current_time - 0.1)

            # Start new round
            self.start_time = time.time()
            self.current_fish = random.choice(self.fish_types)
            self.fish_label.config(text=self.current_fish)
            self.entry.delete(0, tk.END)
        elif elapsed > self.current_time:
            self.game_over()

    def game_over(self):
        self.start_time = None
        messagebox.showinfo("Game Over", 
                          f"Fishing session ended!\nYou caught {self.score} fish!")
        self.window.destroy()

def start_fishing_game(parent, game_state):
    if 'fishing_rod' not in game_state.inventory:
        messagebox.showerror("Error", "You need a fishing rod to fish!")
        return
    FishingGame(parent, game_state)