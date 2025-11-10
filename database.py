from dataclasses import dataclass
import sqlite3
import bcrypt # not default it python
# 72-character limit



class DataStorage():

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



@dataclass
class NetworkStat():
    """
    Stores the network statistics
    the amount in bytes in seconds
    for the response, download and upload
    Calculate the rate seconds/bytes
    """

    response_seconds: float = 0.0
    response_amount: float = 0.0
    download_seconds: float = 0.0
    download_amount: int = 0.0
    upload_seconds: float = 0.0
    upload_amount: int = 0.0
