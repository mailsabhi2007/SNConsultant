"""Database migration script for adding is_admin and making email required."""

import sqlite3
from pathlib import Path
from database import DB_PATH, ensure_db_dir

def migrate_database():
    """Apply database migrations."""
    ensure_db_dir()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print("Starting database migration...")

    try:
        # Check if is_admin column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'is_admin' not in columns:
            print("Adding is_admin column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")

            # Set first user as admin
            cursor.execute("""
                UPDATE users SET is_admin = 1
                WHERE user_id = (SELECT user_id FROM users ORDER BY created_at ASC LIMIT 1)
            """)

            # Set users with admin/superadmin username as admin
            cursor.execute("""
                UPDATE users SET is_admin = 1
                WHERE LOWER(username) IN ('admin', 'superadmin')
            """)

            print("is_admin column added successfully")
        else:
            print("is_admin column already exists")

        # Note: SQLite doesn't support ALTER COLUMN to add NOT NULL constraint
        # So we'll just ensure all existing users have a valid email
        # New users will be required to have email via application logic
        print("Checking email column...")
        cursor.execute("SELECT COUNT(*) FROM users WHERE email IS NULL OR email = ''")
        null_emails = cursor.fetchone()[0]

        if null_emails > 0:
            print(f"Warning: {null_emails} users have no email. Please update them manually.")
            print("Note: New registrations will require email address.")

        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
