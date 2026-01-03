import { useQuery, useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { PanInfo } from 'framer-motion';
import {
  getMembers,
  getMatches,
  markMovieWatched,
} from '../api/client';
import { BottomNav } from '../components/BottomNav';
import { TMDB_BASE_URL, getInitials, getColor, getAvatarUrl, parseGenres } from '../utils';
import type { MatchedMovie, Movie } from '../types';
import './MovieNight.css';

type Stage = 'select' | 'browse' | 'winner' | 'completion';

export function MovieNight() {
  const [stage, setStage] = useState<Stage>('select');
  const [selectedMembers, setSelectedMembers] = useState<number[]>([]);
  const [matches, setMatches] = useState<MatchedMovie[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [result, setResult] = useState<Movie | null>(null);
  const [selectedWatchers, setSelectedWatchers] = useState<number[]>([]);

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
    },
    onError: (error) => {
      console.error('Failed to mark watched:', error);
    },
  });

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
    if (info.offset.x < -threshold && currentIndex < matches.length - 1) {
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
                    {currentIndex + 1} of {matches.length}
                  </div>
                </div>

                <div className="position-dots">
                  {matches.map((_, i) => (
                    <span
                      key={i}
                      className={`dot ${i === currentIndex ? 'active' : ''}`}
                      onClick={() => setCurrentIndex(i)}
                    />
                  ))}
                </div>

                <div className="browse-card-container">
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
                      {matches[currentIndex] && (
                        <>
                          <div
                            className="browse-poster"
                            style={{
                              backgroundImage: matches[currentIndex].movie.poster_url
                                ? `url(${matches[currentIndex].movie.poster_url})`
                                : undefined,
                            }}
                          />

                          <div className="browse-info">
                            <h2>
                              {matches[currentIndex].movie.title}
                              {matches[currentIndex].movie.year && (
                                <span className="year"> ({matches[currentIndex].movie.year})</span>
                              )}
                            </h2>

                            <div className="voter-stack">
                              <span className="voter-icon">
                                {matches[currentIndex].is_full_match ? '✓' : '👍'}
                              </span>
                              <div className="voter-avatars">
                                {matches[currentIndex].voters.map((voter, idx) => (
                                  <span
                                    key={voter.id}
                                    className="voter-avatar"
                                    style={{
                                      backgroundColor: getColor(idx),
                                      zIndex: matches[currentIndex].voters.length - idx
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
                              {matches[currentIndex].is_full_match ? (
                                <span className="voter-label everyone">Everyone!</span>
                              ) : (
                                <span className="voter-label">
                                  ({matches[currentIndex].yes_votes}/{matches[currentIndex].total_present})
                                </span>
                              )}
                            </div>

                            <div className="meta-row">
                              {matches[currentIndex].movie.runtime && (
                                <span className="meta-item">{matches[currentIndex].movie.runtime} min</span>
                              )}
                              {matches[currentIndex].movie.vote_average && (
                                <span className="meta-item">TMDB {(matches[currentIndex].movie.vote_average / 10).toFixed(1)}</span>
                              )}
                              {matches[currentIndex].movie.rt_critic_score && (
                                <span className="rt-score critic">
                                  🍅 {matches[currentIndex].movie.rt_critic_score}%
                                </span>
                              )}
                            </div>

                            {matches[currentIndex].movie.genres && (
                              <div className="genres">
                                {parseGenres(matches[currentIndex].movie.genres).slice(0, 3).map((g) => (
                                  <span key={g} className="genre">{g}</span>
                                ))}
                              </div>
                            )}

                            {matches[currentIndex].movie.overview && (
                              <p className="synopsis">{matches[currentIndex].movie.overview}</p>
                            )}
                          </div>

                          <div className="browse-actions">
                            <div className="action-buttons-row">
                              {matches[currentIndex].movie.trailer_url && (
                                <motion.button
                                  className="btn-secondary"
                                  onClick={() => openTrailer(matches[currentIndex].movie.trailer_url!)}
                                  whileHover={{ scale: 1.02 }}
                                  whileTap={{ scale: 0.98 }}
                                >
                                  ▶ Trailer
                                </motion.button>
                              )}
                              <motion.button
                                className="btn-secondary"
                                onClick={() => openTmdb(matches[currentIndex].movie.tmdb_id)}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                              >
                                More
                              </motion.button>
                            </div>

                            <motion.button
                              className="watch-this-btn"
                              onClick={() => handleWatchThis(matches[currentIndex].movie)}
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
                </div>

                <p className="swipe-hint">← swipe to browse →</p>
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
