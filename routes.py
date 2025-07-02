from flask import Blueprint, request, jsonify
from models import User, Note
# Assuming app.py will initialize users_db, notes_db, user_id_counter, note_id_counter, and current_user_id
# We might need to pass these to the blueprint or manage them differently.
# For simplicity now, we'll assume they are accessible globally from app.py,
# which is not ideal but works for a single file structure that will be combined later.

# The global variables users_db, notes_db, user_id_counter, note_id_counter, current_user_id
# are now expected to be defined and managed in app.py.
# We will import them or receive them from app.py context.

# For this iteration, assume app.py makes them available in the Flask app context
# or we modify app.py to pass them to the blueprint registration.
# A cleaner way is to use Flask's application context 'g' or pass instances.

# To make this runnable standalone initially, then integrate:
# from flask import current_app # To access app.users_db etc.
# However, for the current plan of merging into one file, direct access after merge is assumed.

# Let's get the global variables from app.py directly.
# This is not standard for Blueprints but will work once merged.
# If app.py runs this code directly (by importing functions or merging), it's fine.
from app import users_db, notes_db, user_id_counter as app_user_id_counter, \
                note_id_counter as app_note_id_counter, \
                current_user_id as app_current_user_id
from models import User, Note # User and Note classes
from flask import Blueprint, request, jsonify


api_bp = Blueprint('api', __name__)

# --- Helper Functions ---
# These helpers will now use the lists from app.py
def find_user_by_email(email):
    for user in users_db: # Uses users_db from app.py
        if user.email == email:
            return user
    return None

def find_user_by_id(user_id):
    for user in users_db: # Uses users_db from app.py
        if user.id == user_id:
            return user
    return None

def find_note_by_id(note_id):
    for note in notes_db: # Uses notes_db from app.py
        if note.id == note_id:
            return note
    return None

# --- Routes ---
@api_bp.route('/register', methods=['POST'])
def register_user_route():
    # Use global counters from app.py
    # To modify global variables from app.py, we need to declare them global here too,
    # or better, have app.py functions manage them.
    # For now, we assume app.py's counters are directly modifiable or app.py handles increment.
    # This is a tricky part with blueprints and global state not in app context.
    # Simplification: Assume these routes will be merged into app.py

    data = request.get_json()
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Missing required fields"}), 400

    if find_user_by_email(data['email']): # Uses app.users_db via helper
        return jsonify({"message": "Email already registered"}), 409
    if any(user.name == data['name'] for user in users_db): # Uses app.users_db
        return jsonify({"message": "Username already taken"}), 409

    # Accessing and modifying global counters from app.py is problematic here.
    # This part needs to be in app.py or counters managed via app context.
    # For now, let's assume this function will be moved to app.py or app.py updates counters.
    # Let's pretend we have a way to get the next ID.
    # In app.py, user_id_counter is global. If routes.py is imported by app.py,
    # it needs to refer to app.user_id_counter.
    # The import `from app import user_id_counter as app_user_id_counter` gives us read access.
    # To modify, we'd need `import app` and then `app.user_id_counter +=1`.

    import app # Required to modify app's global variables

    new_user = User(id=app.user_id_counter, name=data['name'], email=data['email'], password=data['password'])
    app.users_db.append(new_user)
    app.user_id_counter += 1
    return jsonify({"message": "User registered successfully", "user": new_user.to_dict()}), 201

