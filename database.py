import sqlite3
import bcrypt # not default it python
# 72-character limit



class DataStorage():
    """
    Goal:
    store username and passwords, be able to verify users
    Store/retrieve network statistics, such as upload/download data rates, file transfer times
    and system response times
    """

    def __init__(self):
        conn = sqlite3.connect('data.db')


    def verify_user(self, username: str, password: str) -> bool:
        pass

    def create_user(self, username: str, password: str) -> bool:
        pass

    def delete_user(self, username: str) -> bool:
        pass

    @staticmethod
    def hash_password(password: str) -> bytes:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed_password

    @staticmethod
    def check_password(password, hashed_password) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password)


    def get_statistics(self, username: str, password: str) -> dict:
        pass

    def set_statistics(self):
        pass


