from flask import Flask
from flask_sqlalchemy import SQLAlchemy # Direct import for db instance

# --- Database Setup ---
# Initialize SQLAlchemy extension instance directly in app.py for now
db = SQLAlchemy()

app = Flask(__name__)
# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Using in-memory for simulation
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the app
db.init_app(app)


# --- MockDBSession ---
class MockDBSession:
    def __init__(self):
        self._data = {}  # Stores data as { 'tablename': [objects] }
        self._temp_added = []  # Objects added but not committed
        self._temp_deleted = []  # Objects marked for deletion but not committed
        self._id_counters = {}  # Simulates auto-incrementing IDs { 'tablename': counter }

    def _get_table_name(self, model_or_instance):
        if hasattr(model_or_instance, '__tablename__'): # Class
            return model_or_instance.__tablename__
        return model_or_instance.__class__.__tablename__ # Instance

    def _get_next_id(self, tablename):
        if tablename not in self._id_counters:
            self._id_counters[tablename] = 0
        self._id_counters[tablename] += 1
        return self._id_counters[tablename]

    def clear_all_data(self):
        self._data = {}
        self._temp_added = []
        self._temp_deleted = []
        self._id_counters = {}
        print("MockDBSession data cleared.")

    def add(self, instance):
        if not hasattr(instance, 'id') or instance.id is None:
            tablename = self._get_table_name(instance)
            instance.id = self._get_next_id(tablename)

        if instance in self._temp_deleted:
            self._temp_deleted.remove(instance)

        if instance not in self._temp_added:
            self._temp_added.append(instance)

    def delete(self, instance):
        if instance in self._temp_added:
            self._temp_added.remove(instance)
        if instance not in self._temp_deleted:
            self._temp_deleted.append(instance)

    def commit(self):
        from models import User # Import models locally to avoid circular on app load
        # Process additions/updates
        for instance in self._temp_added:
            tablename = self._get_table_name(instance)
            if tablename not in self._data:
                self._data[tablename] = []

            if tablename == User.__tablename__: # Specific check for User model
                # Check existing persistent data
                for u_existing in self._data[tablename]:
                    if u_existing.id != instance.id:
                        if u_existing.email == instance.email:
                            self.rollback()
                            raise Exception(f"MockDB IntegrityError: Email '{instance.email}' already exists for user ID {u_existing.id}.")
                        if u_existing.name == instance.name:
                            self.rollback()
                            raise Exception(f"MockDB IntegrityError: Name '{instance.name}' already exists for user ID {u_existing.id}.")
                # Check against other items being committed
                for u_temp in self._temp_added:
                    if u_temp != instance:
                         if u_temp.email == instance.email:
                            self.rollback()
                            raise Exception(f"MockDB IntegrityError: Email '{instance.email}' is duplicated in current transaction.")
                         if u_temp.name == instance.name:
                            self.rollback()
                            raise Exception(f"MockDB IntegrityError: Name '{instance.name}' is duplicated in current transaction.")

            self._data[tablename] = [obj for obj in self._data[tablename] if obj.id != instance.id]
            self._data[tablename].append(instance)

        # Process deletions
        from models import Note # Import models locally
        for instance_to_delete in self._temp_deleted:
            tablename = self._get_table_name(instance_to_delete)
            if tablename in self._data:
                if tablename == User.__tablename__ and Note.__tablename__ in self._data:
                    self._data[Note.__tablename__] = [
                        note for note in self._data[Note.__tablename__] if note.owner_id != instance_to_delete.id
                    ]
                self._data[tablename] = [obj for obj in self._data[tablename] if obj.id != instance_to_delete.id]

        self._temp_added = []
        self._temp_deleted = []

    def rollback(self):
        self._temp_added = []
        self._temp_deleted = []

    def query(self, model_class):
        tablename = self._get_table_name(model_class)
        if tablename not in self._data:
            self._data[tablename] = []
        return MockQuery(model_class, list(self._data[tablename]))


class MockQuery:
    def __init__(self, model_class, data_list):
        self.model_class = model_class
        self.current_query_results = data_list

    def get(self, ident):
        for item in self.current_query_results:
            if hasattr(item, 'id') and item.id == ident:
                return item
        return None

    def all(self):
        return list(self.current_query_results)

    def first(self):
        return self.current_query_results[0] if self.current_query_results else None

    def filter_by(self, **kwargs):
        filtered = []
        for item in self.current_query_results:
            match = all(hasattr(item, k) and getattr(item, k) == v for k, v in kwargs.items())
            if match:
                filtered.append(item)
        return MockQuery(self.model_class, filtered)

    def count(self):
        return len(self.current_query_results)

mock_db_session_instance = MockDBSession()

def get_db_session():
    return mock_db_session_instance

# --- End MockDBSession ---


# current_user_id will store the ID of the logged-in user (SQLAlchemy model ID)
current_user_id = None

# --- Dummy Data Initialization ---
def initialize_dummy_data():
    from models import User, Note # Import here to ensure db is initialized

    session = get_db_session()
    session.clear_all_data() # Clear previous mock data

    try:
        # Create Admin User
        admin_user = User(name="admin", email="admin@example.com", password="adminpassword", admin=True)
        session.add(admin_user)

        # Create Normal User 1
        user1 = User(name="testuser1", email="test1@example.com", password="password1")
        session.add(user1)

        # Create Normal User 2
        user2 = User(name="testuser2", email="test2@example.com", password="password2")
        session.add(user2)

        session.commit() # Commit users first to get their IDs for notes

        # Add notes for user1 (assuming IDs are now set by mock session)
        note1_user1 = Note(title="User1 Note 1", content="Content for note 1 by user1", owner_id=user1.id)
        session.add(note1_user1)
        note2_user1 = Note(title="User1 Note 2", content="Content for note 2 by user1", owner_id=user1.id)
        session.add(note2_user1)

        # Add notes for user2
        note1_user2 = Note(title="User2 Note A", content="Content for note A by user2", owner_id=user2.id)
        session.add(note1_user2)

        session.commit()
        print(f"Dummy data initialized with MockDBSession. Users: {session.query(User).count()}, Notes: {session.query(Note).count()}")

    except Exception as e:
        session.rollback()
        print(f"Error initializing dummy data: {e}")


# Import and register blueprints
# This needs to be after db, MockDBSession, and get_db_session are defined.
# Also, models.py needs to be updated to import 'db' from 'app' now.

# Defer blueprint import and registration
# from routes import api_bp # routes.py will need adjustments for get_db_session
# app.register_blueprint(api_bp, url_prefix='/api')


def create_mock_tables():
    """Simulates creating tables by ensuring the mock session is ready."""
    # For mock, this mainly means clearing old data if any.
    # The real db.create_all() is not called for the mock.
    mock_db_session_instance.clear_all_data()
    print("Mock 'create_tables' called. MockDBSession cleared and ready.")

# Function to register blueprints to break circular import
def register_blueprints(flask_app):
    from routes import api_bp # Import here, when app and db are defined
    flask_app.register_blueprint(api_bp, url_prefix='/api')
    print("Registered API blueprint at /api")

# Call after app and db are initialized, but before running the app
register_blueprints(app)


if __name__ == '__main__':
    with app.app_context():
        # This would be db.create_all() for a real DB
        create_mock_tables()
        initialize_dummy_data()

    # print("Registered API blueprint at /api") # Moved into register_blueprints
    print("SQLAlchemy configured for 'sqlite:///:memory:' (simulated with MockDBSession in app.py).")
    app.run(debug=True)
