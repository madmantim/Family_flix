from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import members, movies, swipes, watchlist, movie_night, history, watched

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Family Flix Picker",
    description="Async movie voting for family movie night",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(members.router, prefix="/api/members", tags=["members"])
app.include_router(movies.router, prefix="/api/movies", tags=["movies"])
app.include_router(swipes.router, prefix="/api/swipes", tags=["swipes"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(movie_night.router, prefix="/api/movie-night", tags=["movie-night"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(watched.router, prefix="/api/watched", tags=["watched"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": "Family Flix Picker"}
