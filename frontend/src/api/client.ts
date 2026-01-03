import axios from 'axios';
import type {
  Member,
  WatchlistEntry,
  SwipeQueue,
  MovieNightResponse,
  TMDBSearchResponse,
  WatchStats,
  SwipeDirection,
  MemberWatched,
  Swipe,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Members
export const getMembers = () => api.get<Member[]>('/members').then(r => r.data);
export const createMember = (data: { name: string; content_filter?: string }) =>
  api.post<Member>('/members', data).then(r => r.data);
export const updateMember = (memberId: number, data: { name?: string; content_filter?: string }) =>
  api.patch<Member>(`/members/${memberId}`, data).then(r => r.data);
export const uploadAvatar = async (memberId: number, file: File): Promise<Member> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post<Member>(`/members/${memberId}/avatar`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// Movies
export const searchMovies = (query: string, page = 1) =>
  api.get<TMDBSearchResponse>('/movies/search', { params: { query, page } }).then(r => r.data);
export const discoverMovies = (tab: 'popular' | 'highly-rated', page = 1) =>
  api.get<TMDBSearchResponse>('/movies/discover', { params: { tab, page } }).then(r => r.data);

// Swipes
export const getSwipeQueue = (memberId: number, limit = 20) =>
  api.get<SwipeQueue>(`/swipes/queue/${memberId}`, { params: { limit } }).then(r => r.data);
export const recordSwipe = (memberId: number, movieId: number, direction: SwipeDirection, watched = false) =>
  api.post('/swipes', { member_id: memberId, movie_id: movieId, direction, watched }).then(r => r.data);
export const getMemberSwipes = (memberId: number) =>
  api.get<Swipe[]>(`/swipes/member/${memberId}`).then(r => r.data);

// Watchlist
export const getWatchlist = (activeOnly = true) =>
  api.get<WatchlistEntry[]>('/watchlist', { params: { active_only: activeOnly } }).then(r => r.data);
export const addToWatchlist = (tmdbId: number, addedById: number, source = 'manual') =>
  api.post<WatchlistEntry>('/watchlist', { tmdb_id: tmdbId, added_by_id: addedById, source }).then(r => r.data);
export const removeFromWatchlist = (entryId: number) => api.delete(`/watchlist/${entryId}`);

// Movie Night
export const getMatches = (presentMemberIds: number[]) =>
  api.post<MovieNightResponse>('/movie-night/matches', { present_member_ids: presentMemberIds }).then(r => r.data);

// History (now derived from MemberWatched)
export const getWatchHistory = (memberId: number, limit = 50) =>
  api.get<MemberWatched[]>(`/watched/${memberId}`, { params: { limit } }).then(r => r.data);
export const getWatchStats = (memberId?: number) =>
  api.get<WatchStats>('/watched/history/stats', { params: memberId ? { member_id: memberId } : {} }).then(r => r.data);

// Member Watched
export const getMemberWatched = (memberId: number) =>
  api.get<MemberWatched[]>(`/watched/${memberId}`).then(r => r.data);

export const markMovieWatched = (movieId: number, memberIds: number[]) =>
  api.post('/watched/', { movie_id: movieId, member_ids: memberIds }).then(r => r.data);

export const removeWatched = (memberId: number, movieId: number) =>
  api.delete(`/watched/${memberId}/${movieId}`);

export const toggleWatched = (memberId: number, movieId: number) =>
  api.put(`/watched/${memberId}/${movieId}`).then(r => r.data);
