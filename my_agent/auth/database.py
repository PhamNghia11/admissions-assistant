import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

DB_PATH = os.getenv(
    "AUTH_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "users.db"),
)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        avatar_url TEXT,
        provider TEXT NOT NULL,
        google_id TEXT UNIQUE,
        created_at TEXT NOT NULL,
        last_login TEXT NOT NULL
    );
    """)
    
    # 2. Create otp_records table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otp_records (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        code_hash TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used INTEGER DEFAULT 0,
        attempts INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    """)
    
    # 3. Create oauth_states table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS oauth_states (
        state TEXT PRIMARY KEY,
        expires_at TEXT NOT NULL
    );
    """)
    
    # Create indexes for optimal querying
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_otp_email_created ON otp_records (email, created_at);")
    
    conn.commit()
    conn.close()

# --- OTP Database Operations ---

def check_otp_rate_limit(email: str) -> bool:
    """Returns True if user has NOT exceeded rate limit (max 5 OTPs per hour)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    cursor.execute("""
        SELECT COUNT(*) FROM otp_records 
        WHERE email = ? AND created_at > ?
    """, (email, one_hour_ago))
    
    count = cursor.fetchone()[0]
    conn.close()
    return count < 5

def check_otp_cooldown(email: str) -> bool:
    """Returns True if the cooldown is active (requested < 60 seconds ago)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    sixty_seconds_ago = (datetime.utcnow() - timedelta(seconds=60)).isoformat()
    cursor.execute("""
        SELECT COUNT(*) FROM otp_records 
        WHERE email = ? AND created_at > ?
    """, (email, sixty_seconds_ago))
    
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def save_otp(otp_id: str, email: str, code_hash: str, expires_at: datetime) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    
    now_str = datetime.utcnow().isoformat()
    expires_str = expires_at.isoformat()
    
    cursor.execute("""
        INSERT INTO otp_records (id, email, code_hash, expires_at, used, attempts, created_at)
        VALUES (?, ?, ?, ?, 0, 0, ?)
    """, (otp_id, email, code_hash, expires_str, now_str))
    
    conn.commit()
    conn.close()

def get_latest_otp(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM otp_records 
        WHERE email = ? AND used = 0 AND expires_at > ?
        ORDER BY created_at DESC LIMIT 1
    """, (email, datetime.utcnow().isoformat()))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def increment_otp_attempts(otp_id: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE otp_records SET attempts = attempts + 1 WHERE id = ?", (otp_id,))
    conn.commit()
    
    cursor.execute("SELECT attempts FROM otp_records WHERE id = ?", (otp_id,))
    row = cursor.fetchone()
    attempts = row[0] if row else 0
    conn.close()
    return attempts

def mark_otp_used(otp_id: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE otp_records SET used = 1 WHERE id = ?", (otp_id,))
    conn.commit()
    conn.close()

def cleanup_expired_otps() -> None:
    """Deletes records where expires_at is older than 24 hours ago"""
    conn = get_connection()
    cursor = conn.cursor()
    
    twenty_four_hours_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    cursor.execute("DELETE FROM otp_records WHERE expires_at < ?", (twenty_four_hours_ago,))
    conn.commit()
    conn.close()

# --- OAuth State Operations ---

def save_oauth_state(state: str, expires_at: datetime) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    
    expires_str = expires_at.isoformat()
    cursor.execute("INSERT OR REPLACE INTO oauth_states (state, expires_at) VALUES (?, ?)", (state, expires_str))
    conn.commit()
    conn.close()

def verify_and_delete_state(state: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    now_str = datetime.utcnow().isoformat()
    cursor.execute("SELECT 1 FROM oauth_states WHERE state = ? AND expires_at > ?", (state, now_str))
    exists = cursor.fetchone() is not None
    
    if exists:
        cursor.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
        conn.commit()
        
    conn.close()
    return exists

# --- User Database Operations ---

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def create_user(user_id: str, email: str, name: str, provider: str, avatar_url: Optional[str] = None, google_id: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    now_str = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT INTO users (id, email, name, avatar_url, provider, google_id, created_at, last_login)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, email, name, avatar_url, provider, google_id, now_str, now_str))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    user_dict = dict(row)
    conn.close()
    
    return user_dict

def update_user_profile(user_id: str, name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    conn.commit()
    rowcount = cursor.rowcount
    conn.close()
    return rowcount > 0

def update_last_login(user_id: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    
    now_str = datetime.utcnow().isoformat()
    cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, user_id))
    conn.commit()
    conn.close()

def merge_google_account(email: str, google_id: str, avatar_url: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    now_str = datetime.utcnow().isoformat()
    cursor.execute("""
        UPDATE users 
        SET google_id = ?, avatar_url = ?, last_login = ?
        WHERE email = ?
    """, (google_id, avatar_url, now_str, email))
    
    conn.commit()
    rowcount = cursor.rowcount
    conn.close()
    return rowcount > 0

def delete_user_data(user_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    rowcount = cursor.rowcount
    conn.close()
    return rowcount > 0
