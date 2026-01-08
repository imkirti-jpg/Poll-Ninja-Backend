from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import polls, ws , votes , likes , auth
from app.routes.ws import redis_client 
from app.routes.ws import redis_url

app = FastAPI(title="PollNinja Backend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(polls.routers, prefix="/api/polls", tags=["Polls"])
app.include_router(votes.routers, prefix="/api/votes", tags=["Votes"])
app.include_router(likes.router, prefix="/api/likes", tags=["Likes"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(ws.routers)

@app.get("/")
def root():
    return {"message": "QuickPoll API is running 🚀"}
