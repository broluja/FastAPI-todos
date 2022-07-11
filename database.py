import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


# DATABASE_NAME = os.getenv("DATABASE_NAME", "todo")
# DATABASE_USER = os.getenv("DATABASE_USER", "root")
# DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "root")
# DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
# DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")

SQLALCHEMY_DATABASE_URL = os.environ.get('DATABASE_URL')
if SQLALCHEMY_DATABASE_URL.startswith('postgres://'):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace('postgres://', 'postgresql://', 1)
# DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
