from app import db # Import the db instance from app.py

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False) # Store password hashes
    admin = db.Column(db.Boolean, default=False, nullable=False)

    notes = db.relationship('Note', backref='owner', lazy=True, cascade="all, delete-orphan")

    def __init__(self, name, email, password, admin=False):
        self.name = name
        self.email = email
        # In a real app, you'd call a password hashing function here
        self.password_hash = password # For mock, we'll keep it simple. Real app: generate_password_hash(password)
        self.admin = admin

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "admin": self.admin
            # password_hash is NOT returned
        }

    # Helper for password checking (real app would use check_password_hash)
    def check_password(self, password):
        return self.password_hash == password # Simplified for mock


class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, title, content, owner_id):
        self.title = title
        self.content = content
        self.owner_id = owner_id

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "owner_id": self.owner_id
        }
