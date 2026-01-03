import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  getWatchlist,
  searchMovies,
  addToWatchlist,
  removeFromWatchlist,
  getMemberWatched,
  recordSwipe,
  toggleWatched,
  removeWatched,
  getMemberSwipes,
  discoverMovies,
} from '../api/client';
import { useCurrentMember } from '../hooks/useCurrentMember';
import { MovieDetailCard } from '../components/MovieDetailCard';
import { HelpTooltip } from '../components/HelpTooltip';
import { BottomNav } from '../components/BottomNav';
import type { TMDBSearchResult, WatchlistEntry, SwipeDirection } from '../types';
import './Watchlist.css';

const WATCHLIST_HELP_ITEMS = [
  { icon: '🔥', label: 'Discover popular movies' },
  { icon: '+', label: 'Search & add movies' },
  { icon: '✕', label: 'Pass' },
  { icon: '♥', label: 'Watch / Rewatch' },
  { icon: '👁', label: 'Seen it' },
  { icon: '🗑', label: 'Remove' },
];

export function Watchlist() {
  const queryClient = useQueryClient();
  const { memberId } = useCurrentMember();
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<TMDBSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<WatchlistEntry | null>(null);
  const [showDiscover, setShowDiscover] = useState(false);
  const [discoverTab, setDiscoverTab] = useState<'popular' | 'highly-rated'>('popular');

  const { data: watchlist, isLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => getWatchlist(true),
  });

  const { data: memberWatchedList } = useQuery({
    queryKey: ['memberWatched', memberId],
    queryFn: () => getMemberWatched(memberId!),
    enabled: !!memberId,
  });

  const { data: memberSwipes } = useQuery({
    queryKey: ['memberSwipes', memberId],
    queryFn: () => getMemberSwipes(memberId!),
    enabled: !!memberId,
  });

  const { data: discoverResults, isLoading: isDiscoverLoading } = useQuery({
    queryKey: ['discover', discoverTab],
    queryFn: () => discoverMovies(discoverTab),
    enabled: showDiscover,
  });

  const addMutation = useMutation({
    mutationFn: (tmdbId: number) => addToWatchlist(tmdbId, memberId!),
    onSuccess: async (entry) => {
      // Auto-swipe "yes" for the user who added the movie
      try {
        await recordSwipe(memberId!, entry.movie.id, 'yes', false);
      } catch (error) {
        console.error('Auto-swipe failed:', error);
        // Operation still succeeds for add, just the auto-swipe failed
      }
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
      queryClient.invalidateQueries({ queryKey: ['swipeQueue'] });
      queryClient.invalidateQueries({ queryKey: ['memberSwipes', memberId] });
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

  const swipeMutation = useMutation({
    mutationFn: ({ movieId, direction }: { movieId: number; direction: SwipeDirection }) =>
      recordSwipe(memberId!, movieId, direction, false),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['swipeQueue'] });
      queryClient.invalidateQueries({ queryKey: ['memberSwipes', memberId] });
    },
  });

  const watchedMutation = useMutation({
    mutationFn: (movieId: number) => toggleWatched(memberId!, movieId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memberWatched', memberId] });
    },
  });

  const unwatchMutation = useMutation({
    mutationFn: (movieId: number) => removeWatched(memberId!, movieId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memberWatched', memberId] });
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

  // Memoized set of movie IDs the member has voted YES on (O(1) lookups)
  const yesMovieIds = useMemo(() => {
    const ids = new Set<number>();
    memberSwipes?.forEach((s) => {
      if (s.direction === 'yes') {
        ids.add(s.movie_id);
      }
    });
    return ids;
  }, [memberSwipes]);

  // Memoized filtered watchlist (only movies the member has voted YES on)
  const likedMovies = useMemo(() => {
    return watchlist?.filter((entry) => yesMovieIds.has(entry.movie.id)) ?? [];
  }, [watchlist, yesMovieIds]);

  return (
    <div className="watchlist-page">
      <header>
        <h1>Watchlist</h1>
        <div className="header-controls">
          <HelpTooltip items={WATCHLIST_HELP_ITEMS} />
          <button
            className="icon-btn discover-btn"
            onClick={() => setShowDiscover(true)}
            aria-label="Discover trending movies"
            title="Discover"
          >
            🔥
          </button>
          <button
            className="icon-btn add-btn"
            onClick={() => setShowSearch(true)}
            aria-label="Add movie"
            title="Add movie"
          >
            +
          </button>
        </div>
      </header>

      {isLoading ? (
        <div className="loading">Loading...</div>
      ) : watchlist?.length === 0 ? (
        <div className="empty">
          <p>No movies in the pool yet</p>
          <button onClick={() => setShowSearch(true)}>Add your first movie</button>
        </div>
      ) : (
        <div className="movie-grid">
          {likedMovies.map((entry) => (
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
                onClick={() => setSelectedEntry(entry)}
              >
                {!entry.movie.poster_url && <span>No Poster</span>}
                <button
                  className="remove-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeMutation.mutate(entry.id);
                  }}
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

      <AnimatePresence>
        {showDiscover && (
          <motion.div
            className="discover-modal"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowDiscover(false)}
          >
            <motion.div
              className="discover-content"
              initial={{ y: 100 }}
              animate={{ y: 0 }}
              exit={{ y: 100 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="discover-header">
                <h2>Discover</h2>
                <button className="close-btn" onClick={() => setShowDiscover(false)}>
                  ✕
                </button>
              </div>

              <div className="discover-tabs">
                <button
                  className={`tab ${discoverTab === 'popular' ? 'active' : ''}`}
                  onClick={() => setDiscoverTab('popular')}
                >
                  Popular
                </button>
                <button
                  className={`tab ${discoverTab === 'highly-rated' ? 'active' : ''}`}
                  onClick={() => setDiscoverTab('highly-rated')}
                >
                  Highly Rated
                </button>
              </div>

              <div className="discover-results">
                {isDiscoverLoading ? (
                  <div className="loading">Loading...</div>
                ) : (
                  <div className="discover-grid">
                    {discoverResults?.results
                      .filter(movie => !watchlist?.some(w => w.movie.tmdb_id === movie.tmdb_id))
                      .map((movie) => (
                        <motion.div
                          key={movie.tmdb_id}
                          className="discover-item"
                          initial={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.8 }}
                          layout
                          onClick={() => addMutation.mutate(movie.tmdb_id)}
                        >
                          <div
                            className="poster"
                            style={{
                              backgroundImage: movie.poster_url
                                ? `url(${movie.poster_url})`
                                : undefined,
                            }}
                          >
                            {!movie.poster_url && <span>No Poster</span>}
                            <div className="add-overlay">+</div>
                          </div>
                          <div className="title">{movie.title}</div>
                          {movie.vote_average && (
                            <div className="rating">★ {movie.vote_average.toFixed(1)}</div>
                          )}
                        </motion.div>
                      ))}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {selectedEntry && (() => {
          const isWatched = memberWatchedList?.some(w => w.movie.id === selectedEntry.movie.id) ?? false;
          return (
            <MovieDetailCard
              entry={selectedEntry}
              watched={isWatched}
              currentSwipe={memberSwipes?.find(s => s.movie_id === selectedEntry.movie.id)?.direction}
              isPending={swipeMutation.isPending || removeMutation.isPending || watchedMutation.isPending || unwatchMutation.isPending}
              onClose={() => setSelectedEntry(null)}
              onSwipe={(direction) => swipeMutation.mutate({ movieId: selectedEntry.movie.id, direction })}
              onRemove={() => {
                removeMutation.mutate(selectedEntry.id);
                setSelectedEntry(null);
              }}
              onWatchedToggle={() => {
                if (isWatched) {
                  unwatchMutation.mutate(selectedEntry.movie.id);
                } else {
                  watchedMutation.mutate(selectedEntry.movie.id);
                }
              }}
            />
          );
        })()}
      </AnimatePresence>

      <BottomNav />
    </div>
  );
}
