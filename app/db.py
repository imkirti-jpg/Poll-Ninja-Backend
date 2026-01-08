from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from sqlalchemy.pool import QueuePool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")



# it creates a SQLAlchemy Engine instance
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,          # number of persistent connections
    max_overflow=10,      # extra connections for bursts
    pool_timeout=30,
    pool_recycle=1800,
    
)

# it is a factory for new Session objects
sessionlocal = sessionmaker(autocommit=False , autoflush=False, bind=engine)

# it is a base class for our models
Base = declarative_base()


# Creates one session per request
# Session is yielded into path operation function
# Session is closed after request ends
def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)


import os

REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"


from app.models import User
from app.models import Poll
from app.models import Vote
from app.models import Option
from app.models import Like

Base.metadata.create_all(bind=engine)
