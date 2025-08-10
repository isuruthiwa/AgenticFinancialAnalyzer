"""
Database connection and management module.

Provides SQLAlchemy-based database connectivity with connection pooling,
transaction management, and schema initialization for the CSE stock prediction platform.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database connection manager with SQLAlchemy integration.
    
    Supports SQLite for development and PostgreSQL for production.
    Handles schema initialization, connection pooling, and transactions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database manager with configuration.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.db_config = config.get("database", {})
        self.db_uri = self.db_config.get("uri", "sqlite:///data/agenticfa.db")
        self.echo = self.db_config.get("echo", False)
        
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        
        # Ensure data directory exists for SQLite
        if self.db_uri.startswith("sqlite:///"):
            db_path = Path(self.db_uri.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def engine(self) -> Engine:
        """Get or create SQLAlchemy engine."""
        if self._engine is None:
            if self.db_uri.startswith("sqlite:"):
                # SQLite-specific configuration
                self._engine = create_engine(
                    self.db_uri,
                    echo=self.echo,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30
                    }
                )
            else:
                # PostgreSQL configuration
                self._engine = create_engine(
                    self.db_uri,
                    echo=self.echo,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True
                )
            
            logger.info(f"Created database engine: {self.db_uri}")
            
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """Get or create session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
        return self._session_factory
    
    def get_session(self) -> Session:
        """
        Create a new database session.
        
        Returns:
            SQLAlchemy session instance
        """
        return self.session_factory()
    
    def init_schema(self) -> None:
        """
        Initialize database schema from SQL file.
        
        Executes the schema.sql file to create all required tables and indexes.
        """
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        logger.info("Initializing database schema...")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Split on semicolons and execute each statement
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        with self.engine.begin() as conn:
            for statement in statements:
                try:
                    conn.execute(text(statement))
                except Exception as e:
                    logger.error(f"Error executing statement: {statement[:100]}...")
                    logger.error(f"Error: {e}")
                    raise
        
        logger.info("Database schema initialized successfully")
    
    def execute_sql(self, sql: str, params: Optional[Dict] = None) -> Any:
        """
        Execute raw SQL statement.
        
        Args:
            sql: SQL statement to execute
            params: Optional parameters for the SQL statement
            
        Returns:
            Query result
        """
        with self.engine.begin() as conn:
            return conn.execute(text(sql), params or {})
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table information
        """
        if self.db_uri.startswith("sqlite:"):
            # SQLite-specific query
            sql = "PRAGMA table_info(?)"
            with self.engine.begin() as conn:
                result = conn.execute(text(sql), {"table_name_1": table_name})
                columns = result.fetchall()
                
            return {
                "table_name": table_name,
                "columns": [dict(row._mapping) for row in columns],
                "row_count": self._get_row_count(table_name)
            }
        else:
            # PostgreSQL-specific query
            sql = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """
            with self.engine.begin() as conn:
                result = conn.execute(text(sql), {"table_name": table_name})
                columns = result.fetchall()
                
            return {
                "table_name": table_name,
                "columns": [dict(row._mapping) for row in columns],
                "row_count": self._get_row_count(table_name)
            }
    
    def _get_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        try:
            sql = f"SELECT COUNT(*) as count FROM {table_name}"
            with self.engine.begin() as conn:
                result = conn.execute(text(sql))
                return result.fetchone()[0]
        except Exception:
            return 0
    
    def close(self) -> None:
        """Close database connections."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(config: Optional[Dict[str, Any]] = None) -> DatabaseManager:
    """
    Get global database manager instance.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    
    if _db_manager is None:
        if config is None:
            raise ValueError("Configuration required for first initialization")
        _db_manager = DatabaseManager(config)
    
    return _db_manager


def init_database(config: Dict[str, Any]) -> DatabaseManager:
    """
    Initialize database with schema and return manager.
    
    Args:
        config: Database configuration
        
    Returns:
        Initialized DatabaseManager instance
    """
    db_manager = get_db_manager(config)
    
    # Test connection
    if not db_manager.test_connection():
        raise RuntimeError("Failed to connect to database")
    
    # Initialize schema
    db_manager.init_schema()
    
    return db_manager