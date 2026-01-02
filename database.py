"""
SQLAlchemy Database Configuration
Supports SQLite for local development and PostgreSQL for production (Render)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Check for DATABASE_URL (PostgreSQL on Render) first, fallback to SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Production: PostgreSQL on Render
    # Render uses postgres:// but SQLAlchemy needs postgresql+psycopg://
    # We use psycopg (v3) driver which is compatible with Python 3.13
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print("✓ Using PostgreSQL database")
else:
    # Local development: SQLite
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'the_greatest.db')
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )
    print("✓ Using SQLite database (local development)")

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables from ORM models.
    Call this on startup if tables don't exist.
    """
    from models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=engine)


def test_connection():
    """Test database connectivity"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
