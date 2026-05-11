from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
import os
from .config import get_settings
from .database import engine, Base, get_db
from .routers import members, movies, swipes, watchlist, movie_night, watched

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Family Flix Picker",
    description="Async movie voting for family movie night",
    version="1.0.0",
)

# When origins == ["*"], credentials must be False per CORS spec (browsers reject otherwise).
cors_origins = settings.cors_origin_list or ["*"]
allow_credentials = cors_origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (avatars, etc.)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(os.path.join(static_dir, "avatars"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(members.router, prefix="/api/members", tags=["members"])
app.include_router(movies.router, prefix="/api/movies", tags=["movies"])
app.include_router(swipes.router, prefix="/api/swipes", tags=["swipes"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(movie_night.router, prefix="/api/movie-night", tags=["movie-night"])
app.include_router(watched.router, prefix="/api/watched", tags=["watched"])


@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "healthy", "app": "Family Flix Picker"}
