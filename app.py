from flask import Flask, request, jsonify

app = Flask(__name__)

from models import User, Note

# In-memory "databases"
users_db = []
notes_db = []
user_id_counter = 1
note_id_counter = 1

# Dummy session management (in a real app, use Flask-Login or JWT)
# This will be managed by login/logout logic.
# We'll simulate it by setting this global variable upon login.
current_user_id = None


# --- Initialize Dummy Data ---
def initialize_data():
    global user_id_counter, note_id_counter
    # Create Admin User
    admin_user = User(id=user_id_counter, name="admin", email="admin@example.com", password="adminpassword", admin=True)
    users_db.append(admin_user)
    user_id_counter += 1

    # Create Normal User 1
    user1 = User(id=user_id_counter, name="testuser1", email="test1@example.com", password="password1")
    users_db.append(user1)
    user_id_counter += 1

    # Create Normal User 2
    user2 = User(id=user_id_counter, name="testuser2", email="test2@example.com", password="password2")
    users_db.append(user2)
    user_id_counter += 1

    # Add notes for user1
    notes_db.append(Note(id=note_id_counter, title="User1 Note 1", content="Content for note 1 by user1", owner_id=user1.id))
    note_id_counter += 1
    notes_db.append(Note(id=note_id_counter, title="User1 Note 2", content="Content for note 2 by user1", owner_id=user1.id))
    note_id_counter += 1

    # Add notes for user2
    notes_db.append(Note(id=note_id_counter, title="User2 Note A", content="Content for note A by user2", owner_id=user2.id))
    note_id_counter += 1

    print("Dummy data initialized:")
    print(f"{len(users_db)} users, {len(notes_db)} notes.")

initialize_data()

# Import blueprints after data initialization if routes depend on it, or pass data stores
# For now, routes.py also initializes some data or expects these to be global.
# This needs to be harmonized. The routes.py initializations will be removed.

if __name__ == '__main__':
    # Register Blueprints
    from routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    print("Registered API blueprint at /api")
    app.run(debug=True)
