# PollNinja Backend

A FastAPI-based polling system with real-time updates. Users can create polls, vote on options, like polls, and receive live updates via WebSockets powered by Redis pub/sub.

## Features

- User authentication with JWT tokens
- Role-based access control (admin and user roles)
- Poll creation, listing, and deletion
- Voting system with one vote per user per poll
- Like/unlike functionality for polls
- Real-time updates via WebSockets for vote counts and poll changes
- Redis pub/sub for broadcasting updates across instances

## Tech Stack

- **FastAPI** - Web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **Redis** - Pub/sub messaging for WebSocket broadcasts
- **WebSockets** - Real-time bidirectional communication
- **JWT** (python-jose) - Authentication tokens
- **Passlib** (pbkdf2_sha256) - Password hashing
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

## Project Structure

```
.
├── alembic/              # Database migration scripts
│   ├── versions/         # Migration version files
│   └── env.py            # Alembic environment configuration
├── app/
│   ├── routes/           # API route handlers
│   │   ├── auth.py       # Authentication endpoints (register, login)
│   │   ├── polls.py      # Poll CRUD operations
│   │   ├── votes.py      # Vote casting and queries
│   │   ├── likes.py      # Like/unlike operations
│   │   └── ws.py         # WebSocket endpoints and Redis pub/sub
│   ├── utils/
│   │   ├── auth.py       # JWT token and password hashing utilities
│   │   └── dependencies.py  # FastAPI dependencies (get_current_user, check_admin_role)
│   ├── db.py             # Database connection and session management
│   ├── models.py         # SQLAlchemy ORM models (User, Poll, Option, Vote, Like)
│   ├── schema.py         # Pydantic schemas for request/response validation
│   └── main.py           # FastAPI application entry point
├── alembic.ini           # Alembic configuration
└── requirements.txt      # Python dependencies
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required
DATABASE_URL=postgresql://user:password@host:port/database

# Optional (defaults provided)
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256
REDIS_URL=redis://localhost:6379
```

- `DATABASE_URL`: PostgreSQL connection string (required)
- `SECRET_KEY`: JWT signing key (default: "your_super_secret_key_here")
- `ALGORITHM`: JWT algorithm (default: "HS256")
- `REDIS_URL`: Redis connection URL for WebSocket pub/sub (optional; if not provided, WebSocket updates use in-memory connections limited to single instance)

## Authentication

### Registration

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "user123",
  "email": "user@example.com",
  "password": "securepassword"
}
```

Returns the created user object (id, username, email, role, created_at).

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

Returns an access token and username:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "username": "user123",
  "token_type": "bearer"
}
```

### Using JWT Tokens

Include the token in the Authorization header for protected endpoints:

```http
Authorization: Bearer <access_token>
```

Tokens expire after 1 hour. The token payload contains `user_id`, `username`, and `role`.

## API Overview

### Polls

- `GET /api/polls/` - List all polls with vote counts (public)
- `GET /api/polls/{poll_id}` - Get a single poll with vote counts (public)
- `POST /api/polls/` - Create a new poll (requires authentication)
  - Request body: `{ "title": "Question?", "description": "Optional", "options": [{"text": "Option 1"}, {"text": "Option 2"}] }`
  - Broadcasts new poll via WebSocket channel `polls:global`
- `DELETE /api/polls/{poll_id}` - Delete a poll (requires authentication, only poll creator can delete)
  - Broadcasts deletion via WebSocket channel `polls:global`

### Votes

- `POST /api/votes/` - Cast a vote on a poll option (requires authentication)
  - Request body: `{ "poll_id": "uuid", "option_id": "uuid" }`
  - One vote per user per poll (returns 400 if user already voted)
  - Broadcasts vote update via WebSocket channels
- `GET /api/votes/users/{poll_id}` - Check if current user voted in a poll (requires authentication)
- `GET /api/votes/users/all/votes` - Get all votes by current user (requires authentication)

### Likes

