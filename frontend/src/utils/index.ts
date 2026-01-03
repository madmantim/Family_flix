/**
 * Shared utility constants and functions
 */

// TMDB movie page base URL
export const TMDB_BASE_URL = 'https://www.themoviedb.org/movie/';

// Avatar color palette for user initials
export const AVATAR_COLORS = [
  '#E53935',
  '#8E24AA',
  '#1E88E5',
  '#43A047',
  '#FB8C00',
  '#00ACC1',
  '#5E35B1',
];

/**
 * Get initials from a name (max 2 characters)
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Get a color from the avatar palette by index (cycles through)
 */
export function getColor(index: number): string {
  return AVATAR_COLORS[index % AVATAR_COLORS.length];
}

/**
 * Get the full avatar URL from a relative path
 */
export function getAvatarUrl(avatarPath: string | null): string | null {
  if (!avatarPath) return null;
  // In production, use relative URL (empty string). In dev, VITE_API_URL points to backend.
  const baseUrl = import.meta.env.VITE_API_URL?.replace('/api', '') || '';
  return `${baseUrl}${avatarPath}`;
}

/**
 * Parse genres JSON string into array
 */
export function parseGenres(genres: string | null): string[] {
  if (!genres) return [];
  try {
    return JSON.parse(genres);
  } catch {
    return [];
  }
}
