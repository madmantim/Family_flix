import { useQuery, useMutation } from '@tanstack/react-query';
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, useMotionValue, useTransform, type PanInfo } from 'framer-motion';
import { getSwipeQueue, recordSwipe, getMember } from '../api/client';
import { useCurrentMember } from '../hooks/useCurrentMember';
import type { Movie, SwipeDirection } from '../types';
import './SwipeScreen.css';

function MovieCard({
  movie,
  onSwipe,
  isTop,
}: {
  movie: Movie;
  onSwipe: (direction: SwipeDirection) => void;
  isTop: boolean;
}) {
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-25, 25]);
  const opacity = useTransform(x, [-200, -100, 0, 100, 200], [0.5, 1, 1, 1, 0.5]);

  const yesOpacity = useTransform(x, [0, 100], [0, 1]);
  const noOpacity = useTransform(x, [-100, 0], [1, 0]);

  const handleDragEnd = useCallback(
    (_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
      const threshold = 100;
      if (info.offset.x > threshold) {
        onSwipe('yes');
      } else if (info.offset.x < -threshold) {
        onSwipe('no');
      }
    },
    [onSwipe]
  );

  const parseGenres = (genres: string | null): string[] => {
    if (!genres) return [];
    try {
      return JSON.parse(genres);
    } catch {
      return [];
    }
  };

  return (
    <motion.div
      className={`movie-card ${isTop ? 'top' : ''}`}
      style={{ x, rotate, opacity }}
      drag={isTop ? 'x' : false}
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.7}
      onDragEnd={handleDragEnd}
      initial={{ scale: isTop ? 1 : 0.95, y: isTop ? 0 : 10 }}
      animate={{ scale: isTop ? 1 : 0.95, y: isTop ? 0 : 10 }}
      exit={{ x: 300, opacity: 0 }}
    >
      <div
        className="poster"
        style={{
          backgroundImage: movie.poster_url ? `url(${movie.poster_url})` : undefined,
        }}
      >
        {!movie.poster_url && <div className="no-poster">No Poster</div>}

        <motion.div className="swipe-indicator yes" style={{ opacity: yesOpacity }}>
          YES
        </motion.div>
        <motion.div className="swipe-indicator no" style={{ opacity: noOpacity }}>
          NOPE
        </motion.div>
      </div>

      <div className="info">
        <h2>{movie.title}</h2>
        <div className="meta">
          {movie.year && <span>{movie.year}</span>}
          {movie.runtime && <span>{movie.runtime} min</span>}
          {movie.vote_average && <span>{(movie.vote_average / 10).toFixed(1)}</span>}
        </div>
        {movie.genres && (
          <div className="genres">
            {parseGenres(movie.genres).slice(0, 3).map((g) => (
              <span key={g} className="genre">{g}</span>
            ))}
          </div>
        )}
        <p className="overview">{movie.overview}</p>
      </div>
    </motion.div>
  );
}

export function SwipeScreen() {
  const navigate = useNavigate();
  const { memberId, clearMember } = useCurrentMember();
  const [currentIndex, setCurrentIndex] = useState(0);

  const { data: member } = useQuery({
    queryKey: ['member', memberId],
    queryFn: () => getMember(memberId!),
    enabled: !!memberId,
  });

  const { data: queue, isLoading } = useQuery({
    queryKey: ['swipeQueue', memberId],
    queryFn: () => getSwipeQueue(memberId!, 20),
    enabled: !!memberId,
  });

  const swipeMutation = useMutation({
    mutationFn: ({ movieId, direction }: { movieId: number; direction: SwipeDirection }) =>
      recordSwipe(memberId!, movieId, direction),
    onSuccess: () => {
      setCurrentIndex((i) => i + 1);
    },
  });

  const handleSwipe = useCallback(
    (direction: SwipeDirection) => {
      const movie = queue?.movies[currentIndex];
      if (movie) {
        swipeMutation.mutate({ movieId: movie.id, direction });
      }
    },
    [queue, currentIndex, swipeMutation]
  );

  const handleSwitchUser = () => {
    clearMember();
    navigate('/');
  };

  if (!memberId) {
    navigate('/');
    return null;
  }

  if (isLoading) {
    return <div className="swipe-screen loading">Loading movies...</div>;
  }

  const movies = queue?.movies || [];
  const remaining = movies.length - currentIndex;
  const currentMovie = movies[currentIndex];
  const nextMovie = movies[currentIndex + 1];

  return (
    <div className="swipe-screen">
      <header>
        <button className="back" onClick={handleSwitchUser}>
          Switch User
        </button>
        <span className="member-name">{member?.name}</span>
        <span className="count">{queue?.total_unswiped || 0} left</span>
      </header>

      <div className="card-stack">
        {remaining === 0 ? (
          <motion.div
            className="empty-state"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <h2>All caught up!</h2>
            <p>No more movies to swipe</p>
            <button onClick={() => navigate('/watchlist')}>
              Add Movies
            </button>
          </motion.div>
        ) : (
          <>
            {nextMovie && (
              <MovieCard key={nextMovie.id} movie={nextMovie} onSwipe={() => {}} isTop={false} />
            )}
            {currentMovie && (
              <MovieCard key={currentMovie.id} movie={currentMovie} onSwipe={handleSwipe} isTop={true} />
            )}
          </>
        )}
      </div>

      {currentMovie && (
        <div className="button-row">
          <motion.button
            className="swipe-btn no"
            onClick={() => handleSwipe('no')}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            ✕
          </motion.button>
          <motion.button
            className="swipe-btn yes"
            onClick={() => handleSwipe('yes')}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            ♥
          </motion.button>
        </div>
      )}

      <nav className="bottom-nav">
        <button className="active">Swipe</button>
        <button onClick={() => navigate('/movie-night')}>Movie Night</button>
        <button onClick={() => navigate('/watchlist')}>Watchlist</button>
        <button onClick={() => navigate('/history')}>History</button>
      </nav>
    </div>
  );
}
