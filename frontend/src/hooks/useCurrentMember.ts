import { useState, useCallback, useEffect } from 'react';
import { getMembers } from '../api/client';
import type { Member } from '../types';

const STORAGE_KEY = 'family-flix-member-id';

export function useCurrentMember() {
  const [memberId, setMemberId] = useState<number | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? parseInt(stored, 10) : null;
  });

  // If the stored ID no longer matches a real member (e.g. that member was
  // deleted on another device), clear it so the user is routed back to
  // UserSelect. We call getMembers directly so we don't trust a stale cache
  // entry from another component on the page.
  useEffect(() => {
    if (memberId == null) return;
    let cancelled = false;
    getMembers()
      .then((members: Member[]) => {
        if (cancelled) return;
        if (!members.some((m) => m.id === memberId)) {
          localStorage.removeItem(STORAGE_KEY);
          setMemberId(null);
        }
      })
      .catch(() => {
        // Network error — don't kick the user out, they'll retry on next page.
      });
    return () => {
      cancelled = true;
    };
  }, [memberId]);

  const selectMember = useCallback((member: Member) => {
    localStorage.setItem(STORAGE_KEY, String(member.id));
    setMemberId(member.id);
  }, []);

  const clearMember = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setMemberId(null);
  }, []);

  return { memberId, selectMember, clearMember };
}
