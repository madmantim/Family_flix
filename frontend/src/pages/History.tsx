import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getWatchHistory, getWatchStats } from '../api/client';
import { useCurrentMember } from '../hooks/useCurrentMember';
import './History.css';

export function History() {
  const navigate = useNavigate();
  const { memberId } = useCurrentMember();

  const { data: history, isLoading } = useQuery({
    queryKey: ['history'],
    queryFn: () => getWatchHistory(),
  });

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: getWatchStats,
  });

  if (!memberId) {
    navigate('/');
    return null;
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-AU', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="history-page">
      <header>
        <h1>Watch History</h1>
      </header>

      {stats && (
        <motion.div
          className="stats-card"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="stat">
            <span className="value">{stats.watched_this_year}</span>
            <span className="label">Movies in {stats.year}</span>
          </div>
          <div className="stat">
            <span className="value">{stats.total_watched}</span>
            <span className="label">All Time</span>
          </div>
        </motion.div>
      )}

      {isLoading ? (
        <div className="loading">Loading history...</div>
      ) : history?.length === 0 ? (
        <div className="empty">
          <p>No movies watched yet</p>
          <button onClick={() => navigate('/movie-night')}>
            Start a Movie Night
          </button>
        </div>
      ) : (
        <div className="history-list">
          {history?.map((entry, i) => (
            <motion.div
              key={entry.id}
              className="history-item"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <div
                className="poster"
                style={{
                  backgroundImage: entry.movie.poster_url
                    ? `url(${entry.movie.poster_url})`
                    : undefined,
                }}
              />
              <div className="info">
                <h3>{entry.movie.title}</h3>
                <span className="date">{formatDate(entry.watched_at)}</span>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <nav className="bottom-nav">
        <button onClick={() => navigate('/swipe')}>Swipe</button>
        <button onClick={() => navigate('/movie-night')}>Movie Night</button>
        <button onClick={() => navigate('/watchlist')}>Watchlist</button>
        <button className="active">History</button>
      </nav>
    </div>
  );
}
