import { useQuery, useMutation } from '@tanstack/react-query';
import { useState, useCallback, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, useMotionValue, useTransform, AnimatePresence, type PanInfo } from 'framer-motion';
import { getSwipeQueue, recordSwipe } from '../api/client';
import { useCurrentMember } from '../hooks/useCurrentMember';
import { HelpTooltip } from '../components/HelpTooltip';
import { BottomNav } from '../components/BottomNav';
import { TMDB_BASE_URL, parseGenres } from '../utils';
import type { Movie, SwipeDirection } from '../types';
import './SwipeScreen.css';

const SWIPE_HELP_ITEMS = [
  { icon: '✕', label: 'Pass' },
  { icon: '♥', label: 'Watch / Rewatch' },
  { icon: '👁', label: 'Seen it' },
];

// Fetch a larger batch to reduce API calls
const BATCH_SIZE = 100;
// Refetch more movies when we're down to this many
const REFETCH_THRESHOLD = 5;
// Minimum drag distance to trigger a swipe
const SWIPE_THRESHOLD_PX = 100;

function MovieCard({
  movie,
  onSwipe,
  isTop,
  watched,
  onWatchedToggle,
}: {
  movie: Movie;
  onSwipe: (direction: SwipeDirection) => void;
  isTop: boolean;
  watched: boolean;
  onWatchedToggle: () => void;
}) {
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-25, 25]);
  const opacity = useTransform(x, [-200, -100, 0, 100, 200], [0.5, 1, 1, 1, 0.5]);

  const yesOpacity = useTransform(x, [0, 100], [0, 1]);
  const noOpacity = useTransform(x, [-100, 0], [1, 0]);

  const handleDragEnd = useCallback(
    (_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
      if (info.offset.x > SWIPE_THRESHOLD_PX) {
        onSwipe('yes');
      } else if (info.offset.x < -SWIPE_THRESHOLD_PX) {
        onSwipe('no');
      }
    },
    [onSwipe]
  );

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
      className={`movie-card ${isTop ? 'top' : ''}`}
      style={{ x, rotate, opacity }}
      drag={isTop ? 'x' : false}
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.7}
      onDragEnd={handleDragEnd}
      initial={{ scale: isTop ? 1 : 0.95, y: isTop ? 0 : 10, opacity: isTop ? 1 : 0.8 }}
      animate={{ scale: isTop ? 1 : 0.95, y: isTop ? 0 : 10, opacity: 1 }}
      exit={{ x: isTop ? 300 : 0, opacity: 0, transition: { duration: 0.2 } }}
      layout
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
          className="swipe-btn no"
          onClick={(e) => { e.stopPropagation(); onSwipe('no'); }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          ✕
        </motion.button>
        <button
          className={`swipe-btn seen ${watched ? 'active' : ''}`}
          onClick={(e) => { e.stopPropagation(); onWatchedToggle(); }}
        >
          👁
        </button>
        <motion.button
          className="swipe-btn yes"
          onClick={(e) => { e.stopPropagation(); onSwipe('yes'); }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          ♥
        </motion.button>
      </div>
    </motion.div>
  );
}

export function SwipeScreen() {
  const navigate = useNavigate();
  const { memberId } = useCurrentMember();
  // Track swiped movie IDs locally to filter them out without race conditions
  const [swipedIds, setSwipedIds] = useState<Set<number>>(new Set());
  const [watched, setWatched] = useState(false);

  const { data: queue, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['swipeQueue', memberId],
    queryFn: () => getSwipeQueue(memberId!, BATCH_SIZE),
    enabled: !!memberId,
    // Don't refetch on window focus - we manage refetching ourselves
    refetchOnWindowFocus: false,
  });

  // Filter out movies we've already swiped this session
  const availableMovies = useMemo(() => {
    if (!queue?.movies) return [];
    return queue.movies.filter(movie => !swipedIds.has(movie.id));
  }, [queue, swipedIds]);

  // Calculate the true remaining count
  const trueRemaining = (queue?.total_unswiped || 0) - swipedIds.size;

  // Auto-refetch when we're running low on movies but more exist on server
  useEffect(() => {
    let isMounted = true;

    if (
      availableMovies.length <= REFETCH_THRESHOLD &&
      trueRemaining > availableMovies.length &&
      !isFetching
    ) {
      // Refetch fresh list from server, then clear swiped IDs on success
      refetch().then(() => {
        if (isMounted) {
          setSwipedIds(new Set());
        }
      });
    }

    return () => {
      isMounted = false;
    };
  }, [availableMovies.length, trueRemaining, isFetching, refetch]);

  const swipeMutation = useMutation({
    mutationFn: ({ movieId, direction, watched }: { movieId: number; direction: SwipeDirection; watched: boolean }) =>
      recordSwipe(memberId!, movieId, direction, watched),
    onSuccess: (_, variables) => {
      // Add the swiped movie ID to our local set
      setSwipedIds(prev => new Set(prev).add(variables.movieId));
      setWatched(false); // Reset watched for next card
    },
    onError: (error) => {
      console.error('Swipe failed:', error);
      // Don't advance - let user retry. Card stays in place.
    },
  });

  const handleSwipe = useCallback(
    (direction: SwipeDirection) => {
      const movie = availableMovies[0];
      if (movie && !swipeMutation.isPending) {
        swipeMutation.mutate({ movieId: movie.id, direction, watched });
      }
    },
    [availableMovies, swipeMutation, watched]
  );

  if (isLoading) {
    return <div className="swipe-screen loading">Loading movies...</div>;
  }

  // Get current movie from the filtered available list
  const currentMovie = availableMovies[0];
  const showLoading = isFetching && availableMovies.length === 0 && trueRemaining > 0;

  // Calculate current position for dots (show up to 10 dots)
  const currentPosition = swipedIds.size;
  const totalInBatch = Math.min(availableMovies.length + swipedIds.size, 10);

  return (
    <div className="swipe-screen">
      <header>
        <h1>Movie Match</h1>
        <div className="header-controls">
          <HelpTooltip items={SWIPE_HELP_ITEMS} />
          <span className="count">{currentPosition + 1} of {trueRemaining + currentPosition}</span>
        </div>
      </header>

      {currentMovie && trueRemaining > 0 && (
        <div className="progress-dots">
          {Array.from({ length: totalInBatch }).map((_, i) => (
            <span
              key={i}
              className={`dot ${i === currentPosition ? 'active' : ''} ${i < currentPosition ? 'done' : ''}`}
            />
          ))}
        </div>
      )}

      <div className="card-stack">
        <AnimatePresence mode="popLayout">
          {showLoading ? (
            <motion.div
              key="loading"
              className="empty-state"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <h2>Loading more...</h2>
              <p>Fetching more movies to swipe</p>
            </motion.div>
          ) : trueRemaining === 0 ? (
            <motion.div
              key="empty"
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
          ) : currentMovie ? (
            <MovieCard
              key={`current-${currentMovie.id}`}
              movie={currentMovie}
              onSwipe={handleSwipe}
              isTop={true}
              watched={watched}
              onWatchedToggle={() => setWatched((w) => !w)}
            />
          ) : null}
        </AnimatePresence>
      </div>

      <BottomNav />
    </div>
  );
}
