import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import hashlib
import secrets

class DatabaseManager:
    def __init__(self, db_path: str = "uptime_monitor.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Enable Write Ahead Logs
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                category TEXT DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(url, user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_code INTEGER,
                status TEXT,
                response_time_ms INTEGER,
                FOREIGN KEY (url_id) REFERENCES urls (id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_urls_user_id ON urls(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_checks_url_id ON checks(url_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_checks_timestamp ON checks(timestamp)')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str, salt: str = None) -> tuple:
        if salt is None:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return pwd_hash.hex(), salt

    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        pwd_hash, _ = self.hash_password(password, salt)
        return pwd_hash == hashed_password
    
    def create_user(self, username: str, password: str, email: str) -> Optional[int]:
        password_hash, salt = self.hash_password(password)
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt, email) 
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, salt, email))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            if conn:
                conn.close()
            return None
    
    def verify_user(self, username: str, password: str) -> Optional[int]:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, password_hash, salt FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()

        if result and self.verify_password(password, result[2], result[3]):
            return result[0],result[1]  # Return user_id
        return None
    
    def add_url(self, url: str, user_id: int, category: str = None) -> bool:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO urls (url, user_id, category) VALUES (?, ?, ?)", 
                         (url, user_id, category))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # URL already exists for this user
            if conn:
                conn.close()
            return False
        except sqlite3.OperationalError as e:
            if conn:
                conn.close()
            print(f"Database error: {e}")
            return False
    
    def remove_url(self, url: str, user_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            
            # Get URL ID first
            cursor.execute("SELECT id FROM urls WHERE url = ? AND user_id = ?", (url, user_id))
            url_result = cursor.fetchone()
            
            if not url_result:
                conn.close()
                return False
            
            url_id = url_result[0]
            
            # Delete checks first (foreign key constraint)
            cursor.execute("DELETE FROM checks WHERE url_id = ?", (url_id,))
            
            # Delete URL
            cursor.execute("DELETE FROM urls WHERE id = ?", (url_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            if conn:
                conn.close()
            print(f"Error removing URL: {e}")
            return False
    
    def get_user_urls(self, user_id: int) -> List[Dict]:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, url, created_at, category 
            FROM urls 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        results = cursor.fetchall()
        conn.close()
        
        return [{"id": row[0], "url": row[1], "created_at": row[2], "category": row[3]} 
                for row in results]
    
    def get_all_urls(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute("SELECT id, url, created_at, user_id FROM urls")
        results = cursor.fetchall()
        conn.close()
        
        return [{"id": row[0], "url": row[1], "created_at": row[2], "user_id": row[3]} 
                for row in results]
    
    def user_owns_url(self, url: str, user_id: int) -> bool:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM urls WHERE url = ? AND user_id = ?", (url, user_id))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def get_url_id(self, url: str, user_id: int = None) -> Optional[int]:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("SELECT id FROM urls WHERE url = ? AND user_id = ?", (url, user_id))
        else:
            cursor.execute("SELECT id FROM urls WHERE url = ?", (url,))
            
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def add_check_result(self, url_id: int, response_code: int, status: str, response_time_ms: int):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO checks (url_id, response_code, status, response_time_ms) 
            VALUES (?, ?, ?, ?)
        ''', (url_id, response_code, status, response_time_ms))
        conn.commit()
        conn.close()
    
    def get_url_status(self, url: str, user_id: int = None) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # Get URL info with user check
        if user_id:
            cursor.execute("SELECT id, category FROM urls WHERE url = ? AND user_id = ?", (url, user_id))
        else:
            cursor.execute("SELECT id, category FROM urls WHERE url = ?", (url,))
            
        url_result = cursor.fetchone()
        if not url_result:
            conn.close()
            return None
        
        url_id, category = url_result
        
        # Get latest check
        cursor.execute('''
            SELECT timestamp, status, response_code 
            FROM checks 
            WHERE url_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''', (url_id,))
        latest_check = cursor.fetchone()
        
        # Calculate uptime percentage (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute('''
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
            FROM checks 
            WHERE url_id = ? AND timestamp > ?
        ''', (url_id, yesterday.isoformat()))
        
        uptime_data = cursor.fetchone()
        total_checks, successful_checks = uptime_data
        
        uptime_percentage = (successful_checks / total_checks * 100) if total_checks > 0 else 0
        
        conn.close()
        
        result = {
            "url": url,
            "uptime_percentage": round(uptime_percentage, 2),
            "last_checked": latest_check[0] if latest_check else None
        }
        
        if category:
            result["category"] = category
            
        return result
    
    def get_url_logs(self, url: str, user_id: int = None, limit: int = 100) -> List[Dict]:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT c.timestamp, c.status, c.response_time_ms, c.response_code
                FROM checks c
                JOIN urls u ON c.url_id = u.id
                WHERE u.url = ? AND u.user_id = ?
                ORDER BY c.timestamp DESC
                LIMIT ?
            ''', (url, user_id, limit))
        else:
            cursor.execute('''
                SELECT c.timestamp, c.status, c.response_time_ms, c.response_code
                FROM checks c
                JOIN urls u ON c.url_id = u.id
                WHERE u.url = ?
                ORDER BY c.timestamp DESC
                LIMIT ?
            ''', (url, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": row[0],
                "status": row[1],
                "response_time_ms": row[2],
                "http_code": row[3]
            }
            for row in results
        ]
    
    def update_url_category(self, url: str, user_id: int, category: str) -> bool:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE urls SET category = ? 
                WHERE url = ? AND user_id = ?
            ''', (category, url, user_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            if conn:
                conn.close()
            print(f"Error updating category: {e}")
            return False

    def get_user_info(self, user_id: int) -> dict:
        query = "SELECT id, username, email FROM users WHERE id = ?"
        
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        conn.close()
        if result:
            return {
                "user_id": result[0][0],
                "username": result[0][1],
                "email": result[0][2] if len(result[0]) > 2 else None
            }
        return None

    def get_users_with_urls(self) -> list:
        query = """
        SELECT DISTINCT u.id, u.username, u.email 
        FROM users u 
        INNER JOIN urls url ON u.id = url.user_id
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute(query, ())
        results = cursor.fetchall()
        conn.close()
        
        if results:
            return [
                {
                    "user_id": row[0],
                    "username": row[1],
                    "email": row[2] if len(row) > 2 else f"{row[1]}@example.com"  # fallback email
                }
                for row in results
            ]
        return []

    def get_user_urls_with_status(self, user_id: int) -> list:
        query = """
        SELECT 
            url.url,
            url.category,
            url.created_at,
            COALESCE(
                ROUND(
                    (COUNT(CASE WHEN cr.status = 'success' THEN 1 END) * 100.0) / 
                    NULLIF(COUNT(cr.id), 0), 2
                ), 0
            ) as uptime_percentage,
            MAX(cr.checked_at) as last_checked
        FROM urls url
        LEFT JOIN check_results cr ON url.id = cr.url_id 
            AND cr.checked_at >= datetime('now', '-24 hours')
        WHERE url.user_id = ?
        GROUP BY url.id, url.url, url.category, url.created_at
        ORDER BY url.created_at DESC
        """
        
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        conn.close()
        
        if results:
            return [
                {
                    "url": row[0],
                    "category": row[1],
                    "created_at": row[2],
                    "uptime_percentage": row[3],
                    "last_checked": row[4]
                }
                for row in results
            ]
        return []