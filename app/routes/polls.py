from fastapi import APIRouter , HTTPException, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.schema import PollCreate, Poll, PollBase 
from app import models , schema
from app.utils.dependencies import get_current_user
from datetime import datetime
from app.utils.dependencies import check_admin_role
from uuid import UUID

import asyncio
import json

from app.routes.ws import get_redis


routers = APIRouter()

#Create a poll 
@routers.post("/", response_model=schema.Poll)
async def create_poll(poll: schema.PollCreate ,  
                    db: Session = Depends(get_db),  
                    admin_user: models.User = Depends(check_admin_role),
                    ):
    db_poll = models.Poll(title=poll.title, description=poll.description , likes_count=0, created_by=admin_user.username)
    db.add(db_poll)
    db.commit()
    db.refresh(db_poll)

    # for each option in the poll, create an Option object and associate it with the poll
    for option in poll.options:
        db_option = models.Option(text=option.text, poll_id=db_poll.id)
        db.add(db_option)
    
    db.commit()
    db.refresh(db_poll)

    poll_data = {
        "type": "new_poll",
        "id": str(db_poll.id),
        "title": db_poll.title,
        "description": db_poll.description,
        "created_at": db_poll.created_at.isoformat() if isinstance(db_poll.created_at, datetime) else str(db_poll.created_at),
        "created_by": db_poll.created_by,
        "likes_count": db_poll.likes_count or 0,
        "likes": db_poll.likes_count or 0,
        "options": [
            {"id": str(o.id), "poll_id": str(o.poll_id), "text": o.text, "votes": 0}
            for o in db_poll.options
        ],
    }


    #  Broadcast to global WS channel
    redis_conn = await get_redis()
    if redis_conn:
        await redis_conn.publish("polls:global", json.dumps(poll_data , default=str))
    return poll_data



# Delete a poll
@routers.delete("/{poll_id}")
async def delete_poll(poll_id: UUID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):

    #find poll
    db_poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not db_poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    

    #verify user is creator
    if str(db_poll.created_by) != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to delete this poll")
    
    #Delete related options first
    db.query(models.Option).filter(models.Option.poll_id == poll_id).delete()

    # delete the poll 
    db.delete(db_poll)
    db.commit()



    # Notify via WebSocket
    poll_data = {
        "type": "delete_poll",
        "poll_id": str(poll_id),
    }

    redis_conn = await get_redis()
    if redis_conn:
        await redis_conn.publish("polls:global", json.dumps(poll_data , default=str))

    return {"message": "Poll deleted successfully", "poll_id": poll_id}


# Get All Polls (with votes)
@routers.get("/", response_model=list[schema.Poll])
def list_polls(db: Session = Depends(get_db)):
    polls = db.query(models.Poll).order_by(models.Poll.created_at.desc()).all()
    result = []
    for poll in polls:
        options_data = []
        for option in poll.options:
            votes_count = db.query(models.Vote).filter(models.Vote.option_id == option.id).count()
            options_data.append({
                "id": str(option.id),
                "poll_id": str(option.poll_id),
                "text": option.text,
                "votes": votes_count,
            })

        like_count = db.query(models.Like).filter(models.Like.poll_id == poll.id).count()

        poll_data = {
            "id": str(poll.id),
            "title": poll.title,
            "description": poll.description,
            "created_at": poll.created_at,
            "created_by": poll.created_by,
            "likes_count": like_count,
            "likes": like_count,
            "options": options_data,
        }

        result.append(poll_data)

    return result


# Get polls (with votes)
@routers.get("/{poll_id}", response_model=schema.Poll)
def get_polls(poll_id: str, db: Session = Depends(get_db)):
    poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    options_data = []
    for option in poll.options:
        votes_count = db.query(models.Vote).filter(models.Vote.option_id == option.id).count()
        options_data.append({
            "id": str(option.id),
            "poll_id": str(option.poll_id),
            "text": option.text,
            "votes": votes_count,
        })

    like_count = db.query(models.Like).filter(models.Like.poll_id == poll.id).count()

    poll_data = {
        "id": str(poll.id),
        "title": poll.title,
        "description": poll.description,
        "created_at": poll.created_at,
        "created_by": poll.created_by,
        "likes_count": like_count,
        "likes": like_count,
        "options": options_data,
    }

    return poll_data