import axios from 'axios';
import type {
  Member,
  Movie,
  WatchlistEntry,
  WatchHistory,
  SwipeQueue,
  MovieNightResponse,
  RunoffResult,
  TMDBSearchResponse,
  WatchStats,
  SwipeDirection,
  MemberWatched,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Members
export const getMembers = () => api.get<Member[]>('/members').then(r => r.data);
export const getMember = (id: number) => api.get<Member>(`/members/${id}`).then(r => r.data);
export const createMember = (data: { name: string; content_filter?: string }) =>
  api.post<Member>('/members', data).then(r => r.data);
export const updateMember = (id: number, data: Partial<Member>) =>
  api.patch<Member>(`/members/${id}`, data).then(r => r.data);
export const deleteMember = (id: number) => api.delete(`/members/${id}`);

// Movies
export const searchMovies = (query: string, page = 1) =>
  api.get<TMDBSearchResponse>('/movies/search', { params: { query, page } }).then(r => r.data);
export const getTrending = (page = 1) =>
  api.get<TMDBSearchResponse>('/movies/trending', { params: { page } }).then(r => r.data);
export const getMovie = (id: number) => api.get<Movie>(`/movies/${id}`).then(r => r.data);

// Swipes
export const getSwipeQueue = (memberId: number, limit = 20) =>
  api.get<SwipeQueue>(`/swipes/queue/${memberId}`, { params: { limit } }).then(r => r.data);
export const recordSwipe = (memberId: number, movieId: number, direction: SwipeDirection, watched = false) =>
  api.post('/swipes', { member_id: memberId, movie_id: movieId, direction, watched }).then(r => r.data);

// Watchlist
export const getWatchlist = (activeOnly = true) =>
  api.get<WatchlistEntry[]>('/watchlist', { params: { active_only: activeOnly } }).then(r => r.data);
export const addToWatchlist = (tmdbId: number, addedById: number, source = 'manual') =>
  api.post<WatchlistEntry>('/watchlist', { tmdb_id: tmdbId, added_by_id: addedById, source }).then(r => r.data);
export const removeFromWatchlist = (entryId: number) => api.delete(`/watchlist/${entryId}`);

// Movie Night
export const getMatches = (presentMemberIds: number[]) =>
  api.post<MovieNightResponse>('/movie-night/matches', { present_member_ids: presentMemberIds }).then(r => r.data);
export const startRunoff = (presentMemberIds: number[]) =>
  api.post<{ session_id: string }>('/movie-night/start-runoff', { present_member_ids: presentMemberIds }).then(r => r.data);
export const castVote = (sessionId: string, memberId: number, movieId: number) =>
  api.post(`/movie-night/vote/${sessionId}`, { member_id: memberId, movie_id: movieId }).then(r => r.data);
export const getRunoffResult = (sessionId: string) =>
  api.post<RunoffResult>(`/movie-night/result/${sessionId}`).then(r => r.data);

// History
export const getWatchHistory = (year?: number, limit = 50) =>
  api.get<WatchHistory[]>('/history', { params: { year, limit } }).then(r => r.data);
export const getWatchStats = () => api.get<WatchStats>('/history/stats').then(r => r.data);
export const markWatched = (movieId: number, watcherIds: number[]) =>
  api.post<WatchHistory>('/history', { movie_id: movieId, watcher_ids: watcherIds }).then(r => r.data);

// Member Watched
export const getMemberWatched = (memberId: number) =>
  api.get<MemberWatched[]>(`/watched/${memberId}`).then(r => r.data);

export const markMovieWatched = (movieId: number, memberIds: number[], wouldRewatch = false) =>
  api.post('/watched/', { movie_id: movieId, member_ids: memberIds, would_rewatch: wouldRewatch }).then(r => r.data);

export const updateWouldRewatch = (memberId: number, movieId: number, wouldRewatch: boolean) =>
  api.patch(`/watched/${memberId}/${movieId}`, { would_rewatch: wouldRewatch }).then(r => r.data);
