import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getWatchHistory, getWatchStats, recordSwipe, getMemberSwipes } from '../api/client';
import { useCurrentMember } from '../hooks/useCurrentMember';
import { BottomNav } from '../components/BottomNav';
import './History.css';

export function History() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { memberId } = useCurrentMember();

  const { data: history, isLoading } = useQuery({
    queryKey: ['history', memberId],
    queryFn: () => getWatchHistory(memberId!),
    enabled: !!memberId,
  });

  const { data: stats } = useQuery({
    queryKey: ['stats', memberId],
    queryFn: () => getWatchStats(memberId!),
    enabled: !!memberId,
  });

  const { data: memberSwipes } = useQuery({
    queryKey: ['memberSwipes', memberId],
    queryFn: () => getMemberSwipes(memberId!),
    enabled: !!memberId,
  });

  const rewatchMutation = useMutation({
    mutationFn: (movieId: number) => recordSwipe(memberId!, movieId, 'yes'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memberSwipes', memberId] });
    },
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
          {history?.map((entry, i) => {
            const hasYesVote = memberSwipes?.some(
              s => s.movie_id === entry.movie.id && s.direction === 'yes'
            );

            return (
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
                <button
                  className={`rewatch-btn ${hasYesVote ? 'active' : ''}`}
                  onClick={() => rewatchMutation.mutate(entry.movie.id)}
                  disabled={rewatchMutation.isPending || hasYesVote}
                  title={hasYesVote ? 'On your watchlist' : 'Want to watch again'}
                >
                  {hasYesVote ? '♥' : '♡'}
                </button>
              </motion.div>
            );
          })}
        </div>
      )}

      <BottomNav />
    </div>
  );
}
