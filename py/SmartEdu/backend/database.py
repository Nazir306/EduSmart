# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLITE DATABASE URL
DATABASE_URL = "sqlite:///./school.db"

# Create Engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base
Base = declarative_base()

# Dependency Injection (The 'get_db' function everyone imports)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()