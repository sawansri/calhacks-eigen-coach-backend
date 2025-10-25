"""
Database manager for the Eigen Coach system.
Manages MySQL connection pool and provides database access.
"""

import mysql.connector
from mysql.connector import pooling, Error
from typing import Optional
import os


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
            
        except Error as e:
            print(f"[DatabaseManager] Error initializing pool: {e}")
            raise
    
    @staticmethod
    def _run_migrations():
        """Run SQL migrations to create tables."""
        migration_file = "migrations/001_create_memory_tables.sql"
        
        if not os.path.exists(migration_file):
            print(f"[DatabaseManager] Migration file not found: {migration_file}")
            return
        
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            with open(migration_file, 'r') as f:
                sql_script = f.read()
            
            # Execute each statement separately
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
