from fastapi import FastAPI
from app.routes import polls, ws , votes , likes , auth
from app.routes.ws import redis_client 
from app.routes.ws import redis_url

app = FastAPI(title="PollNinja Backend")

app.include_router(polls.routers, prefix="/api/polls", tags=["Polls"])
app.include_router(votes.routers, prefix="/api/votes", tags=["Votes"])
app.include_router(likes.router, prefix="/api/likes", tags=["Likes"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(ws.routers)

@app.get("/")
def root():
    return {"message": "QuickPoll API is running 🚀"}
