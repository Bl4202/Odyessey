"""
User authentication and account system for the adventure game.
"""
import os
import json
import uuid
import hashlib
import time
from datetime import datetime

# Define the users directory
USERS_DIR = "user_data"
SAVES_DIR = os.path.join(USERS_DIR, "saves")

# Ensure directories exist
os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(SAVES_DIR, exist_ok=True)

class UserAuth:
    def __init__(self):
        self.users = self._load_users()
        self.current_user = None
        self.session_token = None
    
    def _load_users(self):
        """Load the users from the user data file."""
        users_file = os.path.join(USERS_DIR, "users.json")
        if os.path.exists(users_file):
            try:
                with open(users_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _save_users(self):
        """Save the users to the user data file."""
        users_file = os.path.join(USERS_DIR, "users.json")
        with open(users_file, 'w') as f:
            json.dump(self.users, f, indent=4)
    
    def _hash_password(self, password, salt=None):
        """Hash a password with a salt."""
        if not salt:
            salt = uuid.uuid4().hex
        
        # Create the hash with the salt
        hash_obj = hashlib.sha256((password + salt).encode())
        password_hash = hash_obj.hexdigest()
        
        return password_hash, salt
    
    def register(self, username, password):
        """Register a new user."""
        # Check if username already exists
        if username in self.users:
            return False, "Username already exists"
        
        # Hash the password with a salt
        password_hash, salt = self._hash_password(password)
        
        # Create the user
        self.users[username] = {
            "password_hash": password_hash,
            "salt": salt,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        # Save the users
        self._save_users()
        
        return True, "Registration successful"
    
    def login(self, username, password):
        """Login a user."""
        # Check if username exists
        if username not in self.users:
            return False, "Invalid username or password"
        
        # Get the user
        user = self.users[username]
        
        # Hash the password with the stored salt
        password_hash, _ = self._hash_password(password, user["salt"])
        
        # Check if password hash matches
        if password_hash != user["password_hash"]:
            return False, "Invalid username or password"
        
        # Update last login time
        user["last_login"] = datetime.now().isoformat()
        self._save_users()
        
        # Set the current user and create a session token
        self.current_user = username
        self.session_token = uuid.uuid4().hex
        
        return True, "Login successful"
    
    def logout(self):
        """Logout the current user."""
        self.current_user = None
        self.session_token = None
        return True, "Logout successful"
    
    def is_logged_in(self):
        """Check if a user is logged in."""
        return self.current_user is not None
    
    def get_current_user(self):
        """Get the current user."""
        return self.current_user
    
    def delete_account(self, username, password):
        """Delete a user account."""
        # Check if username exists
        if username not in self.users:
            return False, "Invalid username or password"
        
        # Get the user
        user = self.users[username]
        
        # Hash the password with the stored salt
        password_hash, _ = self._hash_password(password, user["salt"])
        
        # Check if password hash matches
        if password_hash != user["password_hash"]:
            return False, "Invalid username or password"
        
        # Delete the user
        del self.users[username]
        self._save_users()
        
        # Delete any save files for the user
        user_save_dir = os.path.join(SAVES_DIR, username)
        if os.path.exists(user_save_dir):
            for filename in os.listdir(user_save_dir):
                os.remove(os.path.join(user_save_dir, filename))
            os.rmdir(user_save_dir)
        
        # Logout if the current user is the deleted user
        if self.current_user == username:
            self.logout()
        
        return True, "Account deleted successfully"
    
    def save_game(self, game_state, save_name="default"):
        """Save a game state for the current user."""
        if not self.current_user:
            return False, "No user logged in"
        
        # Create the user saves directory if it doesn't exist
        user_save_dir = os.path.join(SAVES_DIR, self.current_user)
        os.makedirs(user_save_dir, exist_ok=True)
        
        # Save the game state
        save_file = os.path.join(user_save_dir, f"{save_name}.json")
        with open(save_file, 'w') as f:
            json.dump(game_state, f, indent=4)
        
        return True, "Game saved successfully"
    
    def load_game(self, save_name="default"):
        """Load a game state for the current user."""
        if not self.current_user:
            return None, "No user logged in"
        
        # Check if the save exists
        save_file = os.path.join(SAVES_DIR, self.current_user, f"{save_name}.json")
        if not os.path.exists(save_file):
            return None, "Save file not found"
        
        # Load the game state
        try:
            with open(save_file, 'r') as f:
                game_state = json.load(f)
            return game_state, "Game loaded successfully"
        except json.JSONDecodeError:
            return None, "Error loading save file"
    
    def get_save_files(self):
        """Get the list of save files for the current user."""
        if not self.current_user:
            return [], "No user logged in"
        
        # Check if the user saves directory exists
        user_save_dir = os.path.join(SAVES_DIR, self.current_user)
        if not os.path.exists(user_save_dir):
            return [], "No saves found"
        
        # Get the list of save files
        save_files = [os.path.splitext(f)[0] for f in os.listdir(user_save_dir) 
                     if os.path.isfile(os.path.join(user_save_dir, f)) and f.endswith('.json')]
        
        return save_files, "Save files retrieved"

# Create a global instance of the UserAuth class
user_auth = UserAuth()