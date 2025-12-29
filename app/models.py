from fastapi import FastAPI 
from sqlalchemy import Column, Integer, String , DateTime , Text , ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db import Base
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True) , primary_key= True , default=uuid.uuid4 )
    username = Column(String(50), unique=True , nullable=False)
    email = Column(String(100), unique=True , nullable=False)
    hashed_password = Column(Text, nullable=False)
    role = Column(String(20), default="user")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False  
    )

    votes = relationship("Vote" , back_populates="user")
    likes = relationship("Like" , back_populates="user")    


class Poll(Base):
    __tablename__ = "polls"

    id = Column(UUID(as_uuid=True) , primary_key= True , default=uuid.uuid4 )
    title = Column(Text , nullable=False)
    description = Column(Text , nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False  
    )
    likes_count = Column(Integer, default=0)  
    created_by = Column(String , nullable=False) #change later for FK to users

    options = relationship("Option" , back_populates="poll" , cascade="all, delete-orphan")
    votes = relationship("Vote" , back_populates="poll" , cascade="all, delete-orphan")
    likes = relationship("Like" , back_populates="poll" , cascade="all, delete-orphan")

class Option(Base):
    __tablename__ = "options"
    
    id = Column(UUID(as_uuid=True) , primary_key= True , default=uuid.uuid4 )
    poll_id = Column(UUID(as_uuid=True) , ForeignKey("polls.id" , ondelete="CASCADE") , nullable=False)
    text = Column(Text , nullable=False)
    
    poll = relationship("Poll" , back_populates="options")
    votes = relationship("Vote" , back_populates="option" , cascade="all, delete-orphan")
   
class Vote(Base):
    __tablename__ = "votes"

    id = Column(UUID(as_uuid=True) , primary_key= True , default=uuid.uuid4 )
    poll_id = Column(UUID(as_uuid=True) , ForeignKey("polls.id" , ondelete="CASCADE") , nullable=False)
    option_id = Column(UUID(as_uuid=True) , ForeignKey("options.id" , ondelete="CASCADE") , nullable=False)
    user_id = Column(UUID(as_uuid=True) , ForeignKey("users.id" , ondelete="CASCADE") , nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False  
    )

    poll = relationship("Poll" , back_populates="votes")
    option = relationship("Option" , back_populates="votes")
    user = relationship("User" , back_populates="votes")


class Like(Base):
    __tablename__ = "likes"

    id = Column(UUID(as_uuid=True) , primary_key= True , default=uuid.uuid4 )
    poll_id = Column(UUID(as_uuid=True) , ForeignKey("polls.id" , ondelete="CASCADE") , nullable=False)
    user_id = Column(UUID(as_uuid=True) , ForeignKey("users.id" , ondelete="CASCADE") , nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False  
    )

    poll = relationship("Poll" , back_populates="likes")
    user = relationship("User" , back_populates="likes")