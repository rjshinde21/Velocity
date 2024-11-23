import os
import sqlite3
import argparse

def init_database(reset=False):
    """Initialize the SQLite database"""
    db_path = 'prompt_history.db'
    
    # If reset flag is true, remove existing database
    if reset and os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            prompt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            prompt_text TEXT NOT NULL,
            ai_type TEXT,
            categories TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Create indices
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON prompts(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON prompts(created_at)')
    
    conn.commit()
    conn.close()
    
    print(f"Database {'reset and ' if reset else ''}initialized successfully at: {db_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Initialize prompt history database')
    parser.add_argument('--reset', action='store_true', help='Reset the database if it exists')
    args = parser.parse_args()
    
    init_database(args.reset)