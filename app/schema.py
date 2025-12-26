from pydantic import BaseModel , Field , EmailStr 
from typing import List, Optional
from uuid import UUID

#User Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: str
    created_at: str

    class Config:
        orm_mode = True

#Token Schemas
class Token(BaseModel):
    access_token: str
    username: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id : Optional[str] = None
    role : Optional[str] = None

#Option Schemas
class OptionBase(BaseModel):
    text: str

class OptionCreate(OptionBase):
    pass

class Option(OptionBase):
    id: UUID
    poll_id: UUID
    votes : int = 0
    class Config:
        orm_mode = True

#Poll Schemas
class PollBase(BaseModel):
    title: str
    description: Optional[str] = None

class PollCreate(PollBase):
    options: List[OptionCreate]

class Poll(PollBase):
    id: UUID
    created_at: str
    likes: int = Field(..., alias="likes_count")
    created_by: str
    options: List[Option] = []

    class Config:
        orm_mode = True
        allow_population_by_field_name = True 

#Vote Schemas
class VoteCreate(BaseModel):
    poll_id: UUID
    option_id: UUID

#Like Schemas
class LikeUpdate(BaseModel):
    poll_id: UUID