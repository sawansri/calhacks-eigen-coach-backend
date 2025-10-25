"""Database manager for the Eigen Coach system."""

from pathlib import Path
from typing import Optional

from mysql.connector import Error, pooling


class DatabaseManager:
    """Manages MySQL connection pool."""
    
    _pool: Optional[pooling.MySQLConnectionPool] = None
    
    @staticmethod
    def initialize():
        """Initialize MySQL connection pool."""
        try:
            DatabaseManager._pool = pooling.MySQLConnectionPool(
                pool_name="calhacks_pool",
                pool_size=5,
                host='localhost',
                port=8003,
                user='root',
                password='joe_is_very_cool',
                database='calhacks',
                autocommit=True
            )
            print("[DatabaseManager] MySQL connection pool initialized")
            
            # Run migrations to create tables
            DatabaseManager._run_migrations()
            DatabaseManager._run_seeders()
            
        except Error as e:
            print(f"[DatabaseManager] Error initializing pool: {e}")
            raise
    
    @staticmethod
    def _run_migrations():
        """Run SQL migrations found in the migrations directory."""
        migrations_dir = Path(__file__).resolve().parent.parent / "migrations"

        if not migrations_dir.exists():
            print(f"[DatabaseManager] Migrations directory not found: {migrations_dir}")
            return

        sql_files = sorted(migrations_dir.glob("*.sql"))
        if not sql_files:
            print("[DatabaseManager] No migration files detected")
            return

        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()

            for file_path in sql_files:
                with open(file_path, "r", encoding="utf-8") as handle:
                    sql_script = handle.read()

                for statement in sql_script.split(';'):
                    statement = statement.strip()
                    if statement:
                        cursor.execute(statement)

            cursor.close()
            conn.close()
            print("[DatabaseManager] Migrations completed successfully")

        except Error as e:
            print(f"[DatabaseManager] Migration error: {e}")

    @staticmethod
    def _run_seeders():
        """Run default data seeders after migrations."""
        try:
            from database.seed_data import run_seeders
        except ImportError as exc:
            print(f"[DatabaseManager] Unable to import seeders: {exc}")
            return

        conn = None
        try:
            conn = DatabaseManager.get_connection()
            run_seeders(conn)
        except Error as e:
            print(f"[DatabaseManager] Seeder error: {e}")
        finally:
            if conn is not None:
                conn.close()
    
    @staticmethod
    def get_connection():
        """Get a connection from the pool."""
        if DatabaseManager._pool is None:
            DatabaseManager.initialize()
        return DatabaseManager._pool.get_connection()
    
    @staticmethod
    def close_all():
        """Close all connections in the pool."""
        if DatabaseManager._pool:
            print("[DatabaseManager] Closing connection pool")
            # Connection pool doesn't need explicit closing
            DatabaseManager._pool = None