- `POST /api/likes/{poll_id}` - Toggle like on a poll (requires authentication)
  - Creates a like if none exists, removes existing like
  - Returns `{ "liked": true/false, "likes": count }`
  - Broadcasts like update via WebSocket channels
- `GET /api/likes/user/{poll_id}` - Check if current user liked a poll (requires authentication)
- `GET /api/likes/users/all/likes` - Get all liked polls by current user (requires authentication)

## WebSocket & Real-Time Architecture

### WebSocket Endpoints

- `ws://host/ws/ws/poll` - Global channel for all poll updates (new polls, deletions, vote/like updates)
- `ws://host/ws/ws/poll/{poll_id}` - Poll-specific channel for vote and like updates

Note: WebSocket paths reflect the router prefix (`/ws`) combined with endpoint paths (`/ws/poll`).

### Message Types

**New Poll:**
```json
{
  "type": "new_poll",
  "id": "uuid",
  "title": "Question?",
  "description": "Optional description",
  "created_at": "2024-01-01T00:00:00",
  "created_by": "username",
  "likes_count": 0,
  "options": [{"id": "uuid", "poll_id": "uuid", "text": "Option", "votes": 0}]
}
```

**Poll Deletion:**
```json
{
  "type": "delete_poll",
  "poll_id": "uuid"
}
```

**Vote Update:**
```json
{
  "type": "vote_update",
  "poll_id": "uuid",
  "options": [{"option_id": "uuid", "text": "Option", "votes": 5}]
}
```

**Like Update:**
```json
{
  "type": "like_update",
  "poll_id": "uuid",
  "likes": 10
}
```

### Architecture

When Redis is enabled:
1. WebSocket connections subscribe to Redis pub/sub channels
2. API operations publish messages to Redis channels (`polls:global` or `poll:{poll_id}`)
3. Redis broadcasts messages to all subscribed WebSocket clients

When Redis is disabled (REDIS_URL not set or connection fails):
1. Poll-specific WebSocket connections are stored in-memory (`active_connections` dict)
2. API operations send messages directly to connected clients via `active_connections` (broadcast functions check for Redis and fall back to in-memory connections)
3. Limited to single instance (not scalable across multiple server instances)
4. Global channel (`/ws/ws/poll`) requires Redis pub/sub and will not receive updates without it (WebSocket handler enters sleep loop when Redis unavailable)

## Database Models

- **User**: id (UUID), username (unique), email (unique), hashed_password, role (default: "user"), created_at
- **Poll**: id (UUID), title, description, created_at, likes_count, created_by (username string)
- **Option**: id (UUID), poll_id (FK), text
- **Vote**: id (UUID), poll_id (FK), option_id (FK), user_id (FK), created_at
- **Like**: id (UUID), poll_id (FK), user_id (FK), created_at

Relationships are configured with cascade deletes: deleting a poll removes its options, votes, and likes.

## Running Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/fastpoll
SECRET_KEY=your_secret_key_here
REDIS_URL=redis://localhost:6379
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive API documentation at `http://localhost:8000/docs`.

## Authorization Rules

- **Public endpoints**: List polls, get single poll
- **Authenticated endpoints**: Create poll, vote, like, delete own polls
- **Role-based**: Admin role exists in the User model and `check_admin_role` dependency is defined, but it is not used in any endpoint. All authenticated endpoints use `get_current_user` which accepts any authenticated user regardless of role.
- **Poll deletion**: Only the poll creator (matching `created_by` with current user's `username`) can delete a poll
- **Voting**: One vote per user per poll (enforced at database query level)
- **Likes**: Multiple toggles allowed (like/unlike), counts are maintained in `poll.likes_count`

## Constraints

- Vote creation checks for existing vote by `poll_id` and `user_id` (prevents multiple votes per poll)
- Username and email must be unique (enforced at database level)
- Polls reference creator by username string (not foreign key to users table)
- WebSocket connections use Redis pub/sub when REDIS_URL is set and connection succeeds; otherwise fall back to in-memory connections (single instance only)
- JWT tokens expire after 1 hour
- Database uses UUID primary keys for all tables
