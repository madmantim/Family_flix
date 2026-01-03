import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getMembers, createMember, uploadAvatar } from '../api/client';
import { useCurrentMember } from '../hooks/useCurrentMember';
import { getInitials, getColor } from '../utils';
import type { Member } from '../types';
import './UserSelect.css';

export function UserSelect() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { selectMember } = useCurrentMember();
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState('');
  const [uploadingId, setUploadingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const selectedMemberRef = useRef<number | null>(null);

  const { data: members, isLoading } = useQuery({
    queryKey: ['members'],
    queryFn: getMembers,
  });

  const addMutation = useMutation({
    mutationFn: (name: string) => createMember({ name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] });
      setNewName('');
      setShowAdd(false);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ memberId, file }: { memberId: number; file: File }) =>
      uploadAvatar(memberId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] });
      setUploadingId(null);
    },
    onError: () => {
      alert('Failed to upload avatar. Please try again.');
      setUploadingId(null);
    },
  });

  const handleSelect = (member: Member) => {
    if (didLongPress.current) {
      didLongPress.current = false;
      return; // Don't navigate if we just did a long-press
    }
    selectMember(member);
    navigate('/swipe');
  };

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (newName.trim()) {
      addMutation.mutate(newName.trim());
    }
  };

  const didLongPress = useRef(false);

  const handleTouchStart = (memberId: number) => {
    didLongPress.current = false;
    longPressTimer.current = setTimeout(() => {
      didLongPress.current = true;
      setEditingId(memberId);
    }, 500);
  };

  const handleTouchEnd = () => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  };

  const handleEditClick = (memberId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    selectedMemberRef.current = memberId;
    fileInputRef.current?.click();
    setEditingId(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    const memberId = selectedMemberRef.current;
    if (file && memberId) {
      setUploadingId(memberId);
      uploadMutation.mutate({ memberId, file });
    }
    // Reset input so same file can be selected again
    e.target.value = '';
  };

  if (isLoading) {
    return <div className="user-select loading">Loading...</div>;
  }

  return (
    <div className="user-select">
      <motion.div
        className="hero"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1>Family Flix</h1>
        <p>Who's watching?</p>
      </motion.div>

      <div className="members-grid">
        {members?.map((member, index) => (
          <motion.button
            key={member.id}
            className="member-card"
            onClick={() => handleSelect(member)}
            onTouchStart={() => handleTouchStart(member.id)}
            onTouchEnd={handleTouchEnd}
            onMouseDown={() => handleTouchStart(member.id)}
            onMouseUp={handleTouchEnd}
            onMouseLeave={handleTouchEnd}
            onContextMenu={(e) => e.preventDefault()}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div
              className="avatar"
              style={{ backgroundColor: getColor(index) }}
            >
              {uploadingId === member.id ? (
                <div className="avatar-loading">...</div>
              ) : member.avatar_url ? (
                <img src={`${import.meta.env.VITE_API_URL?.replace('/api', '') || ''}${member.avatar_url}`} alt={member.name} />
              ) : (
                getInitials(member.name)
              )}
              {editingId === member.id && (
                <div className="avatar-edit-overlay" onClick={(e) => handleEditClick(member.id, e)}>
                  <span>Change Photo</span>
                </div>
              )}
            </div>
            <span className="name">{member.name}</span>
          </motion.button>
        ))}

        <motion.button
          className="member-card add-member"
          onClick={() => setShowAdd(true)}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: (members?.length || 0) * 0.1 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <div className="avatar add">+</div>
          <span className="name">Add</span>
        </motion.button>
      </div>

      {showAdd && (
        <motion.div
          className="add-modal"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setShowAdd(false)}
        >
          <motion.form
            className="add-form"
            initial={{ scale: 0.8, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            onClick={(e) => e.stopPropagation()}
            onSubmit={handleAdd}
          >
            <h2>Add Family Member</h2>
            <input
              type="text"
              placeholder="Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
            />
            <div className="buttons">
              <button type="button" onClick={() => setShowAdd(false)}>Cancel</button>
              <button type="submit" disabled={!newName.trim()}>Add</button>
            </div>
          </motion.form>
        </motion.div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />
    </div>
  );
}
