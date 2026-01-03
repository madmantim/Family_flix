import type { FC } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getMembers } from '../api/client';
import { useCurrentMember } from '../hooks/useCurrentMember';
import { getInitials, getColor, getAvatarUrl } from '../utils';
import './BottomNav.css';

// Custom SVG Icons matching the app's aesthetic
const SwipeIcon = ({ active }: { active: boolean }) => (
  <svg viewBox="0 0 32 32" className={`nav-icon ${active ? 'active' : ''}`}>
    {/* Back card */}
    <rect
      x="10"
      y="4"
      width="14"
      height="20"
      rx="2"
      fill={active ? 'rgba(229, 115, 115, 0.3)' : 'none'}
      stroke="currentColor"
      strokeWidth="1.8"
      transform="rotate(12 17 14)"
    />
    {/* Middle card */}
    <rect
      x="9"
      y="5"
      width="14"
      height="20"
      rx="2"
      fill={active ? 'rgba(229, 115, 115, 0.5)' : 'none'}
      stroke="currentColor"
      strokeWidth="1.8"
      transform="rotate(4 16 15)"
    />
    {/* Front card */}
    <rect
      x="8"
      y="6"
      width="14"
      height="20"
      rx="2"
      fill={active ? '#e57373' : 'none'}
      stroke="currentColor"
      strokeWidth="1.8"
    />
  </svg>
);

const MovieNightIcon = ({ active }: { active: boolean }) => (
  <svg viewBox="0 0 32 32" className={`nav-icon ${active ? 'active' : ''}`}>
    {/* Bucket body */}
    <path
      d="M7 14 L9 28 L23 28 L25 14 Z"
      fill={active ? 'rgba(229, 115, 115, 0.3)' : 'none'}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
    {/* Bucket stripes */}
    <line x1="10" y1="17" x2="11" y2="25" stroke="currentColor" strokeWidth="1" opacity="0.5" />
    <line x1="14" y1="16" x2="14.5" y2="26" stroke="currentColor" strokeWidth="1" opacity="0.5" />
    <line x1="18" y1="16" x2="17.5" y2="26" stroke="currentColor" strokeWidth="1" opacity="0.5" />
    <line x1="22" y1="17" x2="21" y2="25" stroke="currentColor" strokeWidth="1" opacity="0.5" />
    {/* Popcorn pieces */}
    <circle cx="11" cy="11" r="2.5" fill={active ? '#e57373' : 'none'} stroke="currentColor" strokeWidth="1.5" />
    <circle cx="16" cy="9" r="2.8" fill={active ? '#e57373' : 'none'} stroke="currentColor" strokeWidth="1.5" />
    <circle cx="21" cy="11" r="2.5" fill={active ? '#e57373' : 'none'} stroke="currentColor" strokeWidth="1.5" />
    <circle cx="13.5" cy="13" r="2" fill={active ? '#e57373' : 'none'} stroke="currentColor" strokeWidth="1.5" />
    <circle cx="18.5" cy="13" r="2" fill={active ? '#e57373' : 'none'} stroke="currentColor" strokeWidth="1.5" />
  </svg>
);

const WatchlistIcon = ({ active }: { active: boolean }) => (
  <svg viewBox="0 0 32 32" className={`nav-icon ${active ? 'active' : ''}`}>
    {/* Bookmark shape */}
    <path
      d="M8 4 L8 28 L16 22 L24 28 L24 4 Z"
      fill={active ? '#e57373' : 'none'}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
  </svg>
);

const HistoryIcon = ({ active }: { active: boolean }) => (
  <svg viewBox="0 0 32 32" className={`nav-icon ${active ? 'active' : ''}`}>
    {/* Clock circle */}
    <circle
      cx="17"
      cy="17"
      r="10"
      fill={active ? 'rgba(229, 115, 115, 0.2)' : 'none'}
      stroke="currentColor"
      strokeWidth="1.8"
    />
    {/* Clock hands */}
    <line x1="17" y1="17" x2="17" y2="11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <line x1="17" y1="17" x2="21" y2="19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    {/* Counter-clockwise arrow */}
    <path
      d="M7 10 L7 5 L12 5"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M7 5 C4 9 4 14 7 19"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
  </svg>
);

const UserSilhouetteIcon = () => (
  <svg viewBox="0 0 32 32" className="nav-icon">
    {/* Head */}
    <circle cx="16" cy="11" r="5" fill="none" stroke="currentColor" strokeWidth="1.8" />
    {/* Body */}
    <path
      d="M8 28 C8 21 11 18 16 18 C21 18 24 21 24 28"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
  </svg>
);

interface NavItem {
  path: string;
  label: string;
  icon: FC<{ active: boolean }>;
}

const navItems: NavItem[] = [
  { path: '/swipe', label: 'Match', icon: SwipeIcon },
  { path: '/movie-night', label: 'Movie Night', icon: MovieNightIcon },
  { path: '/watchlist', label: 'Watchlist', icon: WatchlistIcon },
  { path: '/history', label: 'History', icon: HistoryIcon },
];

export function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const { memberId } = useCurrentMember();

  const { data: members } = useQuery({
    queryKey: ['members'],
    queryFn: getMembers,
  });

  const currentMember = members?.find(m => m.id === memberId);
  const memberIndex = members?.findIndex(m => m.id === memberId) ?? 0;

  return (
    <nav className="bottom-nav">
      {navItems.map(({ path, label, icon: Icon }) => {
        const isActive = location.pathname === path;
        return (
          <button
            key={path}
            className={isActive ? 'active' : ''}
            onClick={() => navigate(path)}
          >
            <Icon active={isActive} />
            <span>{label}</span>
          </button>
        );
      })}
      <button
        className="user-nav-item"
        onClick={() => navigate('/')}
      >
        {currentMember ? (
          <div
            className="user-avatar"
            style={{ backgroundColor: getColor(memberIndex) }}
          >
            {currentMember.avatar_url ? (
              <img
                src={getAvatarUrl(currentMember.avatar_url) || ''}
                alt={currentMember.name}
              />
            ) : (
              getInitials(currentMember.name)
            )}
          </div>
        ) : (
          <UserSilhouetteIcon />
        )}
        <span>User</span>
      </button>
    </nav>
  );
}
