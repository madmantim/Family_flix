import { useState, useCallback } from 'react';
import type { Member } from '../types';

const STORAGE_KEY = 'family-flix-member-id';

export function useCurrentMember() {
  const [memberId, setMemberId] = useState<number | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? parseInt(stored, 10) : null;
  });

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
