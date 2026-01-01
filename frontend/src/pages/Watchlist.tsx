import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  getWatchlist,
  searchMovies,
  addToWatchlist,
  removeFromWatchlist,
  getMemberWatched,
  updateWouldRewatch,
} from '../api/client';
import { useCurrentMember } from '../hooks/useCurrentMember';
import type { TMDBSearchResult, MemberWatched } from '../types';
import './Watchlist.css';

export function Watchlist() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { memberId } = useCurrentMember();
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<TMDBSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showWatched, setShowWatched] = useState(false);

  const { data: watchlist, isLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => getWatchlist(true),
  });

  const { data: watchedMovies } = useQuery({
    queryKey: ['memberWatched', memberId],
    queryFn: () => getMemberWatched(memberId!),
    enabled: !!memberId && showWatched,
  });

  const updateRewatchMutation = useMutation({
    mutationFn: ({ movieId, wouldRewatch }: { movieId: number; wouldRewatch: boolean }) =>
      updateWouldRewatch(memberId!, movieId, wouldRewatch),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memberWatched', memberId] });
    },
  });

  const addMutation = useMutation({
    mutationFn: (tmdbId: number) => addToWatchlist(tmdbId, memberId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
      queryClient.invalidateQueries({ queryKey: ['swipeQueue'] });
      setShowSearch(false);
      setSearchQuery('');
      setSearchResults([]);
    },
  });

  const removeMutation = useMutation({
    mutationFn: (entryId: number) => removeFromWatchlist(entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
    },
  });

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const results = await searchMovies(searchQuery);
      setSearchResults(results.results);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  if (!memberId) {
    navigate('/');
    return null;
  }

  return (
    <div className="watchlist-page">
      <header>
        <h1>{showWatched ? 'Watched' : 'Watchlist'}</h1>
        <div className="header-controls">
          <label className="show-watched-toggle">
            <span>Show Watched</span>
            <input
              type="checkbox"
              checked={showWatched}
              onChange={(e) => setShowWatched(e.target.checked)}
            />
          </label>
          {!showWatched && (
            <button className="add-btn" onClick={() => setShowSearch(true)}>
              + Add
            </button>
          )}
        </div>
      </header>

      {showWatched ? (
        <div className="watched-list">
          {watchedMovies?.length === 0 ? (
            <div className="empty">
              <p>No watched movies yet</p>
            </div>
          ) : (
            watchedMovies?.map((item) => (
              <div key={item.id} className="watched-item">
                <div
                  className="poster"
                  style={{
                    backgroundImage: item.movie.poster_url
                      ? `url(${item.movie.poster_url})`
                      : undefined,
                  }}
                />
                <div className="watched-info">
                  <h3>{item.movie.title}</h3>
                  <p>Watched {new Date(item.watched_at).toLocaleDateString()}</p>
                </div>
                <button
                  className={`rewatch-btn ${item.would_rewatch ? 'active' : ''}`}
                  onClick={() => updateRewatchMutation.mutate({
                    movieId: item.movie.id,
                    wouldRewatch: !item.would_rewatch
                  })}
                >
                  {item.would_rewatch ? '♥' : '♡'}
                </button>
              </div>
            ))
          )}
        </div>
      ) : isLoading ? (
        <div className="loading">Loading...</div>
      ) : watchlist?.length === 0 ? (
        <div className="empty">
          <p>No movies in the pool yet</p>
          <button onClick={() => setShowSearch(true)}>Add your first movie</button>
        </div>
      ) : (
        <div className="movie-grid">
          {watchlist?.map((entry) => (
            <motion.div
              key={entry.id}
              className="movie-item"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              layout
            >
              <div
                className="poster"
                style={{
                  backgroundImage: entry.movie.poster_url
                    ? `url(${entry.movie.poster_url})`
                    : undefined,
                }}
              >
                {!entry.movie.poster_url && <span>No Poster</span>}
                <button
                  className="remove-btn"
                  onClick={() => removeMutation.mutate(entry.id)}
                >
                  ✕
                </button>
              </div>
              <div className="title">{entry.movie.title}</div>
              <div className="added-by">Added by {entry.added_by.name}</div>
            </motion.div>
          ))}
        </div>
      )}

      <AnimatePresence>
        {showSearch && (
          <motion.div
            className="search-modal"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowSearch(false)}
          >
            <motion.div
              className="search-content"
              initial={{ y: 100 }}
              animate={{ y: 0 }}
              exit={{ y: 100 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h2>Add Movie</h2>
              <div className="search-bar">
                <input
                  type="text"
                  placeholder="Search movies..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  autoFocus
                />
                <button onClick={handleSearch} disabled={isSearching}>
                  {isSearching ? '...' : 'Search'}
                </button>
              </div>

              <div className="search-results">
                {searchResults.map((movie) => (
                  <motion.div
                    key={movie.tmdb_id}
                    className="search-result"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    onClick={() => addMutation.mutate(movie.tmdb_id)}
                  >
                    <div
                      className="poster"
                      style={{
                        backgroundImage: movie.poster_url
                          ? `url(${movie.poster_url})`
                          : undefined,
                      }}
                    />
                    <div className="info">
                      <div className="title">{movie.title}</div>
                      <div className="year">{movie.year}</div>
                    </div>
                    <div className="add">+</div>
                  </motion.div>
                ))}
              </div>

              <button className="close-btn" onClick={() => setShowSearch(false)}>
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <nav className="bottom-nav">
        <button onClick={() => navigate('/swipe')}>Swipe</button>
        <button onClick={() => navigate('/movie-night')}>Movie Night</button>
        <button className="active">Watchlist</button>
        <button onClick={() => navigate('/history')}>History</button>
      </nav>
    </div>
  );
}
