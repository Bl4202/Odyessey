"""
Login screen for the adventure game.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
from user_auth import user_auth

class LoginScreen(tk.Tk):
    def __init__(self, on_login_success=None):
        super().__init__()
        
        self.title("Adventure Game - Login")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # Set the callback function for login success
        self.on_login_success = on_login_success
        
        # Set up the UI
        self.setup_ui()
    
    def setup_ui(self):
        # Create a frame for the login form
        self.login_frame = ttk.Frame(self)
        self.login_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Game title
        ttk.Label(self.login_frame, 
                 text="Adventure Game", 
                 font=("Arial", 24, "bold")).pack(pady=(0, 20))
        
        # Username field
        ttk.Label(self.login_frame, 
                 text="Username:").pack(anchor="w", pady=(10, 0))
        self.username_entry = ttk.Entry(self.login_frame, width=30)
        self.username_entry.pack(pady=(0, 10), fill="x")
        
        # Password field
        ttk.Label(self.login_frame, 
                 text="Password:").pack(anchor="w", pady=(10, 0))
        self.password_entry = ttk.Entry(self.login_frame, width=30, show="*")
        self.password_entry.pack(pady=(0, 20), fill="x")
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.login_frame)
        buttons_frame.pack(pady=(0, 20), fill="x")
        
        # Login button
        self.login_button = ttk.Button(
            buttons_frame, 
            text="Login",
            command=self.login)
        self.login_button.pack(side="left", padx=(0, 10))
        
        # Register button
        self.register_button = ttk.Button(
            buttons_frame, 
            text="Register",
            command=self.show_register_screen)
        self.register_button.pack(side="left")
        
        # Guest button
        self.guest_button = ttk.Button(
            buttons_frame, 
            text="Play as Guest",
            command=self.play_as_guest)
        self.guest_button.pack(side="right")
        
        # Bind the Return key to login
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        # Add some visual style
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 10), padding=5)
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TEntry", font=("Arial", 10), padding=5)
        
        # Start with the username field focused
        self.username_entry.focus()
    
    def login(self):
        # Get the username and password
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # Check if the fields are empty
        if not username or not password:
            messagebox.showerror("Error", "Please enter a username and password")
            return
        
        # Try to login
        success, message = user_auth.login(username, password)
        if success:
            # Show a success message
            messagebox.showinfo("Success", message)
            
            # Call the login success callback if provided
            if self.on_login_success:
                self.destroy()  # Close the login window
                self.on_login_success()  # Start the game
            else:
                # Just close the window if no callback
                self.destroy()
        else:
            # Show an error message
            messagebox.showerror("Error", message)
    
    def show_register_screen(self):
        # Hide the login frame
        self.login_frame.pack_forget()
        
        # Create a frame for the register form
        self.register_frame = ttk.Frame(self)
        self.register_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Register title
        ttk.Label(self.register_frame, 
                 text="Register New Account", 
                 font=("Arial", 18, "bold")).pack(pady=(0, 20))
        
        # Username field
        ttk.Label(self.register_frame, 
                 text="Username:").pack(anchor="w", pady=(10, 0))
        self.reg_username_entry = ttk.Entry(self.register_frame, width=30)
        self.reg_username_entry.pack(pady=(0, 10), fill="x")
        
        # Password field
        ttk.Label(self.register_frame, 
                 text="Password:").pack(anchor="w", pady=(10, 0))
        self.reg_password_entry = ttk.Entry(self.register_frame, width=30, show="*")
        self.reg_password_entry.pack(pady=(0, 10), fill="x")
        
        # Confirm password field
        ttk.Label(self.register_frame, 
                 text="Confirm Password:").pack(anchor="w", pady=(10, 0))
        self.reg_confirm_entry = ttk.Entry(self.register_frame, width=30, show="*")
        self.reg_confirm_entry.pack(pady=(0, 20), fill="x")
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.register_frame)
        buttons_frame.pack(pady=(0, 20), fill="x")
        
        # Register button
        self.reg_button = ttk.Button(
            buttons_frame, 
            text="Register",
            command=self.register_user)
        self.reg_button.pack(side="left", padx=(0, 10))
        
        # Back button
        self.back_button = ttk.Button(
            buttons_frame, 
            text="Back to Login",
            command=self.show_login_screen)
        self.back_button.pack(side="left")
        
        # Bind the Return key to register
        self.reg_username_entry.bind("<Return>", lambda e: self.reg_password_entry.focus())
        self.reg_password_entry.bind("<Return>", lambda e: self.reg_confirm_entry.focus())
        self.reg_confirm_entry.bind("<Return>", lambda e: self.register_user())
        
        # Start with the username field focused
        self.reg_username_entry.focus()
    
    def show_login_screen(self):
        # Hide the register frame if it exists
        if hasattr(self, 'register_frame'):
            self.register_frame.pack_forget()
        
        # Show the login frame
        self.login_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Clear the register fields if they exist
        if hasattr(self, 'reg_username_entry'):
            self.reg_username_entry.delete(0, 'end')
        if hasattr(self, 'reg_password_entry'):
            self.reg_password_entry.delete(0, 'end')
        if hasattr(self, 'reg_confirm_entry'):
            self.reg_confirm_entry.delete(0, 'end')
        
        # Focus on the username field
        self.username_entry.focus()
    
    def register_user(self):
        # Get the username and password
        username = self.reg_username_entry.get().strip()
        password = self.reg_password_entry.get()
        confirm = self.reg_confirm_entry.get()
        
        # Check if the fields are empty
        if not username or not password or not confirm:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        # Check if the passwords match
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        # Check if the username has valid characters
        if not username.isalnum():
            messagebox.showerror("Error", "Username can only contain letters and numbers")
            return
        
        # Check if the password is long enough
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        
        # Try to register
        success, message = user_auth.register(username, password)
        if success:
            # Show a success message
            messagebox.showinfo("Success", message)
            
            # Go back to the login screen
            self.show_login_screen()
            
            # Pre-fill the username field
            self.username_entry.delete(0, 'end')
            self.username_entry.insert(0, username)
            self.password_entry.focus()
        else:
            # Show an error message
            messagebox.showerror("Error", message)
    
    def play_as_guest(self):
        """Allow playing without account."""
        # Call the login success callback if provided
        if self.on_login_success:
            self.destroy()  # Close the login window
            self.on_login_success()  # Start the game
        else:
            # Just close the window if no callback
            self.destroy()

# If running directly, show the login screen
if __name__ == "__main__":
    def on_success():
        print("Login successful!")
        
    app = LoginScreen(on_login_success=on_success)
    app.mainloop()