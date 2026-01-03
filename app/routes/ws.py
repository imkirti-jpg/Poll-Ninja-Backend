import os
import asyncio
import json
import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.db import  get_db , sessionlocal
from app import models
from app.models import Poll, Option
import redis.asyncio as redis
from redis.asyncio import Redis
from typing import Optional


routers = APIRouter(prefix="/ws", tags=["websocket"])

redis_url = os.getenv("REDIS_URL")
redis_client: Optional[Redis] = None
active_connections = {}

# Redis Setup
async def get_redis():
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(redis_url , encoding="utf-8", decode_responses=True)
            await redis_client.ping() 
            print("Connected to Redis")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}") 
            redis_client = None  
    return redis_client


# Broadcast vote updates
async def broadcast_vote_update(poll_id: str):
    # Send updated vote counts to all WebSocket clients
    db = sessionlocal()
    try:
        options = db.query(models.Option.id , models.Option.text).filter(models.Option.poll_id == poll_id).all()
        payload = []
        for opt in options:
            count = db.query(models.Vote).filter(models.Vote.option_id == opt.id).count()
            payload.append({"option_id": str(opt.id), "text": opt.text, "votes": count})

        message = {"poll_id": str(poll_id), "options": payload}

        redis_conn = await get_redis()
        if redis_conn:
            await redis_conn.publish(f"poll:{poll_id}", json.dumps(message))
            print(f"Published vote update for poll {poll_id} to Redis")

        else:
            if poll_id in active_connections:
                for connection in active_connections[poll_id]:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        print(f"Error sending message to client: {e}")

    finally:
        db.close()

# Broadcast like updates
async def broadcast_like_update(poll_id: str):
    db = sessionlocal()
    try:
        poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
        if not poll:
            return
        
        message = {
            "type": "like_update",
            "poll_id": str(poll_id),
            "likes": poll.likes_count or 0,
        }

        redis_conn = await get_redis()
        if redis_conn:
            await redis_conn.publish(f"poll:{poll_id}", json.dumps(message))
            print(f"Published like update for poll {poll_id} to Redis")

        else:
            if poll_id in active_connections:
                for con in active_connections[poll_id]:
                    try:
                        await con.send_json(message)
                    except Exception as e:
                        print(f"Error sending message to client: {e}")
    finally:
        db.close()


# Global WebSocket endpoint (new poll broadcast)
@routers.websocket("/ws/poll")
async def websocket_all_polls(websocket : WebSocket):
    await websocket.accept()

    redis_conn = await get_redis()
    pubsub = None
    if redis_conn:
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe("polls:global")

    try:
        if pubsub:
            async for message in pubsub.listen():
                if message and message['type'] == 'message':
                    data = json.loads(message['data'])
                    await websocket.send_json(data)
                else:
                    while True:
                        await asyncio.sleep(15)

    except WebSocketDisconnect:
        if pubsub:
            await pubsub.unsubscribe("polls:global")
            await pubsub.close()
        print("WebSocket disconnected from global polls")


# Per-poll WebSocket endpoint
@routers.websocket("/ws/poll/{poll_id}")
async def websocket_poll_update(websocket: WebSocket, poll_id: str):
    await websocket.accept()

    await broadcast_vote_update(poll_id)
    await broadcast_like_update(poll_id)

    if poll_id not in active_connections:
        active_connections[poll_id] = []
    active_connections[poll_id].append(websocket)

    redis_conn = await get_redis()
    pubsub = None
    if redis_conn:
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe(f"poll:{poll_id}")

    try:
        if pubsub:
            async for message in pubsub.listen():
                if message and message['type'] == 'message':
                    data = json.loads(message['data'])
                    await websocket.send_json(json.loads(message["data"]))
                else:
                    while True:
                        await asyncio.sleep(15)

    except WebSocketDisconnect:
        active_connections[poll_id].remove(websocket)
        if not active_connections[poll_id]:
            del active_connections[poll_id]
        if pubsub:
            await pubsub.unsubscribe(f"poll:{poll_id}")
            await pubsub.close()
        print(f"WebSocket disconnected from poll {poll_id}")