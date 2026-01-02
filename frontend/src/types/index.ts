export type ContentRating = 'all_ages' | 'teen' | 'mature' | 'adult';
export type SwipeDirection = 'yes' | 'no';

export interface Member {
  id: number;
  name: string;
  avatar_url: string | null;
  content_filter: ContentRating;
  created_at: string;
}

export interface Movie {
  id: number;
  tmdb_id: number;
  title: string;
  year: number | null;
  overview: string | null;
  poster_path: string | null;
  backdrop_path: string | null;
  poster_url: string | null;
  backdrop_url: string | null;
  vote_average: number | null;
  content_rating: ContentRating;
  runtime: number | null;
  genres: string | null;
  imdb_id: string | null;
  rt_critic_score: number | null;
  rt_audience_score: number | null;
  rt_url: string | null;
  trailer_url: string | null;
  created_at: string;
}

export interface Swipe {
  id: number;
  member_id: number;
  movie_id: number;
  direction: SwipeDirection;
  swiped_at: string;
}

export interface WatchlistEntry {
  id: number;
  movie: Movie;
  added_by: Member;
  source: string;
  added_at: string;
  is_active: boolean;
}

export interface MemberWatched {
  id: number;
  movie: Movie;
  watched_at: string;
  would_rewatch: boolean;
}

export interface MatchedMovie {
  movie: Movie;
  yes_votes: number;
  total_present: number;
  is_full_match: boolean;
}

export interface MovieNightResponse {
  matches: MatchedMovie[];
  present_members: Member[];
}

export interface SwipeQueue {
  movies: Movie[];
  total_unswiped: number;
}

export interface TMDBSearchResult {
  tmdb_id: number;
  title: string;
  year: number | null;
  overview: string | null;
  poster_url: string | null;
  vote_average: number | null;
}

export interface TMDBSearchResponse {
  results: TMDBSearchResult[];
  page: number;
  total_pages: number;
  total_results: number;
}

export interface WatchStats {
  total_watched: number;
  watched_this_year: number;
  year: number;
}
