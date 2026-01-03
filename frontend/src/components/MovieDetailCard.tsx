// frontend/src/components/MovieDetailCard.tsx
import { motion } from 'framer-motion';
import type { WatchlistEntry, SwipeDirection } from '../types';
import { TMDB_BASE_URL, parseGenres } from '../utils';
import './MovieDetailCard.css';

interface MovieDetailCardProps {
  entry: WatchlistEntry;
  watched: boolean;
  currentSwipe?: SwipeDirection;
  isPending: boolean;
  onClose: () => void;
  onSwipe: (direction: SwipeDirection) => void;
  onRemove: () => void;
  onWatchedToggle: () => void;
}

export function MovieDetailCard({
  entry,
  watched,
  currentSwipe,
  isPending,
  onClose,
  onSwipe,
  onRemove,
  onWatchedToggle,
}: MovieDetailCardProps) {
  const movie = entry.movie;

  const openTrailer = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (movie.trailer_url) {
      window.open(movie.trailer_url, '_blank', 'noopener,noreferrer');
    }
  };

  const openTmdb = (e: React.MouseEvent) => {
    e.stopPropagation();
    window.open(`${TMDB_BASE_URL}${movie.tmdb_id}`, '_blank', 'noopener,noreferrer');
  };

  return (
    <motion.div
      className="movie-detail-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="movie-detail-card"
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="close-btn" onClick={onClose}>
          ✕
        </button>

        <div
          className="poster"
          style={{
            backgroundImage: movie.poster_url ? `url(${movie.poster_url})` : undefined,
          }}
        >
          {!movie.poster_url && <div className="no-poster">No Poster</div>}
        </div>

        <div className="info">
          <h2>
            {movie.title}
            {movie.year && <span className="year"> ({movie.year})</span>}
          </h2>

          <div className="meta-row">
            {movie.runtime && <span className="meta-item">{movie.runtime} min</span>}
            {movie.vote_average && <span className="meta-item">TMDB {(movie.vote_average / 10).toFixed(1)}</span>}
            {movie.rt_critic_score && (
              movie.rt_url ? (
                <a
                  href={movie.rt_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="rt-score"
                >
                  🍅 {movie.rt_critic_score}%
                </a>
              ) : (
                <span className="rt-score">🍅 {movie.rt_critic_score}%</span>
              )
            )}
          </div>

          {movie.genres && (
            <div className="genres">
              {parseGenres(movie.genres).slice(0, 3).map((g) => (
                <span key={g} className="genre">{g}</span>
              ))}
            </div>
          )}

          <p className="overview">{movie.overview}</p>

          <div className="action-buttons">
            {movie.trailer_url && (
              <button className="btn-secondary" onClick={openTrailer}>
                ▶ Trailer
              </button>
            )}
            <button className="btn-secondary" onClick={openTmdb}>
              More
            </button>
          </div>
        </div>

        <div className="swipe-actions">
          <motion.button
            className={`swipe-btn no ${currentSwipe === 'no' ? 'active' : ''}`}
            onClick={() => onSwipe('no')}
            disabled={isPending}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            ✕
          </motion.button>
          <button
            className={`swipe-btn seen ${watched ? 'active' : ''}`}
            onClick={onWatchedToggle}
            disabled={isPending}
          >
            👁
          </button>
          <motion.button
            className="swipe-btn remove"
            onClick={onRemove}
            disabled={isPending}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            🗑
          </motion.button>
          <motion.button
            className={`swipe-btn yes ${currentSwipe === 'yes' ? 'active' : ''}`}
            onClick={() => onSwipe('yes')}
            disabled={isPending}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            ♥
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
}
