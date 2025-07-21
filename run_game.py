#!/usr/bin/env python3
"""
Simple wrapper to run the game with error handling and diagnostics.
"""

import traceback
import sys
import os

def main():
    try:
        # Try importing the modules first
        print("Importing Tkinter...")
        import tkinter as tk
        from tkinter import ttk, messagebox
        print("Tkinter imported successfully")
        
        print("Importing noise module...")
        import noise
        print("Noise module imported successfully")
        
        print("Importing game modules...")
        from game_logic import GameState
        import game_gui
        from login_screen import LoginScreen
        from user_auth import user_auth
        print("Game modules imported successfully")
        
        def start_game():
            print("Creating game instance...")
            game = game_gui.GameGUI()
            print("Game instance created successfully")
            
            print("Starting game...")
            game.run()
            print("Game closed normally")
        
        # Show the login screen first
        print("Showing login screen...")
        login = LoginScreen(on_login_success=start_game)
        login.mainloop()
        
    except ImportError as e:
        print(f"Import Error: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"Error running game: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting run_game.py wrapper")
    main()
    print("Exiting run_game.py wrapper")