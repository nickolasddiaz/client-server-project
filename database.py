import sqlite3
import bcrypt  # 72-character limit
import jwt
from datetime import datetime, timedelta, timezone


class DataStorage():
    """
    Goal:
    store username and passwords, be able to verify users
    Store/retrieve network statistics, such as upload/download data rates, file transfer times
    and system response times
    """

    def __init__(self, jwt_secret_key: str):
        self.jwt_secret_key = jwt_secret_key
        self.conn = sqlite3.connect('data.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS users
                            (
                                ID            integer PRIMARY KEY AUTOINCREMENT,
                                username      TEXT UNIQUE,
                                password_hash BLOB
                            )
                            """
                            )
        self.conn.commit()

        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS statistics
                            (
                                ID            INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id       INTEGER,
                                upload_rate   REAL,
                                download_rate REAL,
                                transfer_time REAL,
                                response_time REAL,
                                timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES users (ID)
                            )
                            """)
        self.conn.commit()

    def _verify_credentials(self, username: str, password: str) -> bool:
        """Internal method to verify username and password."""
        self.cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()

        if row:
            stored_hash = row[0]
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

        # if no user is found
        else:
            return False

    def get_token(self, username: str, password: str):
        """Verify user credentials and return JWT token if successful, False otherwise."""
        if not self._verify_credentials(username, password):
            return False

        # Get user ID
        self.cursor.execute("SELECT ID FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        user_id = row[0]

        # Create JWT token
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)  # Token expires in 24 hours
        }

        token = jwt.encode(payload, self.jwt_secret_key, algorithm='HS256')
        return token

    def verify_token(self, token: str):
        """Verify JWT token and return payload if valid, False otherwise."""
        try:
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return False  # Token has expired
        except jwt.InvalidTokenError:
            return False  # Invalid token

    def create_user(self, username: str, password: str) -> bool:

        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)

        try:
            self.cursor.execute("""
                                INSERT INTO users (username, password_hash)
                                VALUES (?, ?)
                                """, (username, hashed_pw))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_user(self, username: str) -> bool:
        """Delete a user by username."""
        self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.conn.commit()

        # how many affected rows
        return self.cursor.rowcount > 0

    def set_statistics(self, username: str, upload_rate: float, download_rate: float,
                       transfer_time: float, response_time: float) -> bool:
        """Store network performance metrics for a given user."""
        # Get user ID
        self.cursor.execute("SELECT ID FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()

        if not row:
            return False  # user not found

        user_id = row[0]

        self.cursor.execute("""
                            INSERT INTO statistics (user_id, upload_rate, download_rate, transfer_time, response_time)
                            VALUES (?, ?, ?, ?, ?)
                            """, (user_id, upload_rate, download_rate, transfer_time, response_time))
        self.conn.commit()
        return True

    def get_statistics(self, username: str, password: str) -> dict:
        """Return the most recent network statistics for a verified user."""
        if not self._verify_credentials(username, password):
            return {"error": "Invalid username or password"}

        self.cursor.execute("""
                            SELECT s.upload_rate, s.download_rate, s.transfer_time, s.response_time, s.timestamp
                            FROM statistics s
                                     JOIN users u ON s.user_id = u.ID
                            WHERE u.username = ?
                            ORDER BY s.timestamp DESC
                            LIMIT 1
                            """, (username,))
        row = self.cursor.fetchone()

        if not row:
            return {"message": "No statistics found for this user"}

        return {
            "upload_rate": row[0],
            "download_rate": row[1],
            "transfer_time": row[2],
            "response_time": row[3],
            "timestamp": row[4]
        }

    def __del__(self):
        self.conn.close()


if __name__ == "__main__":
    data = DataStorage(jwt_secret_key="random_secret_key")

    # Create users
    print("Creating users:")
    print(data.create_user("alice1", "pass1"))  # True
    print(data.create_user("alice1", "pass1"))  # False (duplicate)
    print(data.create_user("bob2", "pass2"))  # True
    print(data.create_user("admin", "admin"))  # True

    # Get token for valid credentials
    print("\nGetting token for alice1:")
    token = data.get_token("alice1", "pass1")
    print(f"Token: {token}")

    # Verify token
    print("\nVerifying token:")
    payload = data.verify_token(token)
    print(f"Payload: {payload}")

    # Test with invalid credentials
    print("\nTesting invalid credentials:")
    invalid_token = data.get_token("alice1", "wrongpass")
    print(f"Invalid credentials result: {invalid_token}")  # False

    # Test with invalid token
    print("\nTesting invalid token:")
    invalid_result = data.verify_token("invalid.token.here")
    print(f"Invalid token result: {invalid_result}")  # False

    # Test statistics
    print("\nTesting statistics:")
    print(data.set_statistics("alice1", 1.2, 2.3, 54.6, 3.9))
    print(data.get_statistics("alice1", "pass1"))
    print(data.delete_user("bob2"))