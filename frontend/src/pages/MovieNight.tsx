import { useQuery, useMutation } from '@tanstack/react-query';
import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { PanInfo } from 'framer-motion';
import {
  getMembers,
  getMatches,
  markMovieWatched,
} from '../api/client';
import { BottomNav } from '../components/BottomNav';
import { TMDB_BASE_URL, getInitials, getColor, getAvatarUrl, parseGenres, formatContentRating } from '../utils';
import type { MatchedMovie, Movie } from '../types';
import './MovieNight.css';

type Stage = 'select' | 'browse' | 'winner' | 'completion';

// Quick filter definitions
const QUICK_FILTERS = [
  { id: '< 2hrs', label: '< 2hrs' },
  { id: '🍅 70%+', label: '🍅 70%+' },
  { id: 'no 18+', label: 'no 18+' },
  { id: 'New', label: 'New' },
] as const;

export function MovieNight() {
  const [stage, setStage] = useState<Stage>('select');
  const [selectedMembers, setSelectedMembers] = useState<number[]>([]);
  const [matches, setMatches] = useState<MatchedMovie[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [result, setResult] = useState<Movie | null>(null);
  const [selectedWatchers, setSelectedWatchers] = useState<number[]>([]);

  // Filter state
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());
  const [selectedGenres, setSelectedGenres] = useState<Set<string>>(new Set());

  const { data: members } = useQuery({
    queryKey: ['members'],
    queryFn: getMembers,
  });

  const matchesMutation = useMutation({
    mutationFn: () => getMatches(selectedMembers),
    onSuccess: (data) => {
      setMatches(data.matches);
      if (data.matches.length === 0) {
        // No matches - stay at select with empty state shown
        setStage('browse');
      } else if (data.matches.length === 1) {
        // Only one match - instant winner!
        setResult(data.matches[0].movie);
        setStage('winner');
      } else {
        // Multiple matches - go to browse stage
        setCurrentIndex(0);
        setStage('browse');
      }
    },
    onError: (error) => {
      console.error('Failed to get matches:', error);
    },
  });

  const watchedMutation = useMutation({
    mutationFn: () => markMovieWatched(result!.id, selectedWatchers),
    onSuccess: () => {
      // Reset and go back
      setStage('select');
      setSelectedMembers([]);
      setSelectedWatchers([]);
      setMatches([]);
      setResult(null);
      setCurrentIndex(0);
      setActiveFilters(new Set());
      setSelectedGenres(new Set());
    },
    onError: (error) => {
      console.error('Failed to mark watched:', error);
    },
  });

  // Extract unique genres from unfiltered matches
  const availableGenres = useMemo(() => {
    const genres = new Set<string>();
    matches.forEach((m) => {
      parseGenres(m.movie.genres).forEach((g) => genres.add(g));
    });
    return Array.from(genres).sort();
  }, [matches]);

  // Apply filters to matches
  const filteredMatches = useMemo(() => {
    const currentYear = new Date().getFullYear();
    return matches.filter((m) => {
      const movie = m.movie;

      // Quick filters (AND logic)
      if (activeFilters.has('< 2hrs') && (movie.runtime == null || movie.runtime >= 120)) return false;
      if (activeFilters.has('🍅 70%+') && (movie.rt_critic_score == null || movie.rt_critic_score < 70)) return false;
      if (activeFilters.has('no 18+') && movie.content_rating === 'adult') return false;
      if (activeFilters.has('New') && (movie.year == null || movie.year < currentYear - 1)) return false;

      // Genre filters (OR logic)
      if (selectedGenres.size > 0) {
        const movieGenres = parseGenres(movie.genres);
        if (!movieGenres.some((g) => selectedGenres.has(g))) return false;
      }

      return true;
    });
  }, [matches, activeFilters, selectedGenres]);

  const toggleFilter = (filterId: string) => {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (next.has(filterId)) {
        next.delete(filterId);
      } else {
        next.add(filterId);
      }
      return next;
    });
    setCurrentIndex(0); // Reset to first result when filter changes
  };

  const toggleGenre = (genre: string) => {
    setSelectedGenres((prev) => {
      const next = new Set(prev);
      if (next.has(genre)) {
        next.delete(genre);
      } else {
        next.add(genre);
      }
      return next;
    });
    setCurrentIndex(0); // Reset to first result when filter changes
  };

  const clearFilters = () => {
    setActiveFilters(new Set());
    setSelectedGenres(new Set());
    setCurrentIndex(0);
  };

  const hasActiveFilters = activeFilters.size > 0 || selectedGenres.size > 0;

  const toggleMember = (id: number) => {
    setSelectedMembers((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]
    );
  };

  const toggleWatcher = (id: number) => {
    setSelectedWatchers((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]
    );
  };

  const handleDragEnd = (_: never, info: PanInfo) => {
    const threshold = 100;
    if (info.offset.x < -threshold && currentIndex < filteredMatches.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else if (info.offset.x > threshold && currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const handleWatchThis = (movie: Movie) => {
    setResult(movie);
    setStage('winner');
  };

  const openTrailer = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const openTmdb = (tmdbId: number) => {
    window.open(`${TMDB_BASE_URL}${tmdbId}`, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="movie-night-page">
      <AnimatePresence mode="wait">
        {stage === 'select' && (
          <motion.div
            key="select"
            className="stage"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <h1>Movie Night!</h1>
            <p>Who's watching tonight?</p>

            <div className="member-select">
              {members?.map((member, index) => (
                <motion.button
                  key={member.id}
                  className={`member-chip ${selectedMembers.includes(member.id) ? 'selected' : ''}`}
                  onClick={() => toggleMember(member.id)}
                  whileTap={{ scale: 0.95 }}
                >
                  <span className="avatar" style={{ backgroundColor: getColor(index) }}>
                    {member.avatar_url ? (
                      <img src={getAvatarUrl(member.avatar_url)!} alt={member.name} />
                    ) : (
                      getInitials(member.name)
                    )}
                  </span>
                  <span className="name">{member.name}</span>
                  {selectedMembers.includes(member.id) && <span className="check">✓</span>}
                </motion.button>
              ))}
            </div>

            <motion.button
              className="start-btn"
              disabled={selectedMembers.length < 1}
              onClick={() => matchesMutation.mutate()}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {matchesMutation.isPending ? 'Finding Matches...' : 'Find Matches'}
            </motion.button>
          </motion.div>
        )}

        {stage === 'browse' && (
          <motion.div
            key="browse"
            className="stage browse-stage"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            {matches.length === 0 ? (
              <div className="empty-matches">
                <h1>No Matches Found</h1>
                <p>No movies match for everyone watching tonight.</p>
                <p className="suggestion">Try adding more movies to the watchlist or changing who's watching.</p>
                <motion.button
                  className="start-btn"
                  onClick={() => setStage('select')}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  Go Back
                </motion.button>
              </div>
            ) : (
              <>
                <div className="browse-header">
                  <h1>Pick a Movie</h1>
                  <div className="position-indicator">
                    {filteredMatches.length > 0 ? (
                      hasActiveFilters ? (
                        <><span className="filtered">{currentIndex + 1} of {filteredMatches.length}</span> ({matches.length})</>
                      ) : (
                        <>{currentIndex + 1} of {matches.length}</>
                      )
                    ) : (
                      <>0 of {matches.length}</>
                    )}
                  </div>
                </div>

                <div
                  className="progress-bar-container"
                  onClick={(e) => {
                    if (filteredMatches.length === 0) return;
                    const rect = e.currentTarget.getBoundingClientRect();
                    const clickX = e.clientX - rect.left;
                    const percentage = clickX / rect.width;
                    const newIndex = Math.round(percentage * (filteredMatches.length - 1));
                    setCurrentIndex(Math.max(0, Math.min(newIndex, filteredMatches.length - 1)));
                  }}
                >
                  <div className="progress-bar-track">
                    <div
                      className="progress-bar-fill"
                      style={{ width: filteredMatches.length > 0 ? `${((currentIndex + 1) / filteredMatches.length) * 100}%` : '0%' }}
                    />
                    <div
                      className="progress-bar-thumb"
                      style={{ left: filteredMatches.length > 1 ? `${(currentIndex / (filteredMatches.length - 1)) * 100}%` : '0%' }}
                    />
                  </div>
                </div>

                {/* Filter Chips */}
                <div className="filter-section">
                  <div className="filter-row">
                    {QUICK_FILTERS.map((filter) => (
                      <button
                        key={filter.id}
                        className={`filter-chip ${activeFilters.has(filter.id) ? 'active' : ''}`}
                        onClick={() => toggleFilter(filter.id)}
                      >
                        {filter.label}
                      </button>
                    ))}
                  </div>
                  {availableGenres.length > 0 && (
                    <div className="filter-row genres">
                      {availableGenres.map((genre) => (
                        <button
                          key={genre}
                          className={`filter-chip genre-chip ${selectedGenres.has(genre) ? 'active' : ''}`}
                          onClick={() => toggleGenre(genre)}
                        >
                          {genre}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="browse-card-container">
                  {filteredMatches.length === 0 ? (
                    <div className="empty-filtered">
                      <p>No movies match these filters</p>
                      <button className="clear-filters-btn" onClick={clearFilters}>
                        Clear Filters
                      </button>
                    </div>
                  ) : (
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={currentIndex}
                        className="browse-card"
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -50 }}
                        drag="x"
                        dragConstraints={{ left: 0, right: 0 }}
                        dragElastic={0.2}
                        onDragEnd={handleDragEnd}
                      >
                        {filteredMatches[currentIndex] && (
                          <>
                            {/* Top section: Poster + Info side by side */}
                            <div className="browse-card-top">
                              <div
                                className="browse-poster"
                                style={{
                                  backgroundImage: filteredMatches[currentIndex].movie.poster_url
                                    ? `url(${filteredMatches[currentIndex].movie.poster_url})`
                                    : undefined,
                                }}
                              />

                              <div className="browse-info">
                                <h2>
                                  {filteredMatches[currentIndex].movie.title}
                                  {filteredMatches[currentIndex].movie.year && (
                                    <span className="year"> ({filteredMatches[currentIndex].movie.year})</span>
                                  )}
                                </h2>

                                <div className="meta-stack">
                                  <div className="meta-line">
                                    {filteredMatches[currentIndex].movie.content_rating && (
                                      <span className="rating-badge">{formatContentRating(filteredMatches[currentIndex].movie.content_rating)}</span>
                                    )}
                                    {filteredMatches[currentIndex].movie.runtime && (
                                      <span>{filteredMatches[currentIndex].movie.runtime} min</span>
                                    )}
                                  </div>
                                  <div className="meta-line">
                                    {filteredMatches[currentIndex].movie.rt_critic_score && (
                                      <span className="rt-score">🍅 {filteredMatches[currentIndex].movie.rt_critic_score}%</span>
                                    )}
                                    {filteredMatches[currentIndex].movie.vote_average && (
                                      <span className="tmdb-score">TMDB {(filteredMatches[currentIndex].movie.vote_average / 10).toFixed(1)}</span>
                                    )}
                                  </div>
                                </div>

                                <div className="icon-buttons">
                                  {filteredMatches[currentIndex].movie.trailer_url && (
                                    <button
                                      className="icon-btn trailer"
                                      onClick={() => openTrailer(filteredMatches[currentIndex].movie.trailer_url!)}
                                      title="Watch Trailer"
                                    >
                                      ▶
                                    </button>
                                  )}
                                  <button
                                    className="icon-btn"
                                    onClick={() => openTmdb(filteredMatches[currentIndex].movie.tmdb_id)}
                                    title="More Info"
                                  >
                                    ℹ
                                  </button>
                                </div>
                              </div>
                            </div>

                            {/* Voter row */}
                            <div className="voter-row">
                              <span className="voter-icon">
                                {filteredMatches[currentIndex].is_full_match ? '✓' : '👍'}
                              </span>
                              <div className="voter-avatars">
                                {filteredMatches[currentIndex].voters.map((voter, idx) => (
                                  <span
                                    key={voter.id}
                                    className="voter-avatar"
                                    style={{
                                      backgroundColor: getColor(idx),
                                      zIndex: filteredMatches[currentIndex].voters.length - idx
                                    }}
                                  >
                                    {voter.avatar_url ? (
                                      <img src={getAvatarUrl(voter.avatar_url)!} alt={voter.name} />
                                    ) : (
                                      getInitials(voter.name)
                                    )}
                                  </span>
                                ))}
                              </div>
                              {filteredMatches[currentIndex].is_full_match ? (
                                <span className="voter-label everyone">Everyone!</span>
                              ) : (
                                <span className="voter-label">
                                  {filteredMatches[currentIndex].yes_votes}/{filteredMatches[currentIndex].total_present} voted yes
                                </span>
                              )}
                            </div>

                            {/* Synopsis + genres */}
                            <div className="browse-card-bottom">
                              {filteredMatches[currentIndex].movie.overview && (
                                <p className="synopsis">{filteredMatches[currentIndex].movie.overview}</p>
                              )}
                              {filteredMatches[currentIndex].movie.genres && (
                                <div className="genres">
                                  {parseGenres(filteredMatches[currentIndex].movie.genres).slice(0, 4).map((g) => (
                                    <span key={g} className="genre">{g}</span>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* Watch This CTA */}
                            <div className="browse-actions">
                              <motion.button
                                className="watch-this-btn"
                                onClick={() => handleWatchThis(filteredMatches[currentIndex].movie)}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                              >
                                Watch This
                              </motion.button>
                            </div>
                          </>
                        )}
                      </motion.div>
                    </AnimatePresence>
                  )}
                </div>

                {filteredMatches.length > 1 && <p className="swipe-hint">← swipe to browse →</p>}
              </>
            )}
          </motion.div>
        )}

        {stage === 'winner' && result && (
          <motion.div
            key="winner"
            className="stage winner-stage"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <motion.div
              className="confetti"
              initial={{ scale: 0 }}
              animate={{ scale: [0, 1.2, 1] }}
              transition={{ duration: 0.5 }}
            >
              🎉
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              Tonight's Movie
            </motion.h1>

            <motion.div
              className="winner-card"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5, type: 'spring' }}
            >
              <div
                className="poster"
                style={{
                  backgroundImage: result.poster_url
                    ? `url(${result.poster_url})`
                    : undefined,
                }}
              />
              <h2>{result.title}</h2>
              <p className="year">{result.year}</p>
            </motion.div>

            <div className="winner-actions">
              <motion.button
                className="watched-btn"
                onClick={() => {
                  setSelectedWatchers([...selectedMembers]);
                  setStage('completion');
                }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Mark as Watched
              </motion.button>
              <button
                className="skip-btn"
                onClick={() => {
                  setStage('select');
                  setSelectedMembers([]);
                  setMatches([]);
                  setResult(null);
                  setCurrentIndex(0);
                }}
              >
                Done
              </button>
            </div>
          </motion.div>
        )}

        {stage === 'completion' && result && (
          <motion.div
            key="completion"
            className="stage completion-stage"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <h1>Who watched it?</h1>

            <div className="completion-poster">
              <div
                className="poster"
                style={{
                  backgroundImage: result.poster_url
                    ? `url(${result.poster_url})`
                    : undefined,
                }}
              />
              <h3>{result.title}</h3>
            </div>

            <div className="watcher-checkboxes">
              {members?.map((member) => (
                <label key={member.id} className="watcher-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedWatchers.includes(member.id)}
                    onChange={() => toggleWatcher(member.id)}
                  />
                  <span>{member.name}</span>
                </label>
              ))}
            </div>

            <div className="completion-actions">
              <motion.button
                className="confirm-watched-btn"
                onClick={() => watchedMutation.mutate()}
                disabled={selectedWatchers.length === 0 || watchedMutation.isPending}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {watchedMutation.isPending ? 'Marking...' : 'Confirm Watched'}
              </motion.button>
              <button
                className="skip-btn"
                onClick={() => {
                  setStage('select');
                  setSelectedMembers([]);
                  setSelectedWatchers([]);
                  setMatches([]);
                  setResult(null);
                  setCurrentIndex(0);
                }}
              >
                Skip
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <BottomNav />
    </div>
  );
}
