from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_data):
        """
        Initializes a User object from a database row.
        user_data is expected to be a tuple from the database.
        """
        if user_data:
            self.id = user_data[0]
            self.full_name = user_data[1]
            self.password_hash = user_data[2]
            self.email = user_data[3]
            self.phone_number = user_data[4]
            self.country = user_data[5]
            self.user_type = user_data[6]
        else:
            self.id = None
            
    def get_id(self):
        """Returns the user_id."""
        return self.id

    @property
    def is_active(self):
        # For this application, all users are active.
        return True 