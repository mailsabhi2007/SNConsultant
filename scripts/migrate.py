#!/usr/bin/env python3
"""Database migration script for multi-agent features."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_database, get_database_stats, get_db_connection
from datetime import datetime
import shutil


def create_backup():
    """Create database backup."""
    db_path = "data/app.db"
    if not os.path.exists(db_path):
        print("ℹ No existing database found. Skipping backup.")
        return None

    backup_name = f"data/app.db.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_name)
    print(f"✓ Backup created: {backup_name}")
    return backup_name


def verify_schema():
    """Verify database schema is correct."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check is_superadmin column
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'is_superadmin' not in columns:
            raise Exception("is_superadmin column not found in users table!")

        # Check new tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = ['agent_prompts', 'multi_agent_config', 'agent_handoffs']
        for table in required_tables:
            if table not in tables:
                raise Exception(f"{table} table not found!")

    print("✓ Schema verification passed")


def display_stats():
    """Display database statistics."""
    stats = get_database_stats()
    print("\nDatabase Statistics:")
    print(f"  Total users: {stats['total_users']}")
    print(f"  Active users: {stats['active_users']}")
    print(f"  Total conversations: {stats['total_conversations']}")
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Cache entries: {stats['cache_entries']}")


def main():
    """Main migration function."""
    print("="*50)
    print("Database Migration Script")
    print("="*50)
    print()

    try:
        # Step 1: Backup
        print("[1/4] Creating backup...")
        backup_file = create_backup()

        # Step 2: Migrate
        print("\n[2/4] Running migrations...")
        init_database()
        print("✓ Migrations completed")

        # Step 3: Verify
        print("\n[3/4] Verifying schema...")
        verify_schema()

        # Step 4: Display stats
        print("\n[4/4] Checking database...")
        display_stats()

        # Success
        print("\n" + "="*50)
        print("✓ Migration successful!")
        print("="*50)

        if backup_file:
            print(f"\nBackup file: {backup_file}")
        print("\nNext steps:")
        print("1. Make first user superadmin:")
        cmd = 'from database import get_db_connection; '
        cmd += 'c = get_db_connection(); '
        cmd += 'c.cursor().execute("UPDATE users SET is_superadmin = 1 WHERE username = \'admin\'"); '
        cmd += 'c.commit()'
        print(f'   python -c "{cmd}"')
        print("2. Start the application:")
        print("   uvicorn api.main:app --reload")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        if backup_file:
            print(f"\nTo rollback, restore from: {backup_file}")
            print(f"  cp {backup_file} data/app.db")
        sys.exit(1)


if __name__ == "__main__":
    main()
