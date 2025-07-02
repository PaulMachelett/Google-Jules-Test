class User:
    def __init__(self, id, name, email, password, admin=False):
        self.id = id
        self.name = name
        self.email = email
        self.password = password  # In a real app, hash this!
        self.admin = admin

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "admin": self.admin
            # Password is not returned for security
        }

class Note:
    def __init__(self, id, title, content, owner_id):
        self.id = id
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
