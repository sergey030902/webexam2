from flask_login import current_user

class CheckRights:
    def __init__(self, record):
        self.record = record

    def create_book(self):
        return current_user.is_admin()

    def edit_book(self):
        return current_user.is_admin() or current_user.is_moderator()

    def delete_book(self):
        return current_user.is_admin()
    
    def show_collection(self):
        return current_user.is_admin() or current_user.is_user()
    
    def add_collection(self):
        return current_user.is_admin() or current_user.is_user()