@api_bp.route('/login', methods=['POST'])
def login_user_route():
    import app # Required to modify app.current_user_id

    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required"}), 400

    user = find_user_by_email(data['email']) # Uses app.users_db
    if user and user.password == data['password']: # Plain text password check
        app.current_user_id = user.id # Modify app's global current_user_id
        return jsonify({"message": "Login successful", "user_id": user.id, "is_admin": user.admin}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@api_bp.route('/logout', methods=['POST'])
def logout_user_route():
    import app # Required to modify app.current_user_id
    if app.current_user_id is None:
        return jsonify({"message": "Not currently logged in"}), 400
    logged_out_user_id = app.current_user_id
    app.current_user_id = None # Modify app's global
    return jsonify({"message": "Logout successful", "user_id": logged_out_user_id}), 200

# --- Notes Routes (Protected) ---
@api_bp.route('/notes', methods=['POST'])
def create_note_route():
    import app # Required for app.note_id_counter, app.current_user_id, app.notes_db
    if app.current_user_id is None:
        return jsonify({"message": "Authentication required"}), 401

    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({"message": "Title and content are required"}), 400

    new_note = Note(id=app.note_id_counter, title=data['title'], content=data['content'], owner_id=app.current_user_id)
    app.notes_db.append(new_note)
    app.note_id_counter += 1
    return jsonify({"message": "Note created successfully", "note": new_note.to_dict()}), 201

@api_bp.route('/notes', methods=['GET'])
def get_user_notes_route():
    import app # Required for app.current_user_id, app.notes_db
    if app.current_user_id is None:
        return jsonify({"message": "Authentication required"}), 401

    user_notes = [note.to_dict() for note in app.notes_db if note.owner_id == app.current_user_id]
    return jsonify(user_notes), 200

@api_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note_by_id_route(note_id):
    import app # Required for app.current_user_id
    if app.current_user_id is None:
        return jsonify({"message": "Authentication required"}), 401

    note = find_note_by_id(note_id) # Uses app.notes_db
    if not note:
        return jsonify({"message": "Note not found"}), 404

    requesting_user = find_user_by_id(app.current_user_id) # Uses app.users_db
    if note.owner_id != app.current_user_id and (not requesting_user or not requesting_user.admin):
        return jsonify({"message": "Access forbidden"}), 403
    return jsonify(note.to_dict()), 200

@api_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note_route(note_id):
    import app # Required for app.current_user_id
    if app.current_user_id is None:
        return jsonify({"message": "Authentication required"}), 401

    note = find_note_by_id(note_id) # Uses app.notes_db
    if not note:
        return jsonify({"message": "Note not found"}), 404
    if note.owner_id != app.current_user_id: # Only owner can update
        return jsonify({"message": "Access forbidden: You are not the owner"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    # No need to re-append to app.notes_db as 'note' is a reference to the object in the list
    return jsonify({"message": "Note updated successfully", "note": note.to_dict()}), 200

@api_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note_route(note_id):
    import app # Required for app.current_user_id, app.notes_db
    if app.current_user_id is None:
        return jsonify({"message": "Authentication required"}), 401

    note_to_delete = find_note_by_id(note_id) # Uses app.notes_db
    if not note_to_delete:
        return jsonify({"message": "Note not found"}), 404

    requesting_user = find_user_by_id(app.current_user_id) # Uses app.users_db
    if not requesting_user:
         return jsonify({"message": "Requesting user not found"}), 500

    if note_to_delete.owner_id != app.current_user_id and not requesting_user.admin:
        return jsonify({"message": "Access forbidden: You are not the owner or an admin"}), 403

    app.notes_db.remove(note_to_delete)
    return jsonify({"message": "Note deleted successfully"}), 200

# --- Admin Routes ---
@api_bp.route('/admin/users/<int:user_id_to_delete>', methods=['DELETE'])
def delete_user_by_admin_route(user_id_to_delete):
    import app # Required for app globals
    if app.current_user_id is None:
        return jsonify({"message": "Authentication required"}), 401

    admin_user = find_user_by_id(app.current_user_id) # Uses app.users_db
    if not admin_user or not admin_user.admin:
        return jsonify({"message": "Administrator access required"}), 403

    user_to_delete = find_user_by_id(user_id_to_delete) # Uses app.users_db
    if not user_to_delete:
        return jsonify({"message": "User to delete not found"}), 404

    if user_to_delete.id == app.current_user_id : # Admin cannot delete themselves
        return jsonify({"message": "Admin cannot delete themselves"}), 403

    # Filter notes: note that this creates a new list.
    app.notes_db = [note for note in app.notes_db if note.owner_id != user_id_to_delete]
    app.users_db.remove(user_to_delete)

    return jsonify({"message": f"User {user_to_delete.name} and their notes deleted successfully"}), 200

@api_bp.route('/admin/users', methods=['GET'])
def get_all_users_route():
    import app # Required for app.current_user_id
    if app.current_user_id is None:
        return jsonify({"message": "Authentication required"}), 401

    admin_user = find_user_by_id(app.current_user_id) # Uses app.users_db
    if not admin_user or not admin_user.admin:
        return jsonify({"message": "Administrator access required"}), 403

    return jsonify([user.to_dict() for user in app.users_db]), 200 # Uses app.users_db

@api_bp.route('/admin/notes', methods=['GET'])
def get_all_notes_route():
    import app # Required for app.current_user_id
    if app.current_user_id is None:
        return jsonify({"message": "Authentication required"}), 401

    admin_user = find_user_by_id(app.current_user_id) # Uses app.users_db
    if not admin_user or not admin_user.admin:
        return jsonify({"message": "Administrator access required"}), 403

    return jsonify([note.to_dict() for note in app.notes_db]), 200 # Uses app.notes_db
