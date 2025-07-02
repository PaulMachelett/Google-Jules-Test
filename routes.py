from flask import Blueprint, request, jsonify
from models import User, Note # SQLAlchemy models
import app as main_app # To access main_app.current_user_id and get_db_session

api_bp = Blueprint('api', __name__)

# Helper function to get the current user object from DB
def get_current_user():
    if main_app.current_user_id is None:
        return None
    session = main_app.get_db_session()
    return session.query(User).get(main_app.current_user_id)

@api_bp.route('/register', methods=['POST'])
def register_user_route():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Missing required fields"}), 400

    session = main_app.get_db_session()

    # Check for existing user by email or name
    existing_by_email = session.query(User).filter_by(email=data['email']).first()
    if existing_by_email:
        return jsonify({"message": "Email already registered"}), 409

    existing_by_name = session.query(User).filter_by(name=data['name']).first()
    if existing_by_name:
        return jsonify({"message": "Username already taken"}), 409

    # In a real app, hash the password here: e.g., User(..., password_hash=generate_hash(data['password']))
    # For mock, password stored as is in password_hash field.
    new_user = User(name=data['name'], email=data['email'], password=data['password'])

    try:
        session.add(new_user)
        session.commit()
    except Exception as e:
        session.rollback()
        # Check if the exception is due to our mock unique constraint
        if "MockDB IntegrityError" in str(e):
             return jsonify({"message": str(e)}), 409
        return jsonify({"message": f"Could not register user: {str(e)}"}), 500

    return jsonify({"message": "User registered successfully", "user": new_user.to_dict()}), 201

@api_bp.route('/login', methods=['POST'])
def login_user_route():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required"}), 400

    session = main_app.get_db_session()
    user = session.query(User).filter_by(email=data['email']).first()

    # user.check_password will compare plain text for mock
    if user and user.check_password(data['password']):
        main_app.current_user_id = user.id # Simulate session/token by setting global var
        return jsonify({"message": "Login successful", "user_id": user.id, "is_admin": user.admin}), 200

    return jsonify({"message": "Invalid credentials"}), 401

@api_bp.route('/logout', methods=['POST'])
def logout_user_route():
    if main_app.current_user_id is None:
        return jsonify({"message": "Not currently logged in"}), 400

    logged_out_user_id = main_app.current_user_id
    main_app.current_user_id = None
    return jsonify({"message": "Logout successful", "user_id": logged_out_user_id}), 200

# --- Notes Routes (Protected) ---
@api_bp.route('/notes', methods=['POST'])
def create_note_route():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({"message": "Title and content are required"}), 400

    session = main_app.get_db_session()
    new_note = Note(title=data['title'], content=data['content'], owner_id=current_user.id)

    try:
        session.add(new_note)
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Could not create note: {str(e)}"}), 500

    return jsonify({"message": "Note created successfully", "note": new_note.to_dict()}), 201

@api_bp.route('/notes', methods=['GET'])
def get_user_notes_route():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    session = main_app.get_db_session()
    # Using relationship (if lazy='dynamic', this would be current_user.notes.all())
    # For lazy='True' (default or specified), current_user.notes is already a list
    # Or query directly:
    user_notes_query = session.query(Note).filter_by(owner_id=current_user.id)
    user_notes = user_notes_query.all()

    return jsonify([note.to_dict() for note in user_notes]), 200

@api_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note_by_id_route(note_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    session = main_app.get_db_session()
    note = session.query(Note).get(note_id)

    if not note:
        return jsonify({"message": "Note not found"}), 404

    if note.owner_id != current_user.id and not current_user.admin:
        return jsonify({"message": "Access forbidden"}), 403

    return jsonify(note.to_dict()), 200

@api_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note_route(note_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    session = main_app.get_db_session()
    note = session.query(Note).get(note_id)

    if not note:
        return jsonify({"message": "Note not found"}), 404

    if note.owner_id != current_user.id: # Only owner can update
        return jsonify({"message": "Access forbidden: You are not the owner"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided for update"}), 400

    updated = False
    if 'title' in data:
        note.title = data['title']
        updated = True
    if 'content' in data:
        note.content = data['content']
        updated = True

    if updated:
        try:
            # session.add(note) # Not strictly necessary if object is already in session and modified
            session.commit()
        except Exception as e:
            session.rollback()
            return jsonify({"message": f"Could not update note: {str(e)}"}), 500

    return jsonify({"message": "Note updated successfully", "note": note.to_dict()}), 200

@api_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note_route(note_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    session = main_app.get_db_session()
    note_to_delete = session.query(Note).get(note_id)

    if not note_to_delete:
        return jsonify({"message": "Note not found"}), 404

    if note_to_delete.owner_id != current_user.id and not current_user.admin:
        return jsonify({"message": "Access forbidden: You are not the owner or an admin"}), 403

    try:
        session.delete(note_to_delete)
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Could not delete note: {str(e)}"}), 500

    return jsonify({"message": "Note deleted successfully"}), 200

# --- Admin Routes ---
@api_bp.route('/admin/users/<int:user_id_to_delete>', methods=['DELETE'])
def delete_user_by_admin_route(user_id_to_delete):
    admin_user = get_current_user()
    if not admin_user or not admin_user.admin:
        return jsonify({"message": "Administrator access required"}), 403

    if admin_user.id == user_id_to_delete:
        return jsonify({"message": "Admin cannot delete themselves"}), 403

    session = main_app.get_db_session()
    user_to_delete = session.query(User).get(user_id_to_delete)

    if not user_to_delete:
        return jsonify({"message": "User to delete not found"}), 404

    try:
        # Notes will be cascade deleted due to model relationship `cascade="all, delete-orphan"`
        # and MockDBSession's commit logic handles this for users.
        session.delete(user_to_delete)
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Could not delete user: {str(e)}"}), 500

    return jsonify({"message": f"User '{user_to_delete.name}' and their notes deleted successfully"}), 200

@api_bp.route('/admin/users', methods=['GET'])
def get_all_users_route():
    admin_user = get_current_user()
    if not admin_user or not admin_user.admin:
        return jsonify({"message": "Administrator access required"}), 403

    session = main_app.get_db_session()
    all_users = session.query(User).all()
    return jsonify([user.to_dict() for user in all_users]), 200

@api_bp.route('/admin/notes', methods=['GET'])
def get_all_notes_route():
    admin_user = get_current_user()
    if not admin_user or not admin_user.admin:
        return jsonify({"message": "Administrator access required"}), 403

    session = main_app.get_db_session()
    all_notes = session.query(Note).all()
    return jsonify([note.to_dict() for note in all_notes]), 200
