import { useQuery, useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  getMembers,
  getMatches,
  startRunoff,
  castVote,
  getRunoffResult,
  markMovieWatched,
} from '../api/client';
import { useCurrentMember } from '../hooks/useCurrentMember';
import type { MatchedMovie, RunoffResult } from '../types';
import './MovieNight.css';

type Stage = 'select' | 'matches' | 'voting' | 'winner' | 'completion';

export function MovieNight() {
  const navigate = useNavigate();
  const { memberId } = useCurrentMember();
  const [stage, setStage] = useState<Stage>('select');
  const [selectedMembers, setSelectedMembers] = useState<number[]>([]);
  const [matches, setMatches] = useState<MatchedMovie[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [votedMovie, setVotedMovie] = useState<number | null>(null);
  const [result, setResult] = useState<RunoffResult | null>(null);
  const [selectedWatchers, setSelectedWatchers] = useState<number[]>([]);

  const { data: members } = useQuery({
    queryKey: ['members'],
    queryFn: getMembers,
  });

  const matchesMutation = useMutation({
    mutationFn: () => getMatches(selectedMembers),
    onSuccess: (data) => {
      setMatches(data.matches);
      if (data.matches.length === 1) {
        // Only one match - instant winner!
        setResult({
          winner: data.matches[0].movie,
          votes: { [data.matches[0].movie.id]: selectedMembers.length },
          was_tie: false,
        });
        setStage('winner');
      } else if (data.matches.length > 1) {
        setStage('matches');
      }
    },
  });

  const startVotingMutation = useMutation({
    mutationFn: () => startRunoff(selectedMembers),
    onSuccess: (data) => {
      setSessionId(data.session_id);
      setStage('voting');
    },
  });

  const voteMutation = useMutation({
    mutationFn: (movieId: number) => castVote(sessionId!, memberId!, movieId),
    onSuccess: (_, movieId) => {
      setVotedMovie(movieId);
    },
  });

  const resultMutation = useMutation({
    mutationFn: () => getRunoffResult(sessionId!),
    onSuccess: (data) => {
      setResult(data);
      setStage('winner');
    },
  });

  const watchedMutation = useMutation({
    mutationFn: () => markMovieWatched(result!.winner.id, selectedWatchers, false),
    onSuccess: () => {
      // Reset and go back
      setStage('select');
      setSelectedMembers([]);
      setSelectedWatchers([]);
      setMatches([]);
      setResult(null);
      setVotedMovie(null);
      setSessionId(null);
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

  const getInitials = (name: string) =>
    name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);

  if (!memberId) {
    navigate('/');
    return null;
  }

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
              {members?.map((member) => (
                <motion.button
                  key={member.id}
                  className={`member-chip ${selectedMembers.includes(member.id) ? 'selected' : ''}`}
                  onClick={() => toggleMember(member.id)}
                  whileTap={{ scale: 0.95 }}
                >
                  <span className="avatar">{getInitials(member.name)}</span>
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

        {stage === 'matches' && (
          <motion.div
            key="matches"
            className="stage"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <h1>Your Matches</h1>
            <p>{matches.length} movies everyone agreed on</p>

            <div className="matches-list">
              {matches.map((match, i) => (
                <motion.div
                  key={match.movie.id}
                  className="match-card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <div
                    className="poster"
                    style={{
                      backgroundImage: match.movie.poster_url
                        ? `url(${match.movie.poster_url})`
                        : undefined,
                    }}
                  />
                  <div className="info">
                    <h3>{match.movie.title}</h3>
                    <span className="year">{match.movie.year}</span>
                    {match.is_full_match ? (
                      <span className="badge full">Full Match!</span>
                    ) : (
                      <span className="badge partial">
                        {match.yes_votes}/{match.total_present} votes
                      </span>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>

            <motion.button
              className="start-btn"
              onClick={() => startVotingMutation.mutate()}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Start Runoff Vote
            </motion.button>
          </motion.div>
        )}

        {stage === 'voting' && (
          <motion.div
            key="voting"
            className="stage"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <h1>Cast Your Vote</h1>
            <p>Pick your favorite for tonight</p>

            <div className="voting-grid">
              {matches.map((match) => (
                <motion.button
                  key={match.movie.id}
                  className={`vote-card ${votedMovie === match.movie.id ? 'voted' : ''}`}
                  onClick={() => voteMutation.mutate(match.movie.id)}
                  whileTap={{ scale: 0.95 }}
                  disabled={!!votedMovie}
                >
                  <div
                    className="poster"
                    style={{
                      backgroundImage: match.movie.poster_url
                        ? `url(${match.movie.poster_url})`
                        : undefined,
                    }}
                  >
                    {votedMovie === match.movie.id && (
                      <div className="voted-overlay">
                        <span>✓</span>
                      </div>
                    )}
                  </div>
                  <span className="title">{match.movie.title}</span>
                </motion.button>
              ))}
            </div>

            {votedMovie && (
              <motion.button
                className="start-btn"
                onClick={() => resultMutation.mutate()}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {resultMutation.isPending ? 'Counting...' : 'See Results'}
              </motion.button>
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
                  backgroundImage: result.winner.poster_url
                    ? `url(${result.winner.poster_url})`
                    : undefined,
                }}
              />
              <h2>{result.winner.title}</h2>
              <p className="year">{result.winner.year}</p>
              {result.was_tie && <p className="tie-note">Won by random tiebreaker!</p>}
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
                  backgroundImage: result.winner.poster_url
                    ? `url(${result.winner.poster_url})`
                    : undefined,
                }}
              />
              <h3>{result.winner.title}</h3>
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
                }}
              >
                Skip
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <nav className="bottom-nav">
        <button onClick={() => navigate('/swipe')}>Swipe</button>
        <button className="active">Movie Night</button>
        <button onClick={() => navigate('/watchlist')}>Watchlist</button>
        <button onClick={() => navigate('/history')}>History</button>
      </nav>
    </div>
  );
}
