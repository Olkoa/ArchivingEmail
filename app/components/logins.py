import hashlib
import pickle
from pathlib import Path
import os

# Define authentication functions
def make_hashed_password(password):
    """Create a hashed version of a password"""
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_users_db():
    """Initialize user database if it doesn't exist"""
    users_db_path = Path(os.path.dirname(__file__)) / ".streamlit" / "users.pkl"

    # Create .streamlit directory if it doesn't exist
    users_db_path.parent.mkdir(exist_ok=True)

    if not users_db_path.exists():
        # Create a default admin user
        default_users = {
            "admin": make_hashed_password("admin123"),
            "user": make_hashed_password("user123")
        }

        with open(users_db_path, "wb") as f:
            pickle.dump(default_users, f)


        return default_users

    # Load existing users
    with open(users_db_path, "rb") as f:
        return pickle.load(f)

def verify_password(username, password, users_db):
    """Verify if username and password match"""
    if username not in users_db:
        return False

    hashed_password = make_hashed_password(password)
    print("password match ? ", users_db[username] == hashed_password)
    return users_db[username] == hashed_password

def add_user(username, password):
    """Add a new user to the database"""
    users_db_path = Path(os.path.dirname(__file__)) / ".streamlit" / "users.pkl"

    # Load existing users
    with open(users_db_path, "rb") as f:
        users_db = pickle.load(f)

    # Add new user with hashed password
    users_db[username] = make_hashed_password(password)

    # Save updated database
    with open(users_db_path, "wb") as f:
        pickle.dump(users_db, f)

    return users_db
